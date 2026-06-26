from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# Engine — the actual connection to PostgreSQL
# pool_pre_ping=True means SQLAlchemy will test the connection
# before using it, so stale connections don't cause errors
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# SessionLocal — a factory that creates new database sessions
# autocommit=False means we control when changes are saved
# autoflush=False means changes aren't sent to DB until we say so
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base — parent class for all our table models
Base = declarative_base()


# Dependency function — used by FastAPI endpoints to get a DB session
# It opens a session, gives it to the endpoint, then closes it when done
# The try/finally ensures the session is ALWAYS closed even if an error occurs
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()