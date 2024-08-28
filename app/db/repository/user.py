from datetime import datetime

from sqlalchemy.orm import Session

from app.core.hashing import Hasher
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_new_user(user: UserCreate, db: Session):
    user = User(
        email=user.email,
        password=Hasher.get_password_hash(user.password),
        is_active=True,
        is_superuser=user.is_super_user,
        project_name=user.project_name,
        team_name=user.team_name,
        contact_email=user.contact_email,
        account_type=user.account_type,
        openai_key_type=user.openai_key_type,
        openai_key_name=user.openai_key_name,
        quota=user.quota,
        usage=0,
        # available_models=user.available_models,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def retrieve_user(id: str, db: Session):
    try:
        user = db.query(User).filter(User.id == id).first()
        return user
    except Exception as e:
        raise ValueError(e.response["Error"]["Message"])


def list_users(db: Session):
    try:
        user = db.query(User).all()
        return user
    except Exception as e:
        raise ValueError(e.response["Error"]["Message"])


def reset_usage(user: User, db: Session):
    date_now = datetime.now()
    date_last = user.updated_at

    if date_now.month != date_last.month:
        user.usage = 0
        db.commit()
        db.refresh(user)


def increase_usage(user: User, db: Session):
    # user = db.query(User).filter(User.id == id).first()
    if user.usage < user.quota:
        user.usage += 1
        db.commit()
        db.refresh(user)
        return True
    else:
        return False


def is_super_user(user: User):
    return user.is_superuser


def update_user_based_on_email(email: str, user_update: UserUpdate, db: Session):
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password = (
                Hasher.get_password_hash(user_update.password)
                if user_update.password
                else user.password
            )
            user.is_active = (
                user_update.is_active if user_update.is_active else user.is_active
            )
            user.project_name = (
                user_update.project_name
                if user_update.project_name
                else user.project_name
            )
            user.team_name = (
                user_update.team_name if user_update.team_name else user.team_name
            )
            user.contact_email = (
                user_update.contact_email
                if user_update.contact_email
                else user.contact_email
            )
            user.account_type = (
                user_update.account_type
                if user_update.account_type
                else user.account_type
            )
            user.openai_key_type = (
                user_update.openai_key_type
                if user_update.openai_key_type
                else user.openai_key_type
            )
            user.openai_key_name = (
                user_update.openai_key_name
                if user_update.openai_key_name
                else user.openai_key_name
            )
            user.quota = user_update.quota if user_update.quota else user.quota
            user.is_superuser = (
                user_update.is_superuser
                if user_update.is_superuser
                else user.is_superuser
            )
            user.available_models = (
                user_update.available_models
                if user_update.available_models
                else user.available_models
            )
            db.commit()
            db.refresh(user)
            return user
        return user
    except Exception as e:
        raise ValueError(e.response["Error"]["Message"])
