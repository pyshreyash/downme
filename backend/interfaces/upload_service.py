from typing import Annotated
import hashlib, json
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from backend.db import get_db
from backend.models import Game, GameVersion, Manifest
from backend.interfaces.blob_storage import BlobStorageService

class UploadService:
    def __init__(self, db: Session, blob_storage_service: BlobStorageService) -> None:
        self.db = db
        self.blob_storage_service = blob_storage_service

    def init_game(self, game_name: str, version: str, user_id: int) -> Game:
        game = self.db.query(Game).filter(Game.name==game_name).first()
        if game:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game aldready exists")
        
        new_game = Game(name=game_name, publisher_id=user_id)
        self.db.add(new_game)
        self.db.flush() # to get game_id before commit

        new_game_version = GameVersion(game_id=new_game.game_id, version=version)
        self.db.add(new_game_version)
        self.db.commit()
        self.db.refresh(new_game_version)
        self.db.refresh(new_game)

        self.blob_storage_service.create_upload_container(game_name)

        return new_game

    def ensure_commit_allowed(self, user_id: int, game_name: str, db: Annotated[Session, Depends(get_db)]) -> Game:
        game = db.query(Game).filter(Game.name==game_name).first()
        if not game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
        
        if game.publisher_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only publisher can commit")
        
        return game
    
    def build_manifest_from_blobs(self, container_client, game_name:str, version:str):
        prefix = f"{game_name}/{version}/chunks/"
        blobs = sorted(container_client.list_blobs(name_starts_with=prefix), key=lambda b: b.name)

        if not blobs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chunks found for this game version")
        
        chunks = []
        for idx, blob in enumerate(blobs):
            expected_blob_name = GameVersion.chunk_blob_name(game_name, version, idx)
            if blob.name != expected_blob_name:
                raise HTTPException(status_code=400, detail=f"Missing or out-of-order chunk near {expected_blob_name}")
            data = container_client.get_blob_client(blob.name).download_blob().readall()
            chunks.append(
                {
                    "id": f"{idx:05d}",
                    "path": blob.name,
                    "size": blob.size,
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        return {
            "game_id": game_name,
            "version": version,
            "chunk_size": 1024*1024, # 1MB
            "chunks": chunks}
    
    def upsert_manifest(self, db: Annotated[Session, Depends(get_db)], game_id: int, version: str, manifest_json: dict) -> None:
        gv = (
            db.query(GameVersion)
            .filter(GameVersion.game_id == game_id, GameVersion.version == version)
            .first()
        )
        if gv is None:
            gv = GameVersion(game_id=game_id, version=version)
            db.add(gv)
            db.commit()
            db.refresh(gv)

        existing = db.query(Manifest).filter(Manifest.version_id == gv.version_id).first()
        if existing:
            existing.manifest_json = json.dumps(manifest_json)
        else:
            db.add(Manifest(version_id=gv.version_id, manifest_json=json.dumps(manifest_json)))
        db.commit()