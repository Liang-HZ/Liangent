from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from liangent.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def init_db_custom(url: str):
    """
    Initialize a custom database connection and return a Session.
    Useful for SDK mode where the DB URL might be different or in-memory.
    """
    custom_engine = create_engine(
        url, 
        connect_args={"check_same_thread": False} if "sqlite" in url else {}
    )
    Base.metadata.create_all(bind=custom_engine)
    CustomSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=custom_engine)
    return CustomSessionLocal()
