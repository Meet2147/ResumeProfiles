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
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.weaviate import connect_to_weaviate
from config.mongo import get_resume_collection
from langchain_huggingface import HuggingFaceEmbeddings

from datetime import datetime

# Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

async def generate_vectors(user_id: int, file: UploadFile, documents):
    try:
        print("Hit from generate_vectors")

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Store the full resume content and chunks in MongoDB
        collection = get_resume_collection()
        resume_data = {
            "user_id": user_id,
            "file_name": file.filename,
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
        for i, chunk in enumerate(chunks):
            chunk_embedding = embedding_model.embed_query(chunk.page_content)
            chunk_id = str(uuid.uuid4())
            properties = {
                "user_id": user_id,
                "file_name": file.filename,
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

        return {"message": f"Resume '{file.filename}' uploaded and processed successfully!"}

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return {"error": f"File not found: {e}"}
    except Exception as e:
        print(f"Error generating vectors: {e}")
        return {"error": f"Error generating vectors: {e}"}
    
async def generate_cert_vectors(user_id: int, file: UploadFile, documents):
    try:
        print("Hit from generate_vectors")

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Store the full resume content and chunks in MongoDB
        collection = get_resume_collection()
        resume_data = {
            "user_id": user_id,
            "file_name": file.filename,
            "content": documents[0].page_content,
            "chunks": [chunk.page_content for chunk in chunks],
            "created_at": datetime.utcnow()
        }
        result = await collection.insert_one(resume_data)
        print(f"Inserted document in MongoDB with ID: {result.inserted_id}")

        # Get Weaviate client
        client = await connect_to_weaviate()

        # Generate embeddings and store each chunk in Weaviate
        class_name = "Certification"
        for i, chunk in enumerate(chunks):
            chunk_embedding = embedding_model.embed_query(chunk.page_content)
            chunk_id = str(uuid.uuid4())
            properties = {
                "user_id": user_id,
                "file_name": file.filename,
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

        return {"message": f"Resume '{file.filename}' uploaded and processed successfully!"}

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return {"error": f"File not found: {e}"}
    except Exception as e:
        print(f"Error generating vectors: {e}")
        return {"error": f"Error generating vectors: {e}"}