from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PetCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description='Name of the pet (3–50 characters)',
        example='Fluffy'
    )

class PetResponse(BaseModel):
    id: int = Field(
        ..., 
        description='Unique identifier of the pet',
        example=1
    )
    name: str = Field(
        ..., 
        description='Name of the pet',
        example='Fluffy'
    )
    owner_id: int = Field(
        ..., 
        description='ID of the user who owns the pet',
        example=1
    )
    hunger: int = Field(
        default=100, ge=0, le=100,
        description='Fullness level of the pet (100 = full, 0 = starving)',
        example=100
    )
    energy: int = Field(
        default=100, ge=0, le=100,
        description='Energy level of the pet (100 = fully energized, 0 = exhausted)',
        example=80
    )
    happiness: int = Field(
        default=100, ge=0, le=100,
        description='Happiness level of the pet (100 = very happy, 0 = very sad)',
        example=90
    )
    last_updated: datetime = Field(
        ..., description='The timestamp of the last update of the pet\'s stats',
        example='2025-12-13T12:30:00Z'
    )

    class Config:
        orm_mode = True 

class PetUpdate(BaseModel):
    name: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50, 
        description='Pet name',
        example='Fluffy'
    )

    class Config:
        orm_mode = True