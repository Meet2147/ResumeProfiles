from pydantic import BaseModel  # Import BaseModel for Pydantic model
from app.controllers.vector_controller import handle_uploaded_resume
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from datetime import datetime
from app.config.weaviate import connect_to_weaviate, fetch_user_data_async
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from fastapi.responses import JSONResponse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import os
import uuid
import openai
from PyPDF2 import PdfReader
from app.services.model_inference import generate_detailed_response1
from fpdf import FPDF


# FastAPI router setup
router = APIRouter()

# class Message(BaseModel):  # Define a model for the request body
#     message: str

# class QueryRequest(BaseModel):
#     query: str

# @router.get("/")
# async def chat_root():
#     print("hit from vector router")
#     return {"message": "Welcome to the vector API"}

# @router.post("/send")
# async def upload_resume(file: UploadFile = File(...)):
#     print("hit from vector router post api")
#     result = await handle_uploaded_resume(file)
#     return result



class QueryRequest(BaseModel):
    query: str

@router.get("/")
async def chat_root():
    print("hit from vector router")
    return {"message": "Welcome to the vector API"}

@router.post("/upload_resume/{user_id}")
async def upload_resume(user_id: int, file: UploadFile = File(...)):
    print("hit from vector router post api")

    # Verify that the user_id is valid before proceeding (optional)
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Pass the user_id to the handle_uploaded_resume function
    result = await handle_uploaded_resume(user_id, file)
    return result

    
# # ///////////////////////////////////////////////////////////////////////////////
# from fastapi import FastAPI, UploadFile, Form, HTTPException
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from weaviate import Client
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import os
# import uuid
# from datetime import datetime
# from typing import List
# from langchain_huggingface import HuggingFaceEmbeddings
# from datetime import datetime

# # Initialize the embedding model
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# app = FastAPI()

# @router.patch("/update_embeddings/{user_id}")
# async def update_embeddings(
#     user_id: int,
#     file: UploadFile = Form(...),
# ):
#     """
#     Update embeddings in Weaviate based on the uploaded PDF file.

#     Args:
#         user_id (int): The user ID.
#         file (UploadFile): The PDF file uploaded by the user.

#     Returns:
#         JSONResponse: Success or failure message.
#     """
#     try:
#         # Save the uploaded file temporarily
#         temp_file_path = f"/tmp/{file.filename}"
#         with open(temp_file_path, "wb") as temp_file:
#             temp_file.write(await file.read())

#         # Extract text from PDF (replace with your PDF parsing logic)
#         # For simplicity, let's assume the entire content is in `content`.
#         content = "Mock extracted content from PDF"  # Replace with actual content extraction logic

#         # Split document into chunks
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = text_splitter.split_text(content)

#         # Generate embeddings and update Weaviate
#         client = await connect_to_weaviate()
#         class_name = "Resume"

#         for i, chunk in enumerate(chunks):
#             chunk_embedding = embedding_model.embed_query(chunk)
#             chunk_id = str(uuid.uuid4())
#             properties = {
#                 "user_id": user_id,
#                 "file_name": file.filename,
#                 "chunk_id": chunk_id,
#                 "content": chunk,
#                 "updated_at": datetime.utcnow().isoformat()
#             }

#             # Update existing embedding or add a new one
#             existing_data = client.query.raw(f"""
#             {{
#                 Get {{
#                     {class_name}(
#                         where: {{
#                             path: ["user_id"],
#                             operator: Equal,
#                             valueNumber: {user_id}
#                         }}
#                     ) {{
#                         chunk_id
#                     }}
#                 }}
#             }}
#             """)

#             # Check if chunk already exists in Weaviate (logic depends on schema)
#             existing_chunk_ids = [
#                 obj["chunk_id"] for obj in existing_data.get("data", {}).get("Get", {}).get(class_name, [])
#             ]

#             if chunk_id in existing_chunk_ids:
#                 # Update existing object
#                 client.data_object.update(
#                     data_object=properties,
#                     class_name=class_name,
#                     uuid=chunk_id,
#                     vector=chunk_embedding,
#                 )
#             else:
#                 # Create a new object
#                 client.data_object.create(
#                     data_object=properties,
#                     class_name=class_name,
#                     vector=chunk_embedding,
#                 )

#         # Clean up temporary file
#         os.remove(temp_file_path)

#         return JSONResponse(
#             {"message": f"Embeddings for file '{file.filename}' successfully updated in Weaviate."},
#             status_code=200,
#         )

#     except Exception as e:
#         print(f"Error: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to process the file: {e}")



# Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")





# Helper function to extract text from a PDF file
def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()  # Extract text from each page
    return text

