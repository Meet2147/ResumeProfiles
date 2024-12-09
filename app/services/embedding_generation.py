# import uuid
# from fastapi import UploadFile
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from config.weaviate import connect_to_weaviate
# from config.mongo import get_resume_collection
# from langchain_huggingface import HuggingFaceEmbeddings

# # Initialize the embedding model
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# async def generate_vectors(file: UploadFile, documents):
#     try:
#         print("Hit from generate_vectors")

#         # Split the document into chunks
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = text_splitter.split_documents(documents)
        
#         # Store the full resume content and chunks in MongoDB
#         collection = get_resume_collection()
#         resume_data = {
#             "file_name": file.filename,
#             "content": documents[0].page_content,
#             "chunks": [chunk.page_content for chunk in chunks],
#         }
#         result = await collection.insert_one(resume_data)
#         print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

#         # Get Weaviate client
#         client = await connect_to_weaviate()

#         # Generate embeddings and store each chunk in Weaviate
#         class_name = "Resume"
#         for i, chunk in enumerate(chunks):
#             chunk_embedding = embedding_model.embed_query(chunk.page_content)
#             chunk_id = str(uuid.uuid4())
#             properties = {
#                 "file_name": file.filename,
#                 "chunk_id": chunk_id,
#                 "content": chunk.page_content,
#             }

#             # Store chunk and embedding in Weaviate
#             response = client.data_object.create(
#                 data_object=properties,
#                 class_name=class_name,
#                 vector=chunk_embedding
#             )
#             print(f"Response from Weaviate for chunk {i}: {response}")
#             # print(f"Response from Weaviate for chunk {i}: {response}, Content: {chunk.page_content}")

#         return {"message": f"Resume '{file.filename}' uploaded and processed successfully!"}

#     except FileNotFoundError as e:
#         print(f"File not found: {e}")
#         return {"error": f"File not found: {e}"}
#     except Exception as e:
#         print(f"Error generating vectors: {e}")
#         return {"error": f"Error generating vectors: {e}"}


import uuid
from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config.weaviate import connect_to_weaviate
from app.config.mongo import get_resume_collection
from langchain_huggingface import HuggingFaceEmbeddings
import os

from datetime import datetime

# Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

async def generate_vectors(user_id: int, file: str, documents):
    try:
        print("Hit from generate_vectors")

        # Extract filename from the file path
        file_name = os.path.basename(file)

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Store the full resume content and chunks in MongoDB
        collection = get_resume_collection()
        print("collection", collection)
        resume_data = {
            "user_id": user_id,
            "file_name": file_name,
            "content": documents[0].page_content,
            "chunks": [chunk.page_content for chunk in chunks],
            "created_at": datetime.utcnow()
        }
        print("resume_data => ", resume_data)
        # result = await collection.insert_one(resume_data)
        # print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Generate embeddings and store each chunk in Weaviate
        class_name = "Resume"
        for i, chunk in enumerate(chunks):
            chunk_embedding = embedding_model.embed_query(chunk.page_content)
            chunk_id = str(uuid.uuid4())
            properties = {
                "user_id": user_id,
                "file_name": file_name,
                "chunk_id": chunk_id,
                "content": chunk.page_content,
            }

            # Store chunk and embedding in Weaviate
            response = client.data_object.create(
                data_object=properties,
                class_name=class_name,
                vector=chunk_embedding
            )
            print(f"Response from Weaviate for chunk {i}: {response}")

        return {"message": f"Resume '{file_name}' uploaded and processed successfully!"}

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return {"error": f"File not found: {e}"}
    except Exception as e:
        print(f"Error generating vectors: {e}")
        return {"error": f"Error generating vectors: {e}"}
    

async def update_skills(user_id: int, new_skills: str):
    try:
        # Get MongoDB collection
        collection = get_resume_collection()

        # Find the resume document in MongoDB
        resume = await collection.find_one({"user_id": user_id})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Debug: Print the resume document to inspect structure
        print("Resume document retrieved from MongoDB:", resume)

        # If 'chunks' are missing or not a list, fallback to processing the entire content
        chunks = resume.get("chunks", [])
        if not isinstance(chunks, list) or not chunks:
            raise HTTPException(status_code=400, detail="'chunks' field is missing or empty in the resume document.")

        # Update skills in MongoDB
        updated_content = f"{resume['content']}\nSkills: {new_skills}"
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"content": updated_content, "skills": new_skills}}
        )

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Update embeddings in Weaviate
        class_name = "Resume"
        where_filter = {
            "path": ["user_id"],
            "operator": "Equal",
            "valueString": str(user_id),
        }

        # Query to fetch existing Weaviate objects for this user_id
        objects = client.query.get(class_name, ["id", "chunk_id"]).with_where(where_filter).do()
        weaviate_chunks = objects["data"]["Get"].get(class_name, [])
        if not weaviate_chunks:
            raise HTTPException(status_code=404, detail=f"No chunks found in Weaviate for user_id {user_id}.")

        # Map Weaviate chunks by chunk_id
        weaviate_chunk_map = {chunk["chunk_id"]: chunk["id"] for chunk in weaviate_chunks}

        # Update Weaviate embeddings for each chunk
        for i, chunk_content in enumerate(chunks):
            updated_chunk_content = f"{chunk_content}\nSkills: {new_skills}"
            updated_embedding = embedding_model.embed_query(updated_chunk_content)

            # Get the UUID for the current chunk
            chunk_id = list(weaviate_chunk_map.keys())[i]  # Assuming chunks in MongoDB and Weaviate are aligned
            object_id = weaviate_chunk_map[chunk_id]

            # Update the chunk in Weaviate
            response = client.data_object.update(
                data_object={
                    "content": updated_chunk_content,
                    "skills": new_skills,
                },
                class_name=class_name,
                uuid=object_id,
                vector=updated_embedding
            )
            print(f"Updated Weaviate object for chunk {i} (chunk_id: {chunk_id}): {response}")

        return {"message": f"Skills updated successfully for user ID {user_id}."}

    except Exception as e:
        print(f"Error updating skills: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating skills: {str(e)}")


