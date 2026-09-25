from sqlalchemy import create_engine, text

from app.config import settings

engine = create_engine(settings.DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ Database connected successfully!")
        print(result.fetchone())

except Exception as e:
    print("❌ Database connection failed!")
    print(e)