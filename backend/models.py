from sqlalchemy import Column, Integer, String
from db import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user") #user, admin, publisher

class Games(Base):
    __tablename__ = "games"
    game_id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String, unique=True)
    publisher = Column(String)
 

class Game_versions(Base):
    __tablename__ = "game_versions"
    id = Column(Integer, primary_key=True)
    game_id=Column(Integer, index=True)
    version = Column(String)