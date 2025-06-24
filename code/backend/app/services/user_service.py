from sqlalchemy.orm import Session
from app.models.user import UserCreate
from app.models import user_db
from app.core.security import get_password_hash

def get_user_by_username(db: Session, username: str) -> user_db.User | None:
    """
    通过用户名从数据库中获取用户

    :param db: 数据库会话
    :param username: 用户名
    :return: 用户对象或None
    """
    return db.query(user_db.User).filter(user_db.User.username == username).first()

def create_user(db: Session, user: UserCreate) -> user_db.User:
    """
    在数据库中创建新用户

    :param db: 数据库会话
    :param user: 用户创建数据模型
    :return: 创建的用户对象
    """
    hashed_password = get_password_hash(user.password)
    db_user = user_db.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 