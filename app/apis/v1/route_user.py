from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import ShowUser, UserCreate, UserUpdate

router = APIRouter()

@router.post("/new_user", response_model=ShowUser, status_code=status.HTTP_201_CREATED)
def create_user():
    print("create_user")

@router.get("/user/{id}", response_model=ShowUser)
def get_user():
    print("get_user")

@router.get("/users", response_model=list[ShowUser])
def get_all_users():
    print("get_all_users")

@router.put("/update_user/{email}", response_model=ShowUser, status_code=status.HTTP_200_OK)
def update_user():
    print("update_user")