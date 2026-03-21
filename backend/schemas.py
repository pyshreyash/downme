from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class UserAuthority(BaseModel):
    user_id: int
    role: str

class RefreshSASRequest(BaseModel):
    game_name: str

class UploadInitRequest(BaseModel):
    game_name: str
    version: str

class UploadCommitRequest(BaseModel):
    game_name: str
    version: str