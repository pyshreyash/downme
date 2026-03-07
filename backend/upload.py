import io
import os
import zipfile
import secrets
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from schemas import UploadResponse

from db import SessionLocal
from models import Users, Games, Game_versions

router = APIRouter(prefix="/publisher", tags=["publisher-utils"])

# ----------------------------
# Hard-coded storage root (absolute)
# ----------------------------
STORAGE_ROOT = os.path.abspath("static/")
os.makedirs(STORAGE_ROOT, exist_ok=True)


# ----------------------------
# DB dependency
# ----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------
# Auth dependency (placeholder)
# Replace with your JWT-based "get_current_user" or "require_publisher" if you have it.
# For now it expects a username in some upstream dependency. Wire accordingly.
# ----------------------------
def get_current_user(db: Session = Depends(get_db)) -> Users:
    """
    Replace this stub with your real auth dependency that returns Users row
    for the current caller. For quick local testing you may temporarily fetch
    a fixed user, e.g. the first publisher in DB.
    """
    user = db.query(Users).filter(Users.role.in_(("publisher", "admin"))).first()
    if not user:
        raise HTTPException(status_code=401, detail="No publisher/admin user available. Wire real auth.")
    return user


# ----------------------------
# Helpers
# ----------------------------
def _version_dir(game_pk: int, version: str) -> str:
    """backend/static/content/<game_pk>/<version>/"""
    return os.path.abspath(os.path.join(STORAGE_ROOT, "content", str(game_pk), version))

def _safe_extract_zip(zip_bytes: bytes, dest_dir: str) -> None:
    """Extract ZIP with basic path traversal protection."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for member in z.infolist():
            norm = os.path.normpath(member.filename)
            # Block absolute or parent traversal
            if norm.startswith(("/", "\\")) or ".." in norm.split(os.sep):
                raise HTTPException(status_code=400, detail=f"Blocked unsafe ZIP entry: {member.filename}")

            abs_target = os.path.abspath(os.path.join(dest_dir, norm))
            if not abs_target.startswith(os.path.abspath(dest_dir) + os.sep):
                raise HTTPException(status_code=400, detail=f"Unsafe ZIP entry path: {member.filename}")

        z.extractall(dest_dir)

def _generate_unique_game_id(db: Session) -> int:
    """
    Generate a random 6-digit numeric game_id that does not collide in Games.game_id.
    (You can swap this with UUID or another scheme later.)
    """
    while True:
        gid = secrets.randbelow(900_000) + 100_000  # 100000..999999
        exists = db.query(Games).filter(Games.game_id == gid).first()
        if not exists:
            return gid


# ----------------------------
# Endpoint: create (if needed) + upload
# ----------------------------
@router.post("/upload", response_model=UploadResponse)
def upload_version(
    game_name: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),        # expects a .zip
    db: Session = Depends(get_db),
    publisher: str = Form(...),
):
    """
    Ultra-simple upload that:
      - Finds or creates a game by `game_name`
      - Generates a unique `Games.game_id` if creating
      - Verifies caller is allowed (publisher of the game or admin)
      - Rejects duplicate version for that game
      - Extracts the ZIP to backend/static/content/<Games.id>/<version>/
      - Inserts row in Game_versions
    """

    # 1) Find or create the game by name
    game = db.query(Games).filter(Games.game_name == game_name).first()

    if game is None:
        # Create a new game; generate unique game_id here
        new_game_id = _generate_unique_game_id(db)

        # IMPORTANT: your Games.publisher column is UNIQUE in your model.
        # That means one publisher username can appear only once in "games".
        # If you want multiple games per publisher, remove unique=True on Games.publisher.
        game = Games(
            game_id=new_game_id,
            game_name=game_name,
            publisher=publisher  # set the uploader as publisher
        )
        db.add(game)
        db.commit()
        db.refresh(game)


    # 2) Prevent duplicate version for this game
    dup = db.query(Game_versions).filter(
        Game_versions.game_id == game.game_id,
        Game_versions.version == version
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="This version already exists for the game")

    # 3) Extract the ZIP under backend/static/content/<game_pk>/<version>/
    target_dir = _version_dir(game.game_id, version)
    os.makedirs(target_dir, exist_ok=True)

    try:
        zip_bytes = file.file.read()  # For big builds, stream to disk instead
        _safe_extract_zip(zip_bytes, target_dir)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    # 4) Insert the version row
    gv = Game_versions(game_id=game.game_id, version=version)
    db.add(gv)
    db.commit()

    
    return UploadResponse(
            message="Upload & extraction complete",
            game_id=game.game_id,
            game_name=game.game_name,
            publisher=game.publisher,
            version=version,
            stored_at=target_dir
        )
