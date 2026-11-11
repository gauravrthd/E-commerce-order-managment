from sqlalchemy import text
from database.connection import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )
        print("Database connected successfully!")
        print(result.fetchone())

except Exception as e:
    print("Database connection failed!")
    print(type(e).__name__, str(e))