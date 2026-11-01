import sys

from app.db import Base, normalize_url
from sqlalchemy import create_engine, text

url = sys.argv[1]
engine = create_engine(normalize_url(url), pool_pre_ping=True)
with engine.connect() as connection:
    version = connection.execute(text("SELECT version()")).scalar()
print("connected:", version.split(",")[0])
Base.metadata.create_all(engine)
with engine.connect() as connection:
    count = connection.execute(text("SELECT COUNT(*) FROM extractions")).scalar()
print("table extractions ready, rows:", count)
