from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from src.config import get_settings

setting = get_settings()

# =============================================
engine = create_engine(
    setting.database_url,
    echo=setting.debug,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # the sqlite3 driver will not set PRAGMA foreign_keys
    # if autocommit=False; set to True temporarily
    ac = dbapi_connection.autocommit
    dbapi_connection.autocommit = True

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

    # restore previous autocommit setting
    dbapi_connection.autocommit = ac
# =============================================

# =============================================
def get_db():
    # automatically close the connection
    with SessionLocal() as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
# =============================================
