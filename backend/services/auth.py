from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from backend.interfaces.auth import AuthManager
from backend.schemas import LoginResponse, LoginRequest
from backend.utils import jwt_handler, get_auth_manager
from backend.db import get_db


router = APIRouter(prefix='/auth', tags=['authentication'])

@router.post('/login', response_model=LoginResponse)
def login(payload: OAuth2PasswordRequestForm = Depends(), auth_manager: AuthManager = Depends(get_auth_manager)):
    return auth_manager.login(payload.username, payload.password)

@router.post('/register', response_model=LoginResponse)
def register(payload: LoginRequest, auth_manager: AuthManager = Depends(get_auth_manager)):
    return auth_manager.register(payload.username, payload.password)
