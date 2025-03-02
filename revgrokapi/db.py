from loguru import logger
from tortoise import Tortoise

from revgrokapi.configs import DB_URL

# lifespan.py


async def init_db():
    await Tortoise.init(db_url=DB_URL, modules={"models": ["revgrokapi.models"]})
    await Tortoise.generate_schemas()
    logger.info(f"Tortoise-ORM started, database connected: {DB_URL}")
