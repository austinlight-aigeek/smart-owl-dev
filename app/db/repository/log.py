from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError

from app.core.config import settings
from app.db.models.log import Log
from app.db.models.user import User
from app.schemas.log import CreateLog


def create_new_log(log: CreateLog, db: ServiceResource):
    log = Log(**log.dict())
    log = log.__dict__
    table = db.Table(settings.DYNAMO_DB_TABLE)
    response = table.put_item(Item=log)
    print(response)
    return log


def retrieve_log(id: str, db: ServiceResource):
    try:
        table = db.Table(settings.DYNAMO_DB_TABLE)
        response = table.get_item(Key={"id": id})
        return response.get("Item", {})
    except ClientError as e:
        raise ValueError(e.response["Error"]["Message"])


def list_logs(db: ServiceResource):
    table = db.Table(settings.DYNAMO_DB_TABLE)
    response = table.scan()
    return response.get("Items", [])


def log_prompt(
    db: ServiceResource, user: User, model: str, prompt: str, cleaned_prompt: str, response: dict
) -> Log:
    """
    Create new log for a given Session, prompt, and response.
    """
    log_instance = CreateLog(
        user_id=user.id,
        user_email=user.email,
        project_name=user.project_name,
        openai_key_type=user.openai_key_type,
        is_success=True,
        gpt_request={
            "gpt_model": model,
            "gpt_request": prompt,
            "gpt_cleaned_request": cleaned_prompt,
            "is_cleaned": not (prompt == cleaned_prompt),
        },
        gpt_response=response,
    )
    log = create_new_log(log=log_instance, db=db)
    table = db.Table(settings.DYNAMO_DB_TABLE)
    table.put_item(Item=log)
