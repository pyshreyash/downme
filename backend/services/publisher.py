from fastapi import Depends, HTTPException, status,  APIRouter
from sqlalchemy.orm import Session

from backend.utils import get_user_authority, get_upload_service, blob_storage_service, game_service
from backend.schemas import UploadInitRequest, UploadCommitRequest, UserAuthority, RefreshSASRequest
from backend.db import get_db
from backend.interfaces.upload_service import UploadService

router = APIRouter(prefix='/publisher', tags=['game-publisher'])

@router.post('/upload/init', status_code=status.HTTP_201_CREATED)
def upload_init(payload: UploadInitRequest, current_user: UserAuthority = Depends(get_user_authority), db: Session = Depends(get_db),
                upload_service: UploadService = Depends(get_upload_service)):
    if current_user.role != "publisher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only publisher can upload")
    
    created_game = upload_service.init_game(payload.game_name, payload.version, current_user.user_id)
    container_name, sas = blob_storage_service.generate_upload_sas(created_game.name)

    return game_service.build_upload_payload(container_name, sas)

@router.post('/upload/refresh-sas', status_code=status.HTTP_200_OK)
def refresh_upload_sas(payload: RefreshSASRequest, current_user: UserAuthority = Depends(get_user_authority), 
                       db: Session = Depends(get_db),
                       upload_service: UploadService = Depends(get_upload_service)):
    
    if current_user.role != "publisher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only publisher can upload")

    container_name, sas = blob_storage_service.generate_upload_sas(payload.game_name)

    return game_service.build_upload_payload(container_name, sas)

# @router.post('/upload/commit')
# def upload_commit(payload: UploadCommitRequest, current_user = Depends(jwt_handler.token_to_user), db: Session = Depends(get_db)):
#     game = upload_service.ensure_commit_allowed(current_user.user_id, payload.game_name, db)
#     client = blob_storage_service.get_blob_service_client().get_container_client("AZURE CONTAINER PLACEHOLDER")
#     manifest_json = upload_service.build_manifest_from_blobs(client, payload.game_name, payload.version)
#     upload_service.upsert_manifest(db, game.game_id, payload.version, manifest_json)

#     return {"message": "Game uploaded Successfully!!"}