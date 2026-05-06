from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "auth", ".env"), override=True)

SQLALCHEMY_DATABASE_URL = os.getenv("sqlalchemy_database_url")
if not SQLALCHEMY_DATABASE_URL:
    username = os.getenv("sqlusername", "root")
    password = os.getenv("sqlpassword", "")
    host = os.getenv("sqlhost", "localhost")
    database = os.getenv("sql_database", "defence_surveillance")
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+mysqlconnector://{quote_plus(username)}:{quote_plus(password)}@{host}:3306/{database}"
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
