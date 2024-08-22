from boto3.resources.base import ServiceResource
from fastapi import APIRouter, Depends, HTTPException, status

from app.apis.v1.route_login import get_current_user
from app.db.dynamo_db import initialize_db
from app.db.models.user import User
from app.db.repository.log import list_logs, retrieve_log
from app.db.repository.user import is_super_user
from app.schemas.log import ShowLog

router = APIRouter()


@router.get("/log/{id}", response_model=ShowLog)
def get_log(
    id: str,
    db: ServiceResource = Depends(initialize_db),
    current_user: User = Depends(get_current_user),
):
    if not is_super_user(current_user):
        raise HTTPException(detail="Not a super user!", status_code=status.HTTP_401_UNAUTHORIZED)

    log = retrieve_log(id=id, db=db)
    if not log:
        raise HTTPException(
            detail=f"log with ID {id} does not exist.", status_code=status.HTTP_404_NOT_FOUND
        )
    return log


@router.get("/logs", response_model=list[ShowLog])
def get_all_logs(
    db: ServiceResource = Depends(initialize_db), current_user: User = Depends(get_current_user)
):
    if not is_super_user(current_user):
        raise HTTPException(detail="Not a super user!", status_code=status.HTTP_401_UNAUTHORIZED)

    logs = list_logs(db=db)
    return logs
