from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
import json

from backend.interfaces.blob_storage import BlobStorageService
from backend.interfaces.game_service import GameService
from backend.utils import get_user_authority
from backend.db import get_db
from backend.schemas import UserAuthority, RefreshSASRequest


router = APIRouter(prefix='', tags=['sas'])
blob_storage_service = BlobStorageService()
game_service = GameService()

@router.post('/refresh-sas')
def refresh_sas(payload: RefreshSASRequest, current_user: UserAuthority = Depends(get_user_authority), db: Session = Depends(get_db)):
    game, gv, manifest = game_service.lastest_manifest_for_game(payload.game_name, db)
    if not game or not gv or not manifest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game/version not found")
    
    game_service.ensure_entitlement(current_user.user_id, game.game_id, db)
    manifest_json = json.loads(manifest.manifest_json)
    sas = (
        blob_storage_service.generate_download_sas(manifest_json["chunks"][0]["path"])
        if manifest_json["chunks"] else ""
    )

    return game_service.build_refresh_payload(sas)
