from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends

from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session

from backend.models import User
from backend.schemas import LoginResponse, UserAuthority
from backend.db import get_db




bcrypt_context = CryptContext(schemes=['argon2'], deprecated='auto')


class JWTAuthManager:
    def __init__(self, secret_key: str, algorithm: str, session_timeout: timedelta, db: Session):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.session_timeout = session_timeout
        self.db = db

    def create_JWT(self, user_id: int):
        payload = {'id': user_id, 'ttl': (self.session_timeout+datetime.now()).isoformat()}
        payload.update({})
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    
    def token_to_user(self, token: str) -> UserAuthority:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get('id')
            if datetime.fromisoformat(payload['ttl']) < datetime.now():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token has expired')
            
            user = self.db.query(User).filter(User.user_id==user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Fatal error: user not found')
            
            return UserAuthority(user_id=user.user_id, role=user.role)
        
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')


class AuthManager:
    def __init__(self, jwt_manager: JWTAuthManager, db: Session):
        self.jwt_manager = jwt_manager
        self.db = db

    def login(self, username: str, password:str) -> LoginResponse:
        user = self.db.query(User).filter(User.username==username).first()
        if not user or not bcrypt_context.verify(password, str(user.password)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credientials')
        
        access_token = self.jwt_manager.create_JWT(user.user_id)
        return LoginResponse(access_token=access_token, token_type='bearer')
    
    def register(self, username: str, password: str) -> LoginResponse:
        if self.db.query(User).filter(User.username==username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username already exists')
        
        new_user = User(username=username, password=bcrypt_context.hash(password))
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        access_token = self.jwt_manager.create_JWT(new_user.user_id)

        return LoginResponse(access_token=access_token, token_type='bearer')
        