async def update_certifications(user_id: int, new_certifications: str):
    try:
        # Get MongoDB collection
        collection = get_resume_collection()

        # Find the resume document in MongoDB
        resume = await collection.find_one({"user_id": user_id})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Update certifications in MongoDB
        updated_content = f"{resume['content']}\nCertifications: {new_certifications}"
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"content": updated_content, "certifications": new_certifications}}
        )

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Update embeddings in Weaviate
        class_name = "Resume"
        for chunk_id, chunk in enumerate(resume["chunks"]):
            updated_chunk_content = f"{chunk}\nCertifications: {new_certifications}"
            updated_embedding = embedding_model.embed_query(updated_chunk_content)

            # Update Weaviate object
            response = client.data_object.update(
                data_object={
                    "content": updated_chunk_content,
                    "certifications": new_certifications,
                },
                class_name=class_name,
                uuid=str(uuid.uuid4()),
                vector=updated_embedding
            )
            print(f"Updated Weaviate object for chunk {chunk_id}: {response}")

        return {"message": f"Certifications updated successfully for user ID {user_id}."}

    except Exception as e:
        print(f"Error updating certifications: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating certifications: {str(e)}")

async def update_projects(user_id: int, new_projects: str):
    try:
        # Get MongoDB collection
        collection = get_resume_collection()

        # Find the resume document in MongoDB
        resume = await collection.find_one({"user_id": user_id})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Update projects in MongoDB
        updated_content = f"{resume['content']}\nProjects: {new_projects}"
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"content": updated_content, "projects": new_projects}}
        )

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Update embeddings in Weaviate
        class_name = "Resume"
        for chunk_id, chunk in enumerate(resume["chunks"]):
            updated_chunk_content = f"{chunk}\nProjects: {new_projects}"
            updated_embedding = embedding_model.embed_query(updated_chunk_content)

            # Update Weaviate object
            response = client.data_object.update(
                data_object={
                    "content": updated_chunk_content,
                    "projects": new_projects,
                },
                class_name=class_name,
                uuid=str(uuid.uuid4()),
                vector=updated_embedding
            )
            print(f"Updated Weaviate object for chunk {chunk_id}: {response}")

        return {"message": f"Projects updated successfully for user ID {user_id}."}

    except Exception as e:
        print(f"Error updating projects: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating projects: {str(e)}")
    
# async def generate_cert_vectors(user_id: int, file: UploadFile, documents):
#     try:
#         print("Hit from generate_vectors")

#         # Split the document into chunks
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = text_splitter.split_documents(documents)
        
#         # Store the full resume content and chunks in MongoDB
#         collection = get_resume_collection()
#         resume_data = {
#             "user_id": user_id,
#             "file_name": file.filename,
#             "content": documents[0].page_content,
#             "chunks": [chunk.page_content for chunk in chunks],
#             "created_at": datetime.utcnow()
#         }
#         result = await collection.insert_one(resume_data)
#         print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

#         # Get Weaviate client
#         client = await connect_to_weaviate()

#         # Generate embeddings and store each chunk in Weaviate
#         class_name = "Certification"
#         for i, chunk in enumerate(chunks):
#             chunk_embedding = embedding_model.embed_query(chunk.page_content)
#             chunk_id = str(uuid.uuid4())
#             properties = {
#                 "user_id": user_id,
#                 "file_name": file.filename,
#                 "chunk_id": chunk_id,
#                 "content": chunk.page_content,
#             }

#             # Store chunk and embedding in Weaviate
#             response = client.data_object.create(
#                 data_object=properties,
#                 class_name=class_name,
#                 vector=chunk_embedding
#             )
#             print(f"Response from Weaviate for chunk {i}: {response}")

#         return {"message": f"Resume '{file.filename}' uploaded and processed successfully!"}

#     except FileNotFoundError as e:
#         print(f"File not found: {e}")
#         return {"error": f"File not found: {e}"}
#     except Exception as e:
#         print(f"Error generating vectors: {e}")
#         return {"error": f"Error generating vectors: {e}"}