from fastapi import FastAPI, HTTPException, Depends, status
import models
from db import SessionLocal, engine
from typing import Annotated
from sqlalchemy.orm import Session
import auth
import upload

app = FastAPI()
app.include_router(auth.router)
app.include_router(upload.router)
# Check if required tables exists in database else create new
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.token_to_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"user": user}