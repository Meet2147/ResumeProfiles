
import os
from fastapi import File, UploadFile, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from services import embedding_storage,embedding_generation



# MongoDB Connection
MONGO_DB_URL = "mongodb://localhost:27017"  # Update with your MongoDB connection string
mongo_client = AsyncIOMotorClient(MONGO_DB_URL)
db = mongo_client["employee_profiles"]  # Your database name
collection = db["users"]  # Your collection name

# Directories
CERTIFICATION_DIRECTORY = "uploaded_certifications"
ACHIEVEMENT_DIRECTORY = "uploaded_achievements"

# Upload Certification and Add to Profile Vectors
async def upload_certification(user_id: str, file: UploadFile = File(...)):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, user_id)
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
        vectors = await embedding_generation.generate_cert_vectors(user_id, file, documents)
        
        # Append the new vectors to the user's existing profile
        print("Storing vectors in the user's profile...")
        

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    # Update MongoDB
    await collection.update_one(
        {"user_id": user_id}, 
        {"$push": {"certifications": file.filename}},
        upsert=True
    )

    return {"message": f"Certification '{file.filename}' uploaded for user ID {user_id}"}

async def upload_resume(user_id: str, file: UploadFile = File(...)):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, user_id)
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
        vectors = await embedding_generation.generate_vectors(user_id, file, documents)
        
        # Append the new vectors to the user's existing profile
        print("Storing vectors in the user's profile...")
        

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    # Update MongoDB
    await collection.update_one(
        {"user_id": user_id}, 
        {"$push": {"certifications": file.filename}},
        upsert=True
    )

    return {"message": f"Certification '{file.filename}' uploaded for user ID {user_id}"}


# Upload Achievement and Add to Profile Vectors
async def upload_achievement(user_id: str, file: UploadFile = File(...)):
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, user_id)
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
        vectors = await embedding_generation.generate_cert_vectors(user_id, file, documents)
        
        # Append the new vectors to the user's existing profile
        print("Storing vectors in the user's profile...")
        

    except Exception as e:
        return {"error": f"Error generating vectors: {str(e)}"}

    # Update MongoDB
    await collection.update_one(
        {"user_id": user_id}, 
        {"$push": {"achievements": file.filename}},
        upsert=True
    )

    return {"message": f"Achievement '{file.filename}' uploaded for user ID {user_id}"}


# Helper Functions to Retrieve Certifications and Achievements
async def get_certifications(user_id: str):
    certification_dir = os.path.join(CERTIFICATION_DIRECTORY, user_id)
    if not os.path.exists(certification_dir):
        raise HTTPException(status_code=404, detail="No certifications found for this user.")
    certification_files = [f for f in os.listdir(certification_dir) if os.path.isfile(os.path.join(certification_dir, f))]
    return {"certifications": certification_files}

async def get_achievements(user_id: str):
    achievement_dir = os.path.join(ACHIEVEMENT_DIRECTORY, user_id)
    if not os.path.exists(achievement_dir):
        raise HTTPException(status_code=404, detail="No achievements found for this user.")
    achievement_files = [f for f in os.listdir(achievement_dir) if os.path.isfile(os.path.join(achievement_dir, f))]
    return {"achievements": achievement_files}