import asyncio
from datetime import datetime, timezone
from configs.configdb import Base, async_engine
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from enum import Enum

class ActionType(str, Enum):
    FEED = 'feed'
    PLAY = 'play'
    SLEEP = 'sleep'

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    pets: Mapped[list['Pet']] = relationship(
        back_populates='owner',
        cascade='all, delete-orphan'
    )

class Pet(Base):
    __tablename__ = 'pets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    happiness: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    energy: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    owner: Mapped['User'] = relationship(back_populates='pets')
    actions: Mapped[list['PetActions']] = relationship(
        back_populates='pet',
        cascade='all, delete-orphan'
    )

class PetActions(Base):
    __tablename__ = 'pet_actions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_id: Mapped[int] = mapped_column(Integer, ForeignKey('pets.id'))
    action_type: Mapped[ActionType]= mapped_column(SQLEnum(ActionType), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    pet: Mapped['Pet'] = relationship(back_populates='actions')