@router.patch("/update_embeddings/{user_id}")
async def update_embeddings(
    user_id: int,
    file: UploadFile = Form(...),
):
    """
    Update embeddings in Weaviate based on the uploaded PDF file.

    Args:
        user_id (int): The user ID.
        file (UploadFile): The PDF file uploaded by the user.

    Returns:
        JSONResponse: Success or failure message.
    """
    try:
        # Save the uploaded file temporarily
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Extract text from PDF
        content = extract_text_from_pdf(temp_file_path)

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(content)

        # Connect to Weaviate
        client = await connect_to_weaviate()
        class_name = "Resume"

        for i, chunk in enumerate(chunks):
            # Generate embeddings for the chunk
            chunk_embedding = embedding_model.embed_query(chunk)
            chunk_id = str(uuid.uuid4())
            properties = {
                "user_id": user_id,
                "file_name": file.filename,
                "chunk_id": chunk_id,
                "content": chunk,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Check if chunk already exists in Weaviate (query Weaviate to check if chunk exists)
            existing_data = client.query.raw(f"""
            {{
                Get {{
                    {class_name}(
                        where: {{
                            path: ["user_id"],
                            operator: Equal,
                            valueNumber: {user_id}
                        }}
                    ) {{
                        chunk_id
                    }}
                }}
            }}
            """)

            # Extract chunk_ids from Weaviate response
            existing_chunk_ids = [
                obj["chunk_id"] for obj in existing_data.get("data", {}).get("Get", {}).get(class_name, [])
            ]

            if chunk_id in existing_chunk_ids:
                # Update the existing chunk in Weaviate
                client.data_object.update(
                    data_object=properties,
                    class_name=class_name,
                    uuid=chunk_id,
                    vector=chunk_embedding,
                )
            else:
                # Create a new chunk object in Weaviate
                client.data_object.create(
                    data_object=properties,
                    class_name=class_name,
                    vector=chunk_embedding,
                )

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(
            {"message": f"Embeddings for file '{file.filename}' successfully updated in Weaviate."},
            status_code=200,
        )

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process the file: {e}")


@router.get("/employee/{user_id}")
async def fetch_resumes_by_user_id(user_id: int):
    """
    Fetch resumes from Weaviate based on user_id.

    Args:
        user_id (int): The user ID to filter the resumes.

    Returns:
        list: List of resumes matching the user_id.
    """
    try:
        # Connect to Weaviate client
        client = await connect_to_weaviate()

        # Define the GraphQL query dynamically
        query = """
        {
            Get {
                Resume(
                    where: {
                        path: ["user_id"],
                        operator: Equal,
                        valueNumber: %d
                    }
                ) {
                    user_id
                    file_name
                    chunk_id
                    content
                }
            }
        }
        """ % user_id

        # Execute the GraphQL query
        response = client.query.raw(query)
        return response.get("data", {}).get("Get", {}).get("Resume", [])

    except Exception as e:
        print(f"Error fetching data from Weaviate: {e}")
        return {"error": str(e)}
    
def create_pdf(content: str, filename: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split the content into lines and add each line to the PDF
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    # Save the PDF file
    pdf.output(filename)
    return filename

@router.get("/employee_resume/{user_id}")
async def generate_new_pdf(user_id: int):
    print("Generating PDF for user_id >", user_id)
    try:
        # Connect to Weaviate client
        client = await connect_to_weaviate()

        # Define the GraphQL query dynamically
        query = f"""
        {{
            Get {{
                Resume(
                    where: {{
                        path: ["user_id"],
                        operator: Equal,
                        valueNumber: {user_id}
                    }}
                ) {{
                    content
                }}
            }}
        }}
        """

        # Execute the GraphQL query
        response = client.query.raw(query)
        resumes = response.get("data", {}).get("Get", {}).get("Resume", [])
        print("Response >", response)
        print("Response data to be returned >", resumes)

        if resumes:
            # Assuming each resume content is a string, concatenate or format them as needed
            resume_data = "\n\n".join(resume['content'] for resume in resumes)

            # Create the prompt with the retrieved resume data
            prompt = f"""
            You have been given the following resume data:
            {resume_data}

            Your task is to rebuild a professional resume from this data.
            """

            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )

            # Extract the response text
            reconstructed_resume = response['choices'][0]['message']['content']
            print("Reconstructed Resume >", reconstructed_resume)

            # Create a PDF file from the reconstructed resume
            pdf_filename = f"user_{user_id}_resume.pdf"
            pdf_path = create_pdf(reconstructed_resume, pdf_filename)

            return {"pdf_path": pdf_path}

        else:
            return {"error": "No resume data found for the given user_id"}

    except Exception as e:
        print(f"Error fetching data from Weaviate: {e}")
        return {"error": str(e)}
    
# async def genrate_new_pdf(user_id: int):
#     print("generating pdf for user_id >",user_id)
#     try:
#         # Connect to Weaviate client
#         client = await connect_to_weaviate()

#         # Define the GraphQL query dynamically
#         query = """
#         {
#             Get {
#                 Resume(
#                     where: {
#                         path: ["user_id"],
#                         operator: Equal,
#                         valueNumber: %d
#                     }
#                 ) {
#                     content
#                 }
#             }
#         }
#         """ % user_id

#         # Execute the GraphQL query
#         response = client.query.raw(query)
#         a = response.get("data", {}).get("Get", {}).get("Resume", [])
#         print("response >",response)
#         print("response data to be returned>",a)
        
#         return a 

#     except Exception as e:
#         print(f"Error fetching data from Weaviate: {e}")
#         return {"error": str(e)}