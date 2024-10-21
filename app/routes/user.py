from fastapi import APIRouter, Depends
from app.models.user import UserCreate, UserResponse, UserUpdate
from app.controllers.user_controller import create_user, get_user, update_user, delete_user

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user_route(user: UserCreate):
    return await create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: str):
    return await get_user(user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_route(user_id: str, user_update: UserUpdate):
    return await update_user(user_id, user_update)

@router.delete("/{user_id}")
async def delete_user_route(user_id: str):
    return await delete_user(user_id)

