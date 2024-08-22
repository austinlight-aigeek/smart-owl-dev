from sqlalchemy import ARRAY, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    is_superuser = Column(Boolean(), default=False)
    is_active = Column(Boolean(), default=True)
    project_name = Column(String, nullable=False)
    team_name = Column(String, nullable=False)
    contact_email = Column(String, default="")
    account_type = Column(String, default="dev")
    openai_key_type = Column(String, default="dev")
    openai_key_name = Column(String, nullable=False)
    quota = Column(Integer, default=2000)
    usage = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    available_models = Column(ARRAY(String), nullable=False)

    def __init__(self, **data):
        super().__init__(updated_at=func.now(), **data)
