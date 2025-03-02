from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from revgrokapi.db import init_db
from revgrokapi.utils.time_zone_utils import set_cn_time_zone

# from rev_claude.client.client_manager import ClientManager
# from rev_claude.periodic_checks.limit_sheduler import LimitScheduler


async def on_startup():
    logger.info("Lifespan Starting up")
    set_cn_time_zone()
    await init_db()


async def on_shutdown():
    logger.info("Lifespan Shutting down")
    # await LimitScheduler.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()
