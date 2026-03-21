from fastapi import FastAPI, HTTPException, Depends, status
import models
from db import SessionLocal, engine
from typing import Annotated
from sqlalchemy.orm import Session

from .services import auth, publisher, sas_refresh, user


app = FastAPI()
app.include_router(auth.router)
app.include_router(publisher.router)
app.include_router(sas_refresh.router)
app.include_router(user.router)

# Check if required tables exists in database else create new
models.Base.metadata.create_all(bind=engine)

@app.get("/hello/{user_name}", status_code=status.HTTP_200_OK)
def hello_world(user_name: str):
    return {"message": f"Hello {user_name}!"}
    