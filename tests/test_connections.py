from sqlalchemy import text

from app.database.session import engine


async def test_connection():

    async with engine.begin() as conn:

        result = await conn.execute(text("SELECT 1"))

        print(result)
