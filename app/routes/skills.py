from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.controllers.skills_controller import get_achievements, get_certifications, upload_achievement, upload_certification
from app.services.embedding_generation import update_skills, update_certifications, update_projects
router = APIRouter()

# Endpoint to upload certification file, linked to user_id
# @router.post("/upload_certification/{user_id}")
# async def upload_certification_endpoint(user_id: str, file: UploadFile = File(...)):
#     return await upload_certification(user_id, file)

# # Endpoint to upload achievement file, linked to user_id
# @router.post("/upload_achievements/{user_id}")
# async def upload_achievements_endpoint(user_id: str, file: UploadFile = File(...)):
#     return await upload_achievement(user_id, file)

# # Endpoint to retrieve certifications, linked to user_id
# @router.get("/get_certifications/{user_id}")
# async def get_certifications_endpoint(user_id: str):
#     return await get_certifications(user_id)

# # Endpoint to retrieve achievements, linked to user_id
# @router.get("/get_achievements/{user_id}")
# async def get_achievements_endpoint(user_id: str):
#     return await get_achievements(user_id)


@router.put("/update-skills/")
async def update_user_skills(user_id: int = Form(...), new_skills: str = Form(...)):
    try:
        response = await update_skills(user_id, new_skills)
        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating skills: {str(e)}")    
    

@router.put("/update-certifications/")
async def update_user_certifications(user_id: int = Form(...), new_certifications: str = Form(...)):
    try:
        response = await update_certifications(user_id, new_certifications)
        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating certifications: {str(e)}")
    
@router.put("/update-projects/")
async def update_user_projects(user_id: int = Form(...), new_projects: str = Form(...)):
    try:
        response = await update_projects(user_id, new_projects)
        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating projects: {str(e)}")