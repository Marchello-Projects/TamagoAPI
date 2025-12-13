from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

from app.schemas.pet import PetResponse  

class UserCreate(BaseModel):
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description='Username',
        example='Alice'
    )
    password: str = Field(
        ..., 
        min_length=4, 
        max_length=255, 
        description='Password',
        example='MySecret123'
    )

class UserResponse(BaseModel):
    id: int = Field(
        ..., 
        description='Unique identifier of the user',
        example=1
    )
    username: str = Field(
        ..., 
        description='Username of the user',
        example='Alice'
    )
    created_at: datetime = Field(
        ..., 
        description='Account creation timestamp',
        example='2025-12-13T12:00:00Z'
    )
    pets: List[PetResponse] = Field(
        ..., 
        description='List of user\'s pets'
    )

    class Config:
        from_attributes = True  