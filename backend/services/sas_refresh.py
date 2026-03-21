from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
import json

from ..interfaces.blob_storage import BlobStorageService
from ..interfaces.game_service import GameService
from ..utils import jwt_handler
from ..db import get_db
from ..schemas import UserAuthority, RefreshSASRequest


router = APIRouter(prefix='', tags=['sas'])
blob_storage_service = BlobStorageService()
game_service = GameService()

@router.post('/refresh-sas')
def refresh_sas(payload: RefreshSASRequest, current_user: UserAuthority = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
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
