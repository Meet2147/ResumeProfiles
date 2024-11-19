from fastapi import APIRouter

router = APIRouter()

@router.get("/info")
async def get_user_info():
    return {"message": "User endpoint"}