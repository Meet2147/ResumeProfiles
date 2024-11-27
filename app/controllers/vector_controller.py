

import base64
from datetime import datetime
import os
import uuid
from pydantic import BaseModel
from fastapi import File, HTTPException, UploadFile
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
import docx
from typing import Dict
from config.mongo import get_resume_collection
from services import embedding_storage, rag_pipeline, model_inference, embedding_generation

async def handle_uploaded_resume(user_id: int, file: UploadFile):
    print("hit in controller file upload_resume")

    # Extract the file extension and rename the file
    _, file_extension = os.path.splitext(file.filename)
    if file_extension.lower() not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are supported.")

    renamed_file = f"{user_id}{file_extension}"
    file_location = f"./uploaded_resumes/{renamed_file}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)  # Create directory if it doesn't exist

    # Save the uploaded file with the new name
    with open(file_location, "wb") as f:
        file_content = await file.read()
        f.write(file_content)

    # Load the file using the appropriate loader
    if file_extension.lower() == ".pdf":
        loader = PyMuPDFLoader(file_location)
    elif file_extension.lower() == ".docx":
        loader = UnstructuredWordDocumentLoader(file_location)

    # Load the documents from the file
    documents = loader.load()

    # Store resume metadata and binary file in MongoDB
    collection = get_resume_collection()
    resume_data = {
        "user_id": user_id,
        "file_name": renamed_file,
        "file_path": file_location,
        "upload_date": datetime.utcnow(),
        "content": documents[0].page_content,
        "file_data": base64.b64encode(file_content).decode('utf-8'),  # Store file as base64-encoded string
    }

    # Insert into MongoDB
    result = await collection.insert_one(resume_data)
    print(f"Inserted resume into MongoDB with ID: {result.inserted_id}")

    try:
        # Call embedding generation and storage
        print("Vectors sent for generation")
        await embedding_generation.generate_vectors(user_id, file_location, documents)
        print("Vectors sent for storage")
        embedding_storage.generate_vectors(documents)

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    return {
        "message": f"Uploaded and processed {renamed_file} successfully!",
        "resume_id": str(result.inserted_id),
        "documents": documents
    }