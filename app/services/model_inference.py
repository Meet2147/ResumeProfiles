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

# weaviate_client = weaviate.Client("http://localhost:8080") 
 # Assuming Weaviate runs locally
openai.api_key = "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"
# Initialize HuggingFace Embeddings (Replace this with the actual model)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")



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
        profiles_summary += f"**Profile: {profile['file_name']}**\nSummary: {profile['content']}\n\n"

    prompt = (
    f"As an HR assistant, your goal is to help streamline HR processes and provide insightful answers about employee profiles. "
    f"Below are the details of the employee profiles available. Please respond to the user's query by carefully analyzing these profiles. "
    f"Ensure that your response is thoughtful, professional, and avoids corporate jargon. Summarize key points where necessary to provide a concise and clear answer.\n\n"
    f"Profiles:\n\n{profiles_summary}\n\n"
    f"User's Query: {query}"
)

    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an HR assistant designed to streamline HR processes and provide HR analytics by answering specific questions about employee profiles. When responding, please follow these guidelines:\n"
             "1. Be creative and thoughtful in your responses.\n"
             "2. Maintain a professional tone, but keep the language simple and clear. Avoid complex corporate jargon.\n"
             "3. Ensure the information is accurate and helpful, addressing the user's query in a straightforward manner.\n"
             "4. You cannot answer anything else other than resumes. if such a question is asked please answer Sorry I can only answer  questions about resumes."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=5000  # Increase token limit for longer responses
)

    answer = response.choices[0].message["content"]
    print("hit from model inference generate_detailed response")
    return answer
