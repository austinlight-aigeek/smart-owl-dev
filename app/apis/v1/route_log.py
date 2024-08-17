from fastapi import APIRouter

from app.schemas.log import ShowLog

router = APIRouter()

@router.get("/log/{id}", response_mode=ShowLog)
def get_log():
    print("get_log()")


@router.get("/logs", response_model=list[ShowLog])
def get_all_logs():
    print("get_all_logs()")


    