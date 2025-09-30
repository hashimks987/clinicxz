from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# --- SQLite Database Configuration ---
# This is the correct setup for SQLite. It points to a simple file
# named clinicxz.db that will be created in your project directory.
DATABASE_URL = "sqlite:///./clinicxz.db"

# The engine creation is slightly different for SQLite to support FastAPI's threading.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the DB session for your API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

