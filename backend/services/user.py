from fastapi import APIRouter, Depends, HTTPException, status
import dotenv, os, json
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import Annotated

from backend.interfaces.blob_storage import BlobStorageService
from backend.utils import get_user_authority
from backend.interfaces.game_service import GameService
from backend.schemas import UserAuthority
from backend.db import get_db


router = APIRouter(prefix='/users', tags=['users'])
game_service = GameService()
blob_storage_service = BlobStorageService()


@router.get('/games')
def list_games(current_user: UserAuthority = Depends(get_user_authority), db: Session = Depends(get_db)):
    if current_user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can list their games")
    
    return game_service.list_purchased_games(current_user.user_id, db)


@router.get('/download/{game_name}')
def download_game(game_name: str, current_user: UserAuthority = Depends(get_user_authority), db: Session = Depends(get_db)):
    if current_user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can download games")
    
    game, gv, manifest = game_service.lastest_manifest_for_game(game_name, db)
    if not game or not gv or not manifest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game/version not found")
    
    game_service.ensure_entitlement(current_user.user_id, game.game_id, db) # Implicit 403 if user does not own the game
    
    manifest_json = json.loads(manifest.manifest_json)
    container_name = blob_storage_service.game_container_name(game_name)
    
    sas = blob_storage_service.generate_download_sas(game_name)
    
    return game_service.build_download_payload(manifest_json, sas, container_name)