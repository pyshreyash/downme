from fastapi import APIRouter

from ..interfaces.auth import AuthManager
from ..schemas import LoginResponse, LoginRequest
from ..utils import jwt_handler


auth_manager = AuthManager(jwt_handler)

router = APIRouter(prefix='/auth', tags=['authentication'])

@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest):
    return auth_manager.login(payload.username, payload.password)

@router.post('/register', response_model=LoginResponse)
def register(payload: LoginRequest):
    return auth_manager.register(payload.username, payload.password)
