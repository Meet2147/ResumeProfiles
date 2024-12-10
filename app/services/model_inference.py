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
from app.config.weaviate import connect_to_weaviate
from app.config.mongo import get_resume_collection
import io
import base64
from fastapi.responses import StreamingResponse
from app.routes.user import get_resume_by_user_id

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

# async def generate_detailed_response(role:str, query: str, profiles: list) -> str:
#     # Construct a summary of profiles
#     print("role =>",role )
#     profiles_summary = ""
#     for profile in profiles:
#         profiles_summary += f"*Profile: {profile['file_name']}*\nSummary: {profile['content']}\n\n"

#     prompt = (
#     f"As an HR assistant, your goal is to help streamline HR processes and provide insightful answers about employee profiles. "
#     f"Below are the details of the employee profiles available. Please respond to the user's query by carefully analyzing these profiles.\n\n"
#     f"Guidelines:\n"
#     f"- Maintain strict confidentiality of all employee data\n"
#     f"- If any requested information is missing, clearly state what's unavailable\n"
#     f"- Format responses in bullet points for better readability\n"
#     f"- Avoid corporate jargon and use clear, professional language\n"
#     f"- For complex queries, provide a brief summary followed by detailed explanation\n"
#     f"- Flag any potential compliance issues in the response\n\n"
#     f"Response format:\n"
#     f"1. Summary (2-3 sentences)\n"
#     f"2. Detailed response (bullet points)\n"
#     f"3. Additional considerations (if any)\n\n"
#     f"Profiles:\n{profiles_summary}\n\n"
#     f"User's Query: {query}"
# )

#     response = openai.ChatCompletion.create(
#     model="gpt-4",
    
#     messages=[
#     {"role": "system", "content": 
#         """You are an HR assistant specialized in resume analysis and HR analytics. Your primary focus is streamlining HR processes by providing insights about employee profiles and resumes.

#         Core Guidelines:
#         1. Be creative and thoughtful in your responses while maintaining accuracy
#         2. Use professional but simple language, avoiding corporate jargon
#         3. Structure responses in an easily digestible format
#         4. Maintain strict confidentiality of all resume data
#         5. Only answer questions related to resumes and profiles
#         6. In the response keep the profile name and the pofile file name as that is the user id

#         Response Format:
#         1. Brief summary (2-3 sentences)
#         2. Detailed analysis (bullet points)
#         3. Recommendations (if applicable)

#         Error Handling:
#         - For non-resume queries: Respond with "I can only assist with resume-related questions. Please rephrase your query accordingly."
#         - For incomplete data: Clearly indicate what information is missing
#         - For ambiguous queries: Ask for specific clarification

#         Privacy Guidelines:
#         - Never share sensitive personal information
#         - Aggregate data when possible
#         - Flag any potential privacy concerns

#         Example Good Response:
#         "Summary: [Brief overview]
#         Analysis:
#         • Point 1
#         • Point 2
#         Recommendations:
#         • Suggestion 1"
#         """},
#     {"role": "user", "content": prompt}
#     ],
#     max_tokens=5000  # Increase token limit for longer responses
# )

#     answer = response.choices[0].message["content"]
#     print("hit from model inference generate_detailed response")
#     return answer

async def generate_detailed_response1(role: str, query: str, profiles: list) -> str:
    print("Hit from model inference: generate_detailed_response")
    print("Role =>", role)
    # Construct a summary of profiles
    profiles_summary = ""
    for profile in profiles:
        profiles_summary += f"*Profile: {profile['file_name']}*\nSummary: {profile['content']}\n\n"

    # Define role-specific instructions
    role_prompts = {
         "HR Assistant": ("""You are an HR assistant specialized in resume analysis and HR analytics. Your primary focus is streamlining HR processes by providing insights about employee profiles and resumes.

        Core Guidelines:
        1. Be creative and thoughtful in your responses while maintaining accuracy.
        2. Use professional but simple language, avoiding corporate jargon.
        3. Structure responses in an easily digestible format.
        4. Maintain strict confidentiality of all resume data.
        5. Only answer questions related to resumes and profiles.
        6. In the response, keep the profile name and the profile file name as that is the user ID.

        Response Format:
        1. Total Resumes Found: Clearly state the count of unique profiles or resumes at the beginning of the response.
        2. Brief summary (2-3 sentences).
        3. Detailed analysis (bullet points for each profile).
        4. Recommendations (if applicable).

        Error Handling:
        - For non-resume queries: Respond with "I can only assist with resume-related questions. Please rephrase your query accordingly."
        - For incomplete data: Clearly indicate what information is missing.
        - For ambiguous queries: Ask for specific clarification.

        Privacy Guidelines:
        - Never share sensitive personal information.
        - Aggregate data when possible.
        - Flag any potential privacy concerns.

        Example Good Response:
        "Total Resumes Found: [Number]

        Summary: [Brief overview of the profiles analyzed]
        Analysis:
        • Profile 1 (filename): Key points about this profile.
        • Profile 2 (filename): Key points about this profile.
        Recommendations:
        • Suggestion 1
        • Suggestion 2"
        """
        ),
        "Manager": (
            "As a manager, you are responsible for analyzing team performance and suggesting improvements. "
            "Based on the profiles, provide constructive feedback and strategies to align team skills with project goals.\n\n"
        ),
        "Employee": (
            """As an employee, your role is to analyze your own profile and assess your strengths, skills, and areas for improvement. Your response should focus on:
                Acknowledging your key strengths and accomplishments.
                Identifying areas where you can improve or further develop your skills.
                Analyzing any gaps in your experience or expertise and suggesting possible learning paths or actions to address them.
                Reflecting on how your profile aligns with your current job responsibilities and future goals.
                Your analysis should be self-reflective, constructive, and data-driven, providing clear insights into your professional growth.\n\n"""
        ),
        # Add more roles as needed
    }

    # Select the appropriate prompt based on the role
    role_instructions = role_prompts.get(role,"""
""")

    # Construct the full prompt
    prompt = (
        f"{role_instructions}"
        f"Profiles:\n{profiles_summary}\n\n"
        f"User's Query: {query}"
    )
    print("prompt => ",prompt)

    # Call the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": role_instructions},
            {"role": "user", "content": prompt},
        ],
        max_tokens=5000,
    )


    answer = response.choices[0].message["content"]
    print("answer => ",answer)
    return answer

hr_assistant_prompt = '''
    You are an HR assistant specialized in resume analysis and HR analytics. Your primary focus is streamlining HR processes by providing insights about employee profiles and resumes.

    Core Guidelines:
    1. Be creative and thoughtful in your responses while maintaining accuracy.
    2. Use professional but simple language, avoiding corporate jargon.
    3. Structure responses in an easily digestible format.
    4. Maintain strict confidentiality of all resume data.
    5. Only answer questions related to resumes and profiles.
    6. In the response, keep the profile name and the profile file name as that is the user ID.

    Response Format:
    1. Total Resumes Found: Clearly state the count of unique profiles or resumes at the beginning of the response.
    2. Brief summary (2-3 sentences).
    3. Detailed analysis (bullet points for each profile).
    4. Recommendations (if applicable).

    Error Handling:
    - For non-resume queries: Respond with "I can only assist with resume-related questions. Please rephrase your query accordingly."
    - For incomplete data: Clearly indicate what information is missing.
    - For ambiguous queries: Ask for specific clarification.

    Privacy Guidelines:
    - Never share sensitive personal information.
    - Aggregate data when possible.
    - Flag any potential privacy concerns.

    Example Good Response:
    "Total Resumes Found: [Number]

    Summary: [Brief overview of the profiles analyzed]
    Analysis:
    • Profile 1 (filename): Key points about this profile.
    • Profile 2 (filename): Key points about this profile.
    Recommendations:
    • Suggestion 1
    • Suggestion 2"
'''

async def generate_detailed_response(role: str, query: str, profiles: list) -> dict:
    print("Hit from model inference: generate_detailed_response")
    print("Role =>", role)

    # Construct a summary of profiles
    profiles_summary = [
        {
            "file_name": profile["file_name"],
            "content": profile["content"]
        } for profile in profiles
    ]

    # Define role-specific instructions
    role_prompts = {
        "HR Assistant": hr_assistant_prompt,
        "Manager": '''
            As a manager, you are responsible for analyzing team performance and suggesting improvements. 
            Based on the profiles, provide constructive feedback and strategies to align team skills with project goals.
        ''',
        "Employee": '''
            As an employee, your role is to analyze your own profile and assess your strengths, skills, and areas for improvement. Your response should focus on:
            1. Acknowledging your key strengths and accomplishments.
            2. Identifying areas where you can improve or further develop your skills.
            3. Analyzing any gaps in your experience or expertise and suggesting possible learning paths or actions to address them.
            4. Reflecting on how your profile aligns with your current job responsibilities and future goals.
            Your analysis should be self-reflective, constructive, and data-driven, providing clear insights into your professional growth.
        '''
    }

    # Select the appropriate prompt based on the role
    role_instructions = role_prompts.get(role, "No specific prompt available for this role.")

    # Construct the full prompt
    prompt = {
        "role": role,
        "query": query,
        "profiles": profiles_summary
    }

    print("Constructed Prompt =>", prompt)

    # Call the OpenAI API
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": role_instructions},
            {"role": "user", "content": query},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "hr_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "total_resumes_found": {"type": "integer"},
                        "summary": {"type": "string"},
                        "analysis": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "file_name": {"type": "string"},
                                    "key_points": {"type": "string"}
                                },
                                "required": ["file_name", "key_points"],
                                "additionalProperties": False
                            }
                        },
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["total_resumes_found", "summary", "analysis"],
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        max_tokens=5000
    )

    result = response.choices[0].message["content"]
    print("API Response =>", result)

    return result
