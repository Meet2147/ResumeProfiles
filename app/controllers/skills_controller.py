# # import os
# # import uuid
# # from fastapi import FastAPI, File, UploadFile, HTTPException
# # from pydantic import BaseModel
# # from pymongo import MongoClient
# # from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
# # from langchain.text_splitter import RecursiveCharacterTextSplitter
# # from langchain_huggingface import HuggingFaceEmbeddings
# # import weaviate
# # import openai
# # from typing import Dict, List
# # from fastapi.responses import FileResponse
# # from motor.motor_asyncio import AsyncIOMotorClient


# # ### Upload Certifications for Employee Profiles ###

# # CERTIFICATION_DIRECTORY = "uploaded_certifications"
# # ACHIEVEMENT_DIRECTORY = "uploaded_achievements"
# # collection = "users"

# # async def upload_certification(employee_name: str, file: UploadFile = File(...)):
# #     # Save the certification in the employee's directory
# #     certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)
# #     os.makedirs(certification_dir, exist_ok=True)

# #     # Save the certification file
# #     file_location = os.path.join(certification_dir, file.filename)
# #     with open(file_location, "wb") as f:
# #         f.write(await file.read())

# #     # Optionally, you can also store details in MongoDB for certifications
# #     collection.update_one(
# #         {"file_name": f"{employee_name}.pdf"}, 
# #         {"$push": {"certifications": file.filename}},
# #         upsert=True
# #     )

# #     return {"message": f"Certification '{file.filename}' uploaded for {employee_name}"}


# # ### Upload Achievements for Employee Profiles ###

# # async def upload_achievement(employee_name: str, file: UploadFile = File(...)):
# #     # Save the achievement in the employee's directory
# #     achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)
# #     os.makedirs(achievement_dir, exist_ok=True)

# #     # Save the achievement file
# #     file_location = os.path.join(achievement_dir, file.filename)
# #     with open(file_location, "wb") as f:
# #         f.write(await file.read())

# #     # Optionally, you can also store details in MongoDB for achievements
# #     collection.update_one(
# #         {"file_name": f"{employee_name}.pdf"}, 
# #         {"$push": {"achievements": file.filename}},
# #         upsert=True
# #     )

# #     return {"message": f"Achievement '{file.filename}' uploaded for {employee_name}"}


# # async def get_certifications(employee_name: str):
# #     certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)

# #     if not os.path.exists(certification_dir):
# #         raise HTTPException(status_code=404, detail="No certifications found for this employee.")

# #     # List all certification files
# #     certification_files = [f for f in os.listdir(certification_dir) if os.path.isfile(os.path.join(certification_dir, f))]

# #     return {"certifications": certification_files}


# # async def get_achievements(employee_name: str):
# #     achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)

# #     if not os.path.exists(achievement_dir):
# #         raise HTTPException(status_code=404, detail="No achievements found for this employee.")

# #     # List all achievement files
# #     achievement_files = [f for f in os.listdir(achievement_dir) if os.path.isfile(os.path.join(achievement_dir, f))]

# #     return {"achievements": achievement_files}

# import os
# import uuid
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from pydantic import BaseModel
# from pymongo import MongoClient
# from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# import weaviate
# import openai
# from typing import Dict, List
# from fastapi.responses import FileResponse
# from motor.motor_asyncio import AsyncIOMotorClient
# from services import embedding_storage, rag_pipeline,model_inference,embedding_generation
# rag_pipeline.process_query
# embedding_storage.search_vectors
# embedding_storage.generate_vectors
# model_inference.generate_detailed_response

# ### MongoDB Connection ###
# MONGO_DB_URL = "mongodb://localhost:27017"  # Update with your MongoDB connection string
# mongo_client = AsyncIOMotorClient(MONGO_DB_URL)
# db = mongo_client["employee_profiles"]  # Your database name
# collection = db["users"]  # Your collection name

# ### Upload Certifications for Employee Profiles ###
# CERTIFICATION_DIRECTORY = "uploaded_certifications"
# ACHIEVEMENT_DIRECTORY = "uploaded_achievements"

# async def upload_certification(employee_name: str, file: UploadFile = File(...)):
#     # Save the certification in the employee's directory
#     certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)
#     os.makedirs(certification_dir, exist_ok=True)

#     # Save the certification file
#     file_location = os.path.join(certification_dir, file.filename)
#     with open(file_location, "wb") as f:
#         f.write(await file.read())

#     # Determine file type and load accordingly
#     if file.filename.endswith(".pdf"):
#         loader = PyMuPDFLoader(file_location)
#     elif file.filename.endswith(".docx"):
#         loader = UnstructuredWordDocumentLoader(file_location)
#     else:
#         return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

#     # Load the documents from the file
#     documents = loader.load()

#     # Store details in MongoDB for certifications
   
#     try:
#         print("Vectors sent for generation")
#         await embedding_generation.generate_vectors(file,documents)
#         print("Vectors sent for storage")
#         embedding_storage.generate_vectors(file)  # Pass documents to the vector generation

#     except Exception as e:
#         return {"error": f"Error generating vectors: {str(e)}"}
    
#     await collection.update_one(
#         {"file_name": f"{employee_name}.pdf"}, 
#         {"$push": {"certifications": file.filename}},
#         upsert=True
#     )

#     return {"message": f"Certification '{file.filename}' uploaded for {employee_name}"}


# ### Upload Achievements for Employee Profiles ###

