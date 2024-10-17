

import os
import uuid
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from pymongo import MongoClient
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import weaviate
import openai
from typing import Dict, List
import os
from fastapi import FastAPI, HTTPException
from pdf2image import convert_from_path
from fastapi.responses import FileResponse
from typing import List

# Initialize FastAPI
app = FastAPI()

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["employee_db"]
collection = db["employees"]  # Using the "employees" collection

# OpenAI API Key
openai.api_key = ''  # Replace with your actual OpenAI API key'  # Replace with your actual OpenAI API key'  # Replace with your actual OpenAI API key

# Initialize Weaviate Client
weaviate_client = weaviate.Client("http://localhost:8080")  # Assuming Weaviate runs locally

# Initialize HuggingFace Embeddings (Replace this with the actual model)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

RESUME_DIRECTORY = "uploaded_resumes"
# Define the request body format using Pydantic
class QueryRequest(BaseModel):
    query: str
    conversation_id: str


def convert_pdf_to_images(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert PDF to images (one image per page)
    images = convert_from_path(pdf_path)
    
    # Save images to the output directory
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path, "PNG")

    return output_dir
# Helper function to upload a resume and store in MongoDB and Weaviate
@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    # Save the uploaded PDF file
    file_location = os.path.join(RESUME_DIRECTORY, file.filename)
    os.makedirs(RESUME_DIRECTORY, exist_ok=True)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Convert PDF to images
    profile_name = file.filename.replace('.pdf', '')
    image_dir = os.path.join(RESUME_DIRECTORY, profile_name)
    convert_pdf_to_images(file_location, image_dir)

    # Process the uploaded file (PDF) and extract text for embeddings
    if file.filename.endswith(".pdf"):
        loader = PyMuPDFLoader(file_location)
    else:
        return {"error": "Unsupported file format. Only PDF is supported."}

    documents = loader.load()

    # Split text into chunks for better embedding
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    # Store data in MongoDB
    resume_data = {
        "file_name": file.filename,
        "content": documents[0].page_content,  # Full content of the resume
        "chunks": [chunk.page_content for chunk in chunks],  # Individual chunks of text
    }
    collection.insert_one(resume_data)

    # Generate embeddings for each chunk and store in Weaviate
    for i, chunk in enumerate(chunks):
        chunk_embedding = embedding_model.embed_query(chunk.page_content)  # Generate embeddings
        chunk_id = str(uuid.uuid4())  # Generate a unique ID for each chunk

        # Create or update data in Weaviate
        weaviate_client.data_object.create(
            {
                "file_name": file.filename,
                "chunk_id": i,
                "content": chunk.page_content
            },
            "Resume",  # Assuming you have a class `Resume` in Weaviate schema
            vector=chunk_embedding  # Store the embedding
        )

    return {"message": f"Resume '{file.filename}' uploaded, processed, and converted to images successfully!"}

# Function to query Weaviate and fetch relevant profiles
def query_profiles(query: str, limit: int = 5) -> List[Dict[str, str]]:
    # Generate embedding for the query
    query_embedding = embedding_model.embed_query(query)

    # Query Weaviate for similar embeddings across all profiles
    response = weaviate_client.query.get("Resume", ["file_name", "content"]) \
        .with_near_vector({"vector": query_embedding}) \
        .with_limit(limit).do()

    if response and "data" in response and response["data"]["Get"]["Resume"]:
        profiles = response["data"]["Get"]["Resume"]
        return profiles
    else:
        return []

# Function to generate detailed responses based on multiple employee profiles
def generate_detailed_response(query: str, profiles: list, conversation_id: str) -> str:
    # Construct a summary of profiles
    profiles_summary = ""
    for profile in profiles:
        profiles_summary += f"**Profile: {profile['file_name']}**\nSummary: {profile['content']}\n\n"

    prompt = f"You are an HR assistant helping with employee profiles. Based on the following profiles, answer the user's query:\n\n{profiles_summary}\n\nQuery: {query}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an HR assistant that answers specific questions about employee profiles."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024  # Increase token limit for longer responses
    )

    answer = response.choices[0].message["content"]
    return answer

# Check if the query is asking for a resume
def is_resume_request(query: str) -> bool:
    """ Check if the user is asking for a resume """
    keywords = ["show resume", "view resume", "resume of"]
    return any(keyword in query.lower() for keyword in keywords)

# Combined endpoint to handle profile queries across all stored resumes
@app.post("/process_profile/")
async def process_profile(request: QueryRequest) -> Dict[str, str]:
    query = request.query
    conversation_id = request.conversation_id

    # Step 1: Check if the query is a request to view a resume
    if is_resume_request(query):
        # Query Weaviate for relevant profiles
        profiles_data = query_profiles(query, limit=5)

        # Check if any profiles are found
        if not profiles_data:
            return {"error": "No profiles found for the requested resume."}

        # Return the first matching profile's resume file name
        file_name = profiles_data[0].get("file_name", "")
        if file_name:
            # Remove the path and return just the profile name (no local file path)
            profile_name = file_name.replace('.pdf', '')  # Assuming the filename is 'profile.pdf'
            return {
                "query": query,
                "conversation_id": conversation_id,
                "response": f"Here is the resume for the requested profile: {file_name}",
                "file_name": profile_name  # Returning the profile name, not the file path
            }
        else:
            return {"error": "Resume not available for the requested profile."}

    # Step 2: Normal profile querying and response generation
    profiles_data = query_profiles(query, limit=5)

    # Check if any profiles are found
    if not profiles_data:
        return {"error": "No relevant profiles found."}

    # Generate detailed response based on the profiles fetched
    response = generate_detailed_response(query, profiles_data, conversation_id)

    # Return the response to the user
    return {
        "query": query,
        "conversation_id": conversation_id,
        "response": response
        
    }

# Function to fetch all stored documents in Weaviate (if needed)
@app.get("/get_all_documents/")
async def get_all_documents():
    response = weaviate_client.query.get("Resume", ["file_name", "content"]).do()
    documents = response["data"]["Get"]["Resume"] if "data" in response else []
    return {"documents": documents}

# Endpoint to get the list of images for a specific profile
@app.get("/get_resume_images/{profile_name}")
async def get_resume_images(profile_name: str):
    image_dir = os.path.join(RESUME_DIRECTORY, profile_name)
    
    if not os.path.exists(image_dir):
        raise HTTPException(status_code=404, detail="Profile images not found.")

    # List all the image files in the directory
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith(".png")])
    
    if not image_files:
        raise HTTPException(status_code=404, detail="No images found for this profile.")

    return {"images": image_files}

# Endpoint to serve individual images
@app.get("/serve_image/{profile_name}/{image_name}")
async def serve_image(profile_name: str, image_name: str):
    image_path = os.path.join(RESUME_DIRECTORY, profile_name, image_name)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    
    return FileResponse(image_path, media_type="image/png")
