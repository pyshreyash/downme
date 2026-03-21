from fastapi import Depends, HTTPException, status,  APIRouter
from sqlalchemy.orm import Session

from ..interfaces.upload_service import UploadService
from ..interfaces.blob_storage import BlobStorageService
from ..interfaces.game_service import GameService
from ..utils import jwt_handler
from ..schemas import UploadInitRequest, UploadCommitRequest
from ..db import get_db

router = APIRouter(prefix='/publisher', tags=['game-publisher'])

upload_service = UploadService()
blob_storage_service = BlobStorageService()
game_service = GameService()

@router.post('/upload/init')
def upload_init(payload: UploadInitRequest, current_user = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
    upload_service.ensure_publisher(current_user.user_id, payload.game_name, db)
    sas = blob_storage_service.generate_upload_sas(
        game_service.chunk_blob_name(payload.game_name, payload.version, 1)
    )

    return game_service.build_upload_init_payload(payload.game_name, payload.version, sas)

@router.post('/upload/commit')
def upload_commit(payload: UploadCommitRequest, current_user = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
    game = upload_service.ensure_commit_allowed(current_user.user_id, payload.game_name, db)
    client = blob_storage_service.get_blob_service_client().get_container_client("AZURE CONTAINER PLACEHOLDER")
    manifest_json = upload_service.build_manifest_from_blobs(client, payload.game_name, payload.version)
    upload_service.upsert_manifest(db, game.game_id, payload.version, manifest_json)

    return {"message": "Game uploaded Successfully!!"}