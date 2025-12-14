from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.pet import PetResponse, PetCreate
from configs.configdb import get_db
from routes.auth import get_current_user
from database.models import Pet, User

router = APIRouter(prefix='/pets', tags=['Pets & Actions'])

@router.post('/create', response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_create: PetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    get_pet = await db.execute(
        select(Pet).where(
            Pet.name == pet_create.name,
            Pet.owner_id == current_user.id
        )
    )
    
    existing_pet = get_pet.scalar_one_or_none()
    if existing_pet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Pet already exists'
        )
    
    new_pet = Pet(
        name=pet_create.name,
        owner_id=current_user.id
    )

    db.add(new_pet)
    await db.commit()
    await db.refresh(new_pet)

    return new_pet