from sqlalchemy import create_engine
from urllib.parse import quote_plus

PASSWORD = quote_plus("Nevin1228!")

DB_URL = f"mysql+pymysql://root:{PASSWORD}@localhost:3306/nycparking2025"

engine = create_engine(
    DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)