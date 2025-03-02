import argparse
import os

import fire
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from revgrokapi.configs import LOG_DIR
from revgrokapi.lifespan import lifespan
from revgrokapi.middlewares.register_middlewares import register_middleware
from revgrokapi.router import router

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="0.0.0.0", help="host")
parser.add_argument("--port", default=3648, help="port")
args = parser.parse_args()
logger.add(LOG_DIR / "log_file.log", rotation="1 week")  # 每周轮换一次文件

app = FastAPI(lifespan=lifespan)
app = register_middleware(app)


def start_server(port=args.port, host=args.host):
    logger.info(f"Starting server at {host}:{port}")
    app.include_router(router)
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config=config)
    try:
        server.run()
    finally:
        logger.info("Server shutdown.")


if __name__ == "__main__":
    fire.Fire(start_server)
