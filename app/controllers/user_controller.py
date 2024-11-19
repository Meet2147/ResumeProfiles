# from fastapi import HTTPException
# from models.user import UserCreate, UserResponse, UserUpdate
# from config.mongo import get_user_collection
# from bson import ObjectId
# from datetime import datetime
# import bcrypt

# def hash_password(password: str) -> str:
#     # Generate a salt and hash the password
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password.decode('utf-8')

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     # Check if the provided password matches the hashed password
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# async def create_user(user: UserCreate):
#     user_collection = get_user_collection()

#     # Check if the username or email already exists
#     existing_user = await user_collection.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username or email already registered")

#     user_dict = user.dict()
#     user_dict["password"] = hash_password(user.password)  # Implement password hashing
#     user_dict["created_at"] = datetime.utcnow()  # Set creation time

#     # Insert the user into the database
#     result = await user_collection.insert_one(user_dict)
#     user_id = str(result.inserted_id)

#     return UserResponse(**user_dict, id=user_id)

# async def get_user(user_id: str):
#     user_collection = get_user_collection()

#     user_data = await user_collection.find_one({"_id": ObjectId(user_id)})
#     if not user_data:
#         raise HTTPException(status_code=404, detail="User not found")

#     return UserResponse(**user_data)

# async def update_user(user_id: str, user_update: UserUpdate):
#     user_collection = get_user_collection()

#     # Convert user_id to ObjectId for MongoDB
#     user_data = await user_collection.find_one({"_id": ObjectId(user_id)})
#     if not user_data:
#         raise HTTPException(status_code=404, detail="User not found")

#     update_data = user_update.dict(exclude_unset=True)  # Exclude fields not provided
#     if "password" in update_data:
#         update_data["password"] = hash_password(update_data["password"])  # Hash new password

#     # Update user in the database
#     await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
#     updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})

#     return UserResponse(**updated_user)

# async def delete_user(user_id: str):
#     user_collection = get_user_collection()

#     result = await user_collection.delete_one({"_id": ObjectId(user_id)})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {"message": "User deleted successfully"}

from fastapi import HTTPException
from models.user import UserCreate, UserResponse, UserUpdate
from config.mongo import get_user_collection
from datetime import datetime
import bcrypt

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check if the provided password matches the hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


async def create_user(user: UserCreate):
    user_collection = get_user_collection()

    # Check if the user_id, username, or email already exists
    existing_user = await user_collection.find_one({
        "$or": [
            {"user_id": user.user_id},
            {"username": user.username},
            {"email": user.email}
        ]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="User ID, Username, or Email already registered")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)  # Implement password hashing
    user_dict["created_at"] = datetime.utcnow()  # Set creation time

    # Insert the user into the database
    result = await user_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)

    return UserResponse(**user_dict, id=user_id)

async def get_user(user_id: int):
    user_collection = get_user_collection()

    user_data = await user_collection.find_one({"user_id": user_id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user_data)

async def update_user(user_id: int, user_update: UserUpdate):
    user_collection = get_user_collection()

    # Find the user by user_id
    user_data = await user_collection.find_one({"user_id": user_id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)  # Exclude fields not provided
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])  # Hash new password

    # Update user in the database
    await user_collection.update_one({"user_id": user_id}, {"$set": update_data})
    updated_user = await user_collection.find_one({"user_id": user_id})

    return UserResponse(**updated_user)

async def delete_user(user_id: int):
    user_collection = get_user_collection()

    result = await user_collection.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}