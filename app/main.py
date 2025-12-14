from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.pets import router as pets_router
from database.models import Base
from configs.configdb import async_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()

app = FastAPI(
    title='TamagoAPI',
    description='Tamagotchi API - A fun API to manage virtual pets. Users can create pets, check their state (hunger, happiness, energy), and interact with them by feeding, playing, or putting them to sleep. JWT authentication secures user actions.',
    contact={
        "name": "Marchello",
        "url": "https://github.com/Marchello-Projects",
        "email": "paskalovmarkus@gmail.com",
    }
)

app.include_router(auth_router)
app.include_router(pets_router)