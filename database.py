from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# --- SQLite Database Configuration ---
# This is the core change. We now point to a local file named 'clinicxz.db'.
# No username, password, or server is needed.
DATABASE_URL = "sqlite:///./clinicxz.db"

# The engine creation is slightly different for SQLite to support FastAPI's threading.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

