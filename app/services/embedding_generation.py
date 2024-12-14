import uuid
import os
from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config.weaviate import connect_to_weaviate
from app.config.mongo import get_resume_collection
from langchain_huggingface import HuggingFaceEmbeddings
from datetime import datetime

# Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

async def generate_vectors1(user_id: int, file: str, documents):
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
        result = await collection.insert_one(resume_data)
        print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

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


async def generate_vectors(user_id: int, file: str, documents):
    """
    Generate embeddings for the given resume and store them in MongoDB and Weaviate.

    Args:
        user_id (int): The user ID associated with the resume.
        file (str): The file path or file name.
        documents (list): A list of documents containing the resume content.

    Returns:
        dict: Contains the generated UUIDs for the chunks.
    """
    try:
        print("Hit from generate_vectors")
        print("user_id > ",user_id)
        # Extract filename from the file path
        file_name = os.path.basename(file)

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Store the full resume content and chunks in MongoDB
        collection = get_resume_collection()
        resume_data = {
            "user_id": user_id,
            "file_name": file_name,
            "content": documents[0].page_content,
            "chunks": [chunk.page_content for chunk in chunks],
            "created_at": datetime.utcnow()
        }
        result = await collection.insert_one(resume_data)
        print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Generate embeddings and store each chunk in Weaviate
        class_name = "Resume"
        chunk_uuids = []  # To store the generated UUIDs for all chunks
        for i, chunk in enumerate(chunks):
            chunk_embedding = embedding_model.embed_query(chunk.page_content)
            chunk_id = str(uuid.uuid4())
            chunk_uuids.append(chunk_id)  # Save the chunk UUID
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

        # Return the generated UUIDs
        return {
            "message": f"Resume '{file_name}' uploaded and processed successfully!",
            "uuids": chunk_uuids  # Include the list of UUIDs
        }

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=f"File not found: {e}")
    except Exception as e:
        print(f"Error generating vectors: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating vectors: {e}")

async def get_data_from_weaviate(user_id: int = 123458, file_name: str = None):
    """
    Retrieve data from Weaviate for a given user_id or file_name.

    Args:
        user_id (int, optional): The user ID associated with the resume.
        file_name (str, optional): The file name of the resume.

    Returns:
        dict: Contains the retrieved data from Weaviate.
    """
    try:
        # Connect to Weaviate client
        client = await connect_to_weaviate()

        # Prepare query filters based on provided parameters
        filters = None
        if user_id:
            filters = {
                "path": ["user_id"],
                "operator": "Equal",
                "valueInt": user_id
            }
        elif file_name:
            filters = {
                "path": ["file_name"],
                "operator": "Equal",
                "valueString": file_name
            }

        # Perform the query
        query = client.query.get(
            "Resume",  # Class name
            ["user_id", "file_name", "chunk_id", "content"]  # Properties to retrieve
        )

        if filters:
            query = query.with_where(filters)

        response = query.do()

        # Parse and return the results
        if "data" in response and "Get" in response["data"] and "Resume" in response["data"]["Get"]:
            return {"data": response["data"]["Get"]["Resume"]}
        else:
            return {"message": "No data found in Weaviate matching the criteria."}

    except Exception as e:
        print(f"Error retrieving data from Weaviate: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data from Weaviate: {e}")

response = get_data_from_weaviate(user_id=123)
print("response >>>>>",response)
# #get vector data   
# async def fetch_data_by_employee_id(employee_id: int):
#     """
#     Fetch data from Weaviate using Employee ID.
#     """
#     client = await connect_to_weaviate()
#     print("employee_id form services",employee_id)
#     where_filter = {
#         "path": ["user_id"],  # Ensure this matches the schema field name
#         "operator": "Equal",
#         "valueNumber": employee_id  # Use valueNumber for numeric fields
#     }

#     response = client.query.get(
#         class_name="Resume",  # Replace with your class name
#         properties=["uuid", "content", "user_id", "file_name"]
#     ).with_where(where_filter).do()

#     objects = response.get("data", {}).get("Get", {}).get("Resume", [])
#     if not objects:
#         raise HTTPException(status_code=404, detail=f"No data found for Employee ID {employee_id}")

#     return objects

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
    

# /////////////////////////////////////////////////////////////////////////////////////////////
async def get_chunks_from_weaviate(chunk_ids):
    """
    Retrieve chunk data from Weaviate using their UUIDs.

    Args:
        chunk_ids (list): A list of chunk UUIDs to fetch data for.

    Returns:
        dict: Contains the retrieved chunk data from Weaviate.
    """
    try:
        # Connect to Weaviate client
        client = await connect_to_weaviate()

        # Initialize the result list
        retrieved_chunks = []

        # Loop through each chunk ID and fetch its data
        for chunk_id in chunk_ids:
            response = client.data_object.get(uuid=chunk_id)
            if response:
                retrieved_chunks.append(response)
                print(f"Retrieved data for chunk {chunk_id}: {response}")
            else:
                print(f"No data found for chunk {chunk_id}")

        return {"chunks": retrieved_chunks}

    except Exception as e:
        print(f"Error retrieving chunks from Weaviate: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chunks from Weaviate: {e}")
