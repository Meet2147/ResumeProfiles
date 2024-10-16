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
from typing import Dict

# Initialize FastAPI
app = FastAPI()

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["employee_db"]
collection = db["employees"]  # Using the "employees" collection

# OpenAI API Key
openai.api_key = ''

# Initialize Weaviate Client
weaviate_client = weaviate.Client("http://localhost:8080")  # Assuming Weaviate runs locally

# Initialize HuggingFace Embeddings (Replace this with the actual model)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Define the request body format using Pydantic
class QueryRequest(BaseModel):
    query: str

# Helper function to upload a resume and store in MongoDB and Weaviate
@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    file_location = f"./uploaded_resumes/{file.filename}"  # Save to uploaded_resumes directory
    os.makedirs(os.path.dirname(file_location), exist_ok=True)  # Create directory if it doesn't exist

    # Save the uploaded file
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Process the uploaded file (PDF/DOCX) and extract text
    if file.filename.endswith(".pdf"):
        loader = PyMuPDFLoader(file_location)
    elif file.filename.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_location)
    else:
        return {"error": "Unsupported file format. Only PDF and DOCX are supported."}

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

# Function to query Weaviate and fetch relevant resumes from MongoDB
def query_resumes(query: str) -> Dict[str, str]:
    # Generate embedding for the query
    query_embedding = embedding_model.embed_query(query)

    # Query Weaviate for similar embeddings
    response = weaviate_client.query.get("Resume", ["file_name", "content"]) \
        .with_near_vector({"vector": query_embedding}) \
        .with_limit(1) \
        .do()

    if response and "data" in response and response["data"]["Get"]["Resume"]:
        resume_data = response["data"]["Get"]["Resume"][0]
        file_name = resume_data["file_name"]

        # Fetch the corresponding resume from MongoDB
        resume = collection.find_one({"file_name": file_name})

        if resume:
            return {
                "resume_content": resume.get("content", "No content found in the resume."),
                "file_name": file_name  # Return the resume file name
            }
        else:
            return {"error": "No relevant resumes found in the database."}
    else:
        return {"error": "No relevant resumes found."}

# Function to generate training suggestions using OpenAI GPT
def generate_training_suggestions(profile_summary: str) -> str:
    suggestion_prompt = f"Given the following profile:\n\n{profile_summary}\n\nSuggest relevant trainings and certifications to enhance their professional skills."
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides training and certification suggestions."},
            {"role": "user", "content": suggestion_prompt}
        ],
        max_tokens=300
    )
    
    suggestions = response.choices[0].message["content"]
    return suggestions

# Combined endpoint to handle both resume query and training suggestions
@app.post("/process_profile/")
async def process_profile(request: QueryRequest) -> Dict[str, str]:
    query = request.query

    # Step 1: Query the resume (using Weaviate and MongoDB)
    resume_data = query_resumes(query)

    # Check for errors in the resume fetching step
    if "error" in resume_data:
        return resume_data  # Return the error if no resume was found

    # Step 2: Generate training suggestions based on the refined resume result
    refined_results = resume_data.get("resume_content", "")
    training_suggestions = generate_training_suggestions(refined_results)

    # Step 3: Return the combined response, including the resume file name
    return {
        "query": query,
        "refined_results": refined_results,
        "training_suggestions": training_suggestions,
        "file_name": resume_data.get("file_name")  # Include the dynamically fetched file name
    }

# Function to fetch all stored documents in Weaviate
@app.get("/get_all_documents/")
async def get_all_documents():
    response = weaviate_client.query.get("Resume", ["file_name", "content"]).do()
    documents = response["data"]["Get"]["Resume"] if "data" in response else []
    return {"documents": documents}