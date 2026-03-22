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

    def ensure_commit_allowed(self, user_id: int, game_name: str) -> Game:
        game = self.db.query(Game).filter(Game.name==game_name).first()
        if not game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
        
        if game.publisher_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only publisher can commit")
        
        return game
    
    def build_manifest_from_blobs(self, container_client, game_name:str, version:str, auto_chunk: bool = True):
        if auto_chunk:
            prefix = f"{game_name}/{version}/"
        else:
            raise NotImplementedError("Manual chunking flow is not implemented yet")
        
        blob = next(container_client.list_blobs(name_starts_with=prefix), None)
        

        if not blob:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data found, please reupload your game")
        
        return {
            "prefix": prefix,
            "size": blob.size}
    

    def upsert_manifest(self, game_id: int, version: str, manifest_json: dict) -> None:
        gv = (
            self.db.query(GameVersion)
            .filter(GameVersion.game_id == game_id, GameVersion.version == version)
            .first()
        )
        if gv is None:
            gv = GameVersion(game_id=game_id, version=version)
            self.db.add(gv)
            self.db.commit()
            self.db.refresh(gv)

        existing = self.db.query(Manifest).filter(Manifest.game_id == game_id, Manifest.version_id == gv.version_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="This version already exists, please update the version and try again")
        else:
            self.db.add(Manifest(game_id=game_id, version_id=gv.version_id, manifest_json=json.dumps(manifest_json)))
        self.db.commit()