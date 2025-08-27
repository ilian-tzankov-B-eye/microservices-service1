from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import os
from typing import List, Optional
import uvicorn

app = FastAPI(title="User Management Service", version="1.0.0")

# Data models
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int

class ProcessedUser(BaseModel):
    user: User
    processed_data: dict
    service2_status: str

# In-memory storage for users
users_db = []
user_id_counter = 1

# Service2 configuration
SERVICE2_URL = os.getenv("SERVICE2_URL", "http://localhost:8001")
SERVICE2_TIMEOUT = int(os.getenv("SERVICE2_TIMEOUT", "10"))

@app.get("/")
async def root():
    return {"message": "User Management Service is running", "service": "service1"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service1"}

@app.post("/users", response_model=User)
async def create_user(user: User):
    global user_id_counter
    user.id = user_id_counter
    user_id_counter += 1
    users_db.append(user)
    
    # Send user data to service2 for processing
    try:
        async with httpx.AsyncClient(timeout=SERVICE2_TIMEOUT) as client:
            response = await client.post(
                f"{SERVICE2_URL}/process-user",
                json=user.dict()
            )
            if response.status_code == 200:
                print(f"User {user.name} processed by service2")
    except Exception as e:
        print(f"Failed to communicate with service2: {e}")
    
    return user

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/{user_id}/processed", response_model=ProcessedUser)
async def get_processed_user(user_id: int):
    # Find user in local database
    user = None
    for u in users_db:
        if u.id == user_id:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get processed data from service2
    try:
        async with httpx.AsyncClient(timeout=SERVICE2_TIMEOUT) as client:
            response = await client.get(f"{SERVICE2_URL}/processed-users/{user_id}")
            if response.status_code == 200:
                processed_data = response.json()
                return ProcessedUser(
                    user=user,
                    processed_data=processed_data.get("processed_data", {}),
                    service2_status="success"
                )
            else:
                return ProcessedUser(
                    user=user,
                    processed_data={},
                    service2_status="not_found_in_service2"
                )
    except Exception as e:
        return ProcessedUser(
            user=user,
            processed_data={},
            service2_status=f"error: {str(e)}"
        )

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    global users_db
    for i, user in enumerate(users_db):
        if user.id == user_id:
            deleted_user = users_db.pop(i)
            
            # Notify service2 about user deletion
            try:
                async with httpx.AsyncClient(timeout=SERVICE2_TIMEOUT) as client:
                    await client.delete(f"{SERVICE2_URL}/processed-users/{user_id}")
            except Exception as e:
                print(f"Failed to notify service2 about user deletion: {e}")
            
            return {"message": f"User {deleted_user.name} deleted successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
