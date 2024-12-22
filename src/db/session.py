from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.db.models import Base

# use localhost:5432 if you run from ipynb
DATABASE_URL = "postgresql+psycopg2://myuser:mypassword@postgres/mydatabase"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
