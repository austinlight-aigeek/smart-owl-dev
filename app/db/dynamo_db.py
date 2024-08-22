from os import getenv

import boto3
from boto3.resources.base import ServiceResource

from app.core.config import settings


def initialize_db() -> ServiceResource:
    if getenv("RUN_LOCALLY") and getenv("DYNAMO_DB_ENDPOINT"):
        ddb = boto3.resource(
            "dynamodb", region_name=settings.AWS_REGION, endpoint_url=settings.DYNAMO_DB_ENDPOINT
        )
    else:
        ddb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

    return ddb
