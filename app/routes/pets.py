from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from schemas.pet import PetResponse, PetCreate, PetUpdate, PetActionCreate, PetActionResponse
from configs.configdb import get_db
from routes.auth import get_current_user
from database.models import Pet, User, PetActions, ActionType

router = APIRouter(prefix='/pets', tags=['Pets & Actions'])

def check_not_pet(pet):
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pet not found or access denied'
        )
    
async def get_pet_from_db(db, pet_id: int, user_id: int):
    get_pet = await db.execute(
        select(Pet).where(
            Pet.id == pet_id,
            Pet.owner_id == user_id
        )
    )
    
    data = get_pet.scalar_one_or_none()

    return data

async def changing_pet_stats(pet, db, type_stats: str):
    check_not_pet(pet)

    if type_stats not in ['hunger', 'energy', 'happiness']:
        raise ValueError('Invalid stat type')

    current_value = getattr(pet, type_stats)
    setattr(pet, type_stats, min(current_value + 30, 100))

    pet.last_updated = datetime.now(timezone.utc)

    mapping = {
        'hunger': ActionType.FEED, 
        'energy': ActionType.PLAY, 
        'happiness': ActionType.SLEEP
    }

    new_action = PetActions(
        pet_id=pet.id,
        action_type=mapping[type_stats],
    )

    db.add(new_action)
    await db.commit()
    await db.refresh(pet)
    await db.refresh(new_action)

    return pet


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

@router.get('/{pet_id}', response_model=PetResponse)
async def get_pet(
    pet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = await get_pet_from_db(db, pet_id, current_user.id)

    check_not_pet(pet)

    return pet

@router.patch('/{pet_id}', response_model=PetResponse)
async def update_pet(
    pet_id: int,
    pet_update: PetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = await get_pet_from_db(db, pet_id, current_user.id)

    check_not_pet(pet)

    if pet_update.name is not None:
        pet.name = pet_update.name

    await db.commit()
    await db.refresh(pet)

    return pet

@router.delete('/{pet_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(
    pet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = await get_pet_from_db(db, pet_id, current_user.id)

    check_not_pet(pet)
    
    await db.delete(pet)
    await db.commit()

    await db.execute(text("ALTER SEQUENCE pets_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE pet_actions_id_seq RESTART WITH 1"))
    await db.commit()

    return None

@router.patch('/{pet_id}/action', response_model=PetResponse)
async def action_pet(
    pet_id: int,
    action: PetActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = await get_pet_from_db(db, pet_id, current_user.id)
    check_not_pet(pet)
    return await changing_pet_stats(pet, db, action.type_stats)

@router.get('/pets/{pet_id}/actions_history', response_model=list[PetActionResponse])
async def get_actions_history(
    pet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = await get_pet_from_db(db, pet_id, current_user.id)
    check_not_pet(pet)

    result = await db.execute(
        select(PetActions)
        .where(PetActions.pet_id == pet_id)
        .order_by(PetActions.timestamp.desc())
    )

    actions = result.scalars().all()
    return actions