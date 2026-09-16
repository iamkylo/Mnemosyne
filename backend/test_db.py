import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

async def test_db():
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            print("Connected successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
