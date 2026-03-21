from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, UTC

from db import Base

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user") #user, admin, publisher

class Game(Base):
    __tablename__ = "games"
    game_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    publisher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
 

class GameVersion(Base):
    __tablename__ = "game_versions"
    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.game_id"), index=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    __table_args__ = (UniqueConstraint('game_id', 'version', name='uq_game_version'),)

    game = relationship("Game")

class Purchase(Base):
    __tablename__ = "purchases"
    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.game_id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_purchase"),)


class Manifest(Base):
    __tablename__ = "manifests"
    manifest_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_versions.version_id"), nullable=False, unique=True)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)