from typing import Annotated
from ..db import get_db
from ..models import Game, GameVersion, Manifest, Purchase, User
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

class GameService:
    @staticmethod
    def chunk_blob_name(game_name: str, version: str, idx: int) -> str:
        return f"{game_name}/{version}/chunks/{idx:05d}"
    

    def lastest_manifest_for_game(self, game_name: str, db: Annotated[Session, Depends(get_db)]):
        game = db.query(Game).filter(Game.name==game_name).first()
        if not game:
            return None, None, None
        
        gv = db.query(GameVersion).filter(GameVersion.game_id==game.game_id).order_by(GameVersion.version.desc()).first()
        if not gv:
            return None, None, None
        
        manifest = db.query(Manifest).filter(Manifest.version_id==gv.version_id).first()

        return game, gv, manifest
    

    def ensure_entitlement(self, user_id: int, game_id: int, db: Annotated[Session, Depends(get_db)]) -> bool:
        entitlement = db.query(Purchase).filter(Purchase.user_id==user_id, Purchase.game_id==game_id).first()

        if not entitlement:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own this game")
        
        return True
    

    def list_purchased_games(self, user_id: int, db: Annotated[Session, Depends(get_db)]):
        purchases = (
            db.query(Game, GameVersion)
            .join(Purchase, Purchase.game_id == Game.game_id)
            .outerjoin(GameVersion, GameVersion.game_id == Game.game_id)
            .filter(Purchase.user_id == user_id)
            .order_by(Game.name.asc(), GameVersion.created_at.desc())
            .all()
        )
        lastest_by_game = {}
        for game, version in purchases:
            if game.name not in lastest_by_game:
                lastest_by_game[game.name] = version.version if version else "unknown"
        
        return [{"name": n, "version": v} for n, v in lastest_by_game.items()]
    

    def build_download_payload(self, manifest_json: dict, sas_token: str):
        return {
            "manifest": manifest_json,
            "sas_token": sas_token,
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "blob_base_url": "BLOB_BASE_URL_PLACEHOLDER"}
    

    def build_refresh_payload(self, sas_token: str):
        return {
            "sas_token": sas_token,
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}
    

    def build_upload_init_payload(self, game_name: str, version: str, sas_token: str):
        return {
            "container": "CONTAINER_NAME_PLACEHOLDER",
            "blob_base_url": "BLOB_BASE_URL_PLACEHOLDER",
            "path_prefix": f"{game_name}/{version}/chunks/",
            "sas_token": sas_token, 
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        }
    
    
