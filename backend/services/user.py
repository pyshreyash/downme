from fastapi import APIRouter, Depends, HTTPException, status
import dotenv, os, json
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import Annotated

from ..interfaces.blob_storage import BlobStorageService
from ..utils import jwt_handler
from ..interfaces.game_service import GameService
from ..schemas import UserAuthority
from ..db import get_db


dotenv.load_dotenv()

secret_key: str = os.environ["SECRET_KEY"]
algorithm: str = os.environ["ALGORITHM"]
session_timeout: timedelta = timedelta(minutes=int(os.environ["SESSION_TIMEOUT"]))

router = APIRouter(prefix='/users', tags=['users'])
game_service = GameService()
blob_storage_service = BlobStorageService()


@router.get('/games')
def list_games(current_user: UserAuthority = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
    if current_user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can list their games")
    
    return game_service.list_purchased_games(current_user.user_id, db)


@router.get('/download/{game_name}')
def download_game(game_name: str, current_user: UserAuthority = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
    if current_user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can download games")
    
    game, gv, manifest = game_service.lastest_manifest_for_game(game_name, db)
    if not game or not gv or not manifest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game/version not found")
    
    game_service.ensure_entitlement(current_user.user_id, game.game_id, db)
    
    manifest_json = json.loads(manifest.manifest_json)
    sas = (
        blob_storage_service.generate_download_sas(manifest_json["chunks"][0]["path"])
        if manifest_json["chunks"] else ""
    )
    
    return game_service.build_download_payload(manifest_json, sas)