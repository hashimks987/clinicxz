from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use PostgreSQL connection string
# FORMAT: "postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
# DATABASE_URL = "postgresql://postgres:1234@localhost/clinicxz"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost/clinicxz")

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Database Dependency ---
# Moved from main.py to be accessible by other modules
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

