from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from controllers.skills_controller import get_achievements, get_certifications, upload_achievement, upload_certification

router = APIRouter()

# Endpoint to upload certification file, linked to user_id
@router.post("/upload_certification/{user_id}")
async def upload_certification_endpoint(user_id: str, file: UploadFile = File(...)):
    return await upload_certification(user_id, file)

# Endpoint to upload achievement file, linked to user_id
@router.post("/upload_achievements/{user_id}")
async def upload_achievements_endpoint(user_id: str, file: UploadFile = File(...)):
    return await upload_achievement(user_id, file)

# Endpoint to retrieve certifications, linked to user_id
@router.get("/get_certifications/{user_id}")
async def get_certifications_endpoint(user_id: str):
    return await get_certifications(user_id)

# Endpoint to retrieve achievements, linked to user_id
@router.get("/get_achievements/{user_id}")
async def get_achievements_endpoint(user_id: str):
    return await get_achievements(user_id)