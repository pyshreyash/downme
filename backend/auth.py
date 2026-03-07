from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from db import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from schemas import User, Token
from models import Users
from datetime import timedelta, datetime, timezone

router = APIRouter(prefix='/auth', tags=['auth'])

SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = 'HS256'
SESSION_TIMEOUT = 30

bcrypt_context = CryptContext(schemes=['argon2'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: User, db: db_dependency):
    new_user = Users(username=user.username, password=bcrypt_context.hash(user.password))
    db.add(new_user)
    db.commit()

@router.post("/token", response_model=Token)
async def get_access_token(user_in: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(user_in.username, user_in.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unable to validate for provided username and password')
    
    token = create_JWT(user.username, user.id, timedelta(minutes=SESSION_TIMEOUT))

    return {'access_token': token, 'token_type': 'bearer'}

def authenticate_user(username: str, password:str, db):
    user = db.query(Users).filter(Users.username==username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    
    return user

def create_JWT(username: str, user_id: int, timeout: timedelta):
    payload = {'username': username, 'id': user_id, 'ttl': (timeout+datetime.now()).isoformat()}
    payload.update({})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def token_to_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('username')
        user_id: int = payload.get('id')
        ttl: datetime = datetime.fromisoformat(payload.get('ttl'))

        if username is None or user_id is None or (ttl < datetime.now()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not authenticate, pls login again')
        
        return {'username': username, 'id': user_id}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid access request')