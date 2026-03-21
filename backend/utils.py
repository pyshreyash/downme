from datetime import timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from backend.interfaces.auth import JWTAuthManager, AuthManager
from backend.config import settings
from backend.db import get_db
from backend.schemas import UserAuthority
from backend.interfaces.blob_storage import BlobStorageService
from backend.interfaces.game_service import GameService
from backend.interfaces.upload_service import UploadService

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/login')

def jwt_handler(db: Session = Depends(get_db)):
    return JWTAuthManager(settings.secret_key, settings.algorithm, settings.session_timeout, db)


def get_auth_manager(db: Session = Depends(get_db)):
    return AuthManager(jwt_handler(db), db)


def get_user_authority(token: str = Depends(oauth2_bearer), jwt_manager: JWTAuthManager = Depends(jwt_handler)) -> UserAuthority:
    return jwt_manager.token_to_user(token)

blob_storage_service = BlobStorageService()

def get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    return UploadService(db, blob_storage_service)


game_service = GameService()