# async def upload_achievement(employee_name: str, file: UploadFile = File(...)):
#     # Save the achievement in the employee's directory
#     achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)
#     os.makedirs(achievement_dir, exist_ok=True)

#     # Save the achievement file
#     file_location = os.path.join(achievement_dir, file.filename)
#     with open(file_location, "wb") as f:
#         f.write(await file.read())

#     # Determine file type and load accordingly
#     if file.filename.endswith(".pdf"):
#         loader = PyMuPDFLoader(file_location)
#     elif file.filename.endswith(".docx"):
#         loader = UnstructuredWordDocumentLoader(file_location)
#     else:
#         return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

#     # Load the documents from the file
#     documents = loader.load()

#     # Store details in MongoDB for certifications
   
#     try:
#         print("Vectors sent for generation")
#         await embedding_generation.generate_vectors(file,documents)
#         print("Vectors sent for storage")
#         embedding_storage.generate_vectors(file)  # Pass documents to the vector generation

#     except Exception as e:
#         return {"error": f"Error generating vectors: {str(e)}"}
    
#     await collection.update_one(
#         {"file_name": f"{employee_name}.pdf"}, 
#         {"$push": {"achievements": file.filename}},
#         upsert=True
#     )

#     return {"message": f"Achievement '{file.filename}' uploaded for {employee_name}"}


# async def get_certifications(employee_name: str):
#     certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)

#     if not os.path.exists(certification_dir):
#         raise HTTPException(status_code=404, detail="No certifications found for this employee.")

#     # List all certification files
#     certification_files = [f for f in os.listdir(certification_dir) if os.path.isfile(os.path.join(certification_dir, f))]

#     return {"certifications": certification_files}


# async def get_achievements(employee_name: str):
#     achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)

#     if not os.path.exists(achievement_dir):
#         raise HTTPException(status_code=404, detail="No achievements found for this employee.")

#     # List all achievement files
#     achievement_files = [f for f in os.listdir(achievement_dir) if os.path.isfile(os.path.join(achievement_dir, f))]

#     return {"achievements": achievement_files}

import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from pymongo import MongoClient
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from motor.motor_asyncio import AsyncIOMotorClient
from services import embedding_storage, embedding_generation

# MongoDB Connection
MONGO_DB_URL = "mongodb://localhost:27017"  # Update with your MongoDB connection string
mongo_client = AsyncIOMotorClient(MONGO_DB_URL)
db = mongo_client["employee_profiles"]  # Your database name
collection = db["users"]  # Your collection name

# Directories
CERTIFICATION_DIRECTORY = "uploaded_certifications"
ACHIEVEMENT_DIRECTORY = "uploaded_achievements"

# Upload Certification and Add to Profile Vectors
async def upload_certification(employee_name: str, file: UploadFile = File(...)):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)
    os.makedirs(certification_dir, exist_ok=True)

    file_location = os.path.join(certification_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Determine file type and load accordingly
    if file.filename.endswith(".pdf"):
        loader = PyMuPDFLoader(file_location)
    elif file.filename.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_location)
    else:
        return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

    # Load the documents
    documents = loader.load()

    # Generate vectors for the documents
    try:
        print("Generating vectors for certification...")
        vectors = await embedding_generation.generate_vectors(file, documents)
        
        # Append the new vectors to the employee's existing profile
        print("Storing vectors in the employee's profile...")
        await embedding_storage.add_vectors_to_employee_profile(employee_name, vectors)

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    # Update MongoDB
    await collection.update_one(
        {"file_name": f"{employee_name}.pdf"}, 
        {"$push": {"certifications": file.filename}},
        upsert=True
    )

    return {"message": f"Certification '{file.filename}' uploaded for {employee_name}"}


# Upload Achievement and Add to Profile Vectors
async def upload_achievement(employee_name: str, file: UploadFile = File(...)):
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)
    os.makedirs(achievement_dir, exist_ok=True)

    file_location = os.path.join(achievement_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Determine file type and load accordingly
    if file.filename.endswith(".pdf"):
        loader = PyMuPDFLoader(file_location)
    elif file.filename.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_location)
    else:
        return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

    # Load the documents
    documents = loader.load()

    # Generate vectors for the documents
    try:
        print("Generating vectors for achievement...")
        vectors = await embedding_generation.generate_vectors(file, documents)
        
        # Append the new vectors to the employee's existing profile
        print("Storing vectors in the employee's profile...")
        await embedding_storage.add_vectors_to_employee_profile(employee_name, vectors)

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    # Update MongoDB
    await collection.update_one(
        {"file_name": f"{employee_name}.pdf"}, 
        {"$push": {"achievements": file.filename}},
        upsert=True
    )

    return {"message": f"Achievement '{file.filename}' uploaded for {employee_name}"}


# Helper Functions to Retrieve Certifications and Achievements
async def get_certifications(employee_name: str):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)
    if not os.path.exists(certification_dir):
        raise HTTPException(status_code=404, detail="No certifications found for this employee.")
    certification_files = [f for f in os.listdir(certification_dir) if os.path.isfile(os.path.join(certification_dir, f))]
    return {"certifications": certification_files}

async def get_achievements(employee_name: str):
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)
    if not os.path.exists(achievement_dir):
        raise HTTPException(status_code=404, detail="No achievements found for this employee.")
    achievement_files = [f for f in os.listdir(achievement_dir) if os.path.isfile(os.path.join(achievement_dir, f))]
    return {"achievements": achievement_files}