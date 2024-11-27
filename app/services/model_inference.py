import openai
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
from config.weaviate import connect_to_weaviate
from config.mongo import get_resume_collection
import io
import base64
from fastapi.responses import StreamingResponse
from routes.user import get_resume_by_user_id
# weaviate_client = weaviate.Client("http://localhost:8080") 
 # Assuming Weaviate runs locally
openai.api_key = ""
# Initialize HuggingFace Embeddings (Replace this with the actual model)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")



# async def download_resume(user_id: int):
#     # Retrieve the resume data for the given user ID
#     resume = await get_resume_by_user_id(user_id)

#     # Create an in-memory file stream for the resume
#     file_stream = io.BytesIO(resume["file_data"])
#     file_stream.seek(0)  # Reset the cursor to the start of the file

#     # Determine the media type based on the file extension
#     media_type = (
#         "application/pdf"
#         if resume["file_name"].endswith(".pdf")
#         else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#     )

#     # Return the file as a streaming response
#     return StreamingResponse(
#         file_stream,
#         media_type=media_type,
#         headers={
#             "Content-Disposition": f"attachment; filename={resume['file_name']}"
#         },
#     )
### HR Profile Query Functions ###
async def query_profiles(query: str, limit: int = 5) -> List[Dict[str, str]]:
    client = await connect_to_weaviate()
    # Generate embedding for the query
    query_embedding = embedding_model.embed_query(query)

    # Query Weaviate for similar embeddings across all profiles
    response = client.query.get("Resume", ["file_name", "content"]) \
        .with_near_vector({"vector": query_embedding}) \
        .with_limit(limit).do()

    if response and "data" in response and response["data"]["Get"]["Resume"]:
        profiles = response["data"]["Get"]["Resume"]
        print("hit from model inference query_profiles")
        return profiles
    else:
        return []

async def generate_detailed_response(query: str, profiles: list) -> str:
    # Construct a summary of profiles
    profiles_summary = ""
    for profile in profiles:
        profiles_summary += f"*Profile: {profile['file_name']}*\nSummary: {profile['content']}\n\n"

    prompt = (
    f"As an HR assistant, your goal is to help streamline HR processes and provide insightful answers about employee profiles. "
    f"Below are the details of the employee profiles available. Please respond to the user's query by carefully analyzing these profiles.\n\n"
    f"Guidelines:\n"
    f"- Maintain strict confidentiality of all employee data\n"
    f"- If any requested information is missing, clearly state what's unavailable\n"
    f"- Format responses in bullet points for better readability\n"
    f"- Avoid corporate jargon and use clear, professional language\n"
    f"- For complex queries, provide a brief summary followed by detailed explanation\n"
    f"- Flag any potential compliance issues in the response\n\n"
    f"Response format:\n"
    f"1. Summary (2-3 sentences)\n"
    f"2. Detailed response (bullet points)\n"
    f"3. Additional considerations (if any)\n\n"
    f"Profiles:\n{profiles_summary}\n\n"
    f"User's Query: {query}"
)

    response = openai.ChatCompletion.create(
    model="gpt-4",
    
    messages=[
    {"role": "system", "content": 
        """You are an HR assistant specialized in resume analysis and HR analytics. Your primary focus is streamlining HR processes by providing insights about employee profiles and resumes.

        Core Guidelines:
        1. Be creative and thoughtful in your responses while maintaining accuracy
        2. Use professional but simple language, avoiding corporate jargon
        3. Structure responses in an easily digestible format
        4. Maintain strict confidentiality of all resume data
        5. Only answer questions related to resumes and profiles
        6. In the response keep the profile name and the pofile file name as that is the user id

        Response Format:
        1. Brief summary (2-3 sentences)
        2. Detailed analysis (bullet points)
        3. Recommendations (if applicable)

        Error Handling:
        - For non-resume queries: Respond with "I can only assist with resume-related questions. Please rephrase your query accordingly."
        - For incomplete data: Clearly indicate what information is missing
        - For ambiguous queries: Ask for specific clarification

        Privacy Guidelines:
        - Never share sensitive personal information
        - Aggregate data when possible
        - Flag any potential privacy concerns

        Example Good Response:
        "Summary: [Brief overview]
        Analysis:
        • Point 1
        • Point 2
        Recommendations:
        • Suggestion 1"
        """},
    {"role": "user", "content": prompt}
    ],
    max_tokens=5000  # Increase token limit for longer responses
)

    answer = response.choices[0].message["content"]
    print("hit from model inference generate_detailed response")
    return answer