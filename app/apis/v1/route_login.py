from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.schemas.token import Token


router = APIRouter()


@router.post("/token", response_model=Token)
def login_for_access_token():
    print("login_for_acccess_token")


