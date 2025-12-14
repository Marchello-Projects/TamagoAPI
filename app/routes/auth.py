import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from configs.configdb import get_db
from database.models import User
from schemas.user import UserCreate, UserResponse
from database.models import Pet

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth & Users"])

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

async def authenticate_user_db(
    username: str, 
    password: str, 
    db: AsyncSession 
):
    get_user = await db.execute(
        select(User).where(User.username == username)
    )
    user = get_user.scalar_one_or_none()

    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({'exp': int(expire.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('username')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    get_user = await db.execute(
        select(User)
        .options(selectinload(User.pets))
        .where(User.username == username)
    )

    user = get_user.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    
    return user

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    get_user = await db.execute(
        select(User).where(User.username == user_create.username)
    )

    existing_user = get_user.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already registered'
        )
    
    hashed_pw = hash_password(user_create.password)

    new_user = User(
        username=user_create.username,
        password_hash=hashed_pw
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    result = await db.execute(
        select(User)
        .where(User.id == new_user.id)
        .options(selectinload(User.pets))
    )
    
    user_with_pets = result.scalar_one()

    return user_with_pets

@router.post('/login')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user_db(
        form_data.username,
        form_data.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password'
        )
    
    access_token = create_access_token(
        data={'username': user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        'access_token': access_token,
        'token_type': 'bearer'
    }

@router.get('/me')
async def get_my_account(current_user: User = Depends(get_current_user)):
    return {
        'id': current_user.id,
        'username': current_user.username,
        'created_at': current_user.created_at,
        'pets': current_user.pets
    }

@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await db.delete(current_user)
    await db.commit()

    await db.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE pets_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE pet_actions_id_seq RESTART WITH 1"))
    await db.commit()

    return None