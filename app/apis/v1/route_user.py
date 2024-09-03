from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.v1.route_login import get_current_user
from app.db.models.user import User
from app.db.repository.user import (
    create_new_user,
    is_super_user,
    list_users,
    retrieve_user,
    update_user_based_on_email,
)
from app.db.session import get_db
from app.schemas.user import ShowUser, UserCreate, UserUpdate

router = APIRouter()


@router.post("/new_user", response_model=ShowUser, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_super_user(current_user):
        raise HTTPException(detail="Not a super user!", status_code=status.HTTP_401_UNAUTHORIZED)

    user = create_new_user(user=user, db=db)
    return user


@router.get("/user/{id}", response_model=ShowUser)
def get_user(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_super_user(current_user):
        raise HTTPException(
            detail="Not a super user!", status_code=status.HTTP_401_UNAUTHORIZED
        )

    user = retrieve_user(id=id, db=db)
    if not user:
        raise HTTPException(
            detail=f"user with ID {id} does not exist.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return user


@router.get("/users", response_model=list[ShowUser])
def get_all_users(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if not is_super_user(current_user):
        raise HTTPException(
            detail="Not a super user!", status_code=status.HTTP_401_UNAUTHORIZED
        )

    users = list_users(db=db)
    return users


@router.put(
    "/update_user/{email}", response_model=ShowUser, status_code=status.HTTP_200_OK
)
def update_user(
    email: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if not is_super_user(current_user):
        raise HTTPException(
            detail="Not a super user!", status_code=status.HTTP_403_FORBIDDEN
        )

    user = update_user_based_on_email(email=email, user_update=user_update, db=db)
    if not user:
        raise HTTPException(
            detail=f"user with email '{email}' does not exist.", status_code=404
        )
    return user


# @router.get("/increase_usage", response_model=ShowUser)
# def get_all_users(db: Session = Depends(get_db), current_user: User=Depends(get_current_user)):
#     increase_usage(current_user, db)
#     return current_user
