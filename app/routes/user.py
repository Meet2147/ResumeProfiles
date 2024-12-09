import base64
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.config.mongo import get_resume_collection
from app.models.user import UserCreate, UserResponse, UserUpdate
from app.controllers.user_controller import create_user, get_user, update_user, delete_user
import os
from fastapi.responses import FileResponse
import io
from fastapi.responses import StreamingResponse

router = APIRouter()


RESUME_DIRECTORY = "Users/meetjethwa/Downloads/ResumeProfiles-main/app/uploaded_resumes"

@router.post("/", response_model=UserResponse)
async def create_user_route(user: UserCreate):
    return await create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: int):
    return await get_user(user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_route(user_id: int, user_update: UserUpdate):
    return await update_user(user_id, user_update)

@router.delete("/{user_id}")
async def delete_user_route(user_id: int):
    return await delete_user(user_id)


@router.get("/get_resume/{user_id}")
async def get_resume(user_id: int):
    # Iterate through the uploaded resumes to find the file with the given user_id
    for filename in os.listdir(RESUME_DIRECTORY):
        if filename.startswith(f"{user_id}"):
            file_path = os.path.join(RESUME_DIRECTORY, filename)
            if os.path.isfile(file_path):
                return FileResponse(
                    path=file_path,
                    media_type="application/pdf",
                    filename=filename
                )
    
    # If no file is found for the given user_id
    raise HTTPException(status_code=404, detail="Resume not found")

async def get_resume_by_user_id(user_id: int):
    collection = get_resume_collection()
    resume = await collection.find_one({"user_id": user_id})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Decode the Base64-encoded file data
    file_data = base64.b64decode(resume["file_data"])
    print(resume["file_path"])

    # Return metadata and file content
    return {
        "user_id": resume["user_id"],
        "file_name": resume["file_name"],
        "file_path": resume["file_path"],
        "upload_date": resume["upload_date"],
        "content": resume["content"],
        "file_data": file_data  # Return binary content for download
    }


@router.get("/download_resume/{user_id}")
async def download_resume(user_id: int):
    resume = await get_resume_by_user_id(user_id)

    # Create an in-memory file stream
    file_stream = io.BytesIO(resume["file_data"])
    file_stream.seek(0)  # Reset the cursor to the start of the file

    # Determine the media type based on the file extension
    media_type = (
        "application/pdf" if resume["file_name"].endswith(".pdf") 
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # Return the file as a streaming response
    return StreamingResponse(
        file_stream,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={resume['file_name']}"
        }
    )