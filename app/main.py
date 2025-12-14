from contextlib import asynccontextmanager

from configs.configdb import async_engine
from database.models import Base
from fastapi import FastAPI
from middleware.pet_decay import PetDecayMiddleware
from routes.auth import router as auth_router
from routes.pets import router as pets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(
    title="TamagoAPI",
    description="Tamagotchi API - A fun API to manage virtual pets. Users can create pets, check their state (hunger, happiness, energy), and interact with them by feeding, playing, or putting them to sleep. JWT authentication secures user actions.",
    # year.month.day.major.minor
    version="25.12.14.1.0",
    contact={
        "name": "Marchello",
        "url": "https://github.com/Marchello-Projects",
        "email": "paskalovmarkus@gmail.com",
    },
)

app.add_middleware(PetDecayMiddleware)
app.include_router(auth_router)
app.include_router(pets_router)
