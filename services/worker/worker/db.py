from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from .config import settings

engine = create_engine(settings.database_url)


class Base(DeclarativeBase):
    pass


def session_scope():
    return Session(engine)
