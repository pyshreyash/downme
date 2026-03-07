from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UploadResponse(BaseModel):
    message: str
    game_id: int
    game_name: str
    publisher: str
    version: str
    stored_at: str
