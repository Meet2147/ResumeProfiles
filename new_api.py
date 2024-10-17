import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import weaviate
import openai
from typing import Dict, List
from fastapi.responses import FileResponse

# Initialize FastAPI
app = FastAPI()

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["employee_db"]
collection = db["employees"]  # Using the "employees" collection

# OpenAI API Key
openai.api_key = ''  # Replace with your actual OpenAI API key

# Initialize Weaviate Client
weaviate_client = weaviate.Client("http://localhost:8080")  # Assuming Weaviate runs locally

# Initialize HuggingFace Embeddings (Replace this with the actual model)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

RESUME_DIRECTORY = "uploaded_resumes"
CERTIFICATION_DIRECTORY = "uploaded_certifications"
ACHIEVEMENT_DIRECTORY = "uploaded_achievements"

# Define the request body format using Pydantic
class QueryRequest(BaseModel):
    query: str
    conversation_id: str


def save_file_to_directory(file: UploadFile, directory: str):
    file_location = os.path.join(directory, file.filename)
    os.makedirs(directory, exist_ok=True)
    
    # Save the file
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    
    return file_location

# Helper function to upload a resume and store in MongoDB and Weaviate
@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    # Save the uploaded PDF file
    file_location = os.path.join(RESUME_DIRECTORY, file.filename)
    os.makedirs(RESUME_DIRECTORY, exist_ok=True)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Convert PDF to images and store it (if needed)
    profile_name = file.filename.replace('.pdf', '')
    image_dir = os.path.join(RESUME_DIRECTORY, profile_name)
    
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

    return {"message": f"Resume '{file.filename}' uploaded and processed successfully!"}


### Upload Certifications for Employee Profiles ###
@app.post("/upload_certification/{employee_name}")
async def upload_certification(employee_name: str, file: UploadFile = File(...)):
    # Save the certification in the employee's directory
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)
    os.makedirs(certification_dir, exist_ok=True)

    # Save the certification file
    file_location = os.path.join(certification_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Optionally, you can also store details in MongoDB for certifications
    collection.update_one(
        {"file_name": f"{employee_name}.pdf"}, 
        {"$push": {"certifications": file.filename}},
        upsert=True
    )

    return {"message": f"Certification '{file.filename}' uploaded for {employee_name}"}


### Upload Achievements for Employee Profiles ###
@app.post("/upload_achievement/{employee_name}")
async def upload_achievement(employee_name: str, file: UploadFile = File(...)):
    # Save the achievement in the employee's directory
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)
    os.makedirs(achievement_dir, exist_ok=True)

    # Save the achievement file
    file_location = os.path.join(achievement_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Optionally, you can also store details in MongoDB for achievements
    collection.update_one(
        {"file_name": f"{employee_name}.pdf"}, 
        {"$push": {"achievements": file.filename}},
        upsert=True
    )

    return {"message": f"Achievement '{file.filename}' uploaded for {employee_name}"}


### HR Profile Query Functions ###
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


@app.post("/process_profile/")
async def process_profile(request: QueryRequest) -> Dict[str, str]:
    query = request.query
    conversation_id = request.conversation_id

    profiles_data = query_profiles(query, limit=5)

    if not profiles_data:
        return {"error": "No relevant profiles found."}

    response = generate_detailed_response(query, profiles_data, conversation_id)

    return {
        "query": query,
        "conversation_id": conversation_id,
        "response": response
    }

### Additional Functionality: Fetch Certifications or Achievements ###
@app.get("/get_certifications/{employee_name}")
async def get_certifications(employee_name: str):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, employee_name)

    if not os.path.exists(certification_dir):
        raise HTTPException(status_code=404, detail="No certifications found for this employee.")

    # List all certification files
    certification_files = [f for f in os.listdir(certification_dir) if os.path.isfile(os.path.join(certification_dir, f))]

    return {"certifications": certification_files}

@app.get("/get_achievements/{employee_name}")
async def get_achievements(employee_name: str):
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, employee_name)

    if not os.path.exists(achievement_dir):
        raise HTTPException(status_code=404, detail="No achievements found for this employee.")

    # List all achievement files
    achievement_files = [f for f in os.listdir(achievement_dir) if os.path.isfile(os.path.join(achievement_dir, f))]

    return {"achievements": achievement_files}
