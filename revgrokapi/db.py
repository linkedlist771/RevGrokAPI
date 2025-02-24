from revgrokapi.configs import DB_URL
from tortoise import Tortoise
from loguru import logger
# lifespan.py

async def init_db():
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ['revgrokapi.models']}
    )
    await Tortoise.generate_schemas()
    logger.info(f"Tortoise-ORM started, database connected: {DB_URL}")