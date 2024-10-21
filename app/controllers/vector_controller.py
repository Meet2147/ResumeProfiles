import os
import uuid
from pydantic import BaseModel
from fastapi import File, UploadFile
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
import docx
from typing import Dict
from app.services import embedding_storage, rag_pipeline,model_inference,embedding_generation
rag_pipeline.process_query
embedding_storage.search_vectors
embedding_storage.generate_vectors
model_inference.generate_response

async def handle_uploaded_resume(file: UploadFile):
    print("hit in controller file upload_resume")
    
    file_location = f"./uploaded_resumes/{file.filename}"  # Save to uploaded_resumes directory
    os.makedirs(os.path.dirname(file_location), exist_ok=True)  # Create directory if it doesn't exist

    # Save the uploaded file
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Determine file type and load accordingly
    if file.filename.endswith(".pdf"):
        loader = PyMuPDFLoader(file_location)
    elif file.filename.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_location)
    else:
        return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

    # Load the documents from the file
    documents = loader.load()

    try:
        print("Vectors sent for generation")
        await embedding_generation.generate_vectors(file,documents)
        print("Vectors sent for storage")
        embedding_storage.generate_vectors(file)  # Pass documents to the vector generation

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    return {"message": f"Uploaded and processed {file.filename} successfully!", "documents": documents}
