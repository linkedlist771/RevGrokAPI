import asyncio
import time

from loguru import logger
from tqdm.asyncio import tqdm

from revgrokapi.models import Cookie
from revgrokapi.models.cookie_models import CookieQueries
from revgrokapi.revgrok import GrokClient


async def _check_grok_clients_limits():
    all_cookies = await Cookie.get_multi()
    for cookie in all_cookies:
        grok_client = GrokClient(cookie.cookie)
        default_weights = {
            "DEFAULT": 1,
            "REASONING": 1,
            "DEEPSEARCH": 1
        }
        try:
            rate_limit = await grok_client.get_rate_limit()
            # {'DEFAULT': {'windowSizeSeconds': 7200, 'remainingQueries': 75, 'totalQueries': 100},
            #  'REASONING': {'windowSizeSeconds': 7200, 'remainingQueries': 17, 'totalQueries': 30},
            #  'DEEPSEARCH': {'windowSizeSeconds': 7200, 'remainingQueries': 25, 'totalQueries': 30}}

            for kind, data in rate_limit.items():
                default_weights[kind] = data["remainingQueries"]
        except Exception as e:
            from traceback import format_exc
            logger.error(f"Error checking rate limit for cookie {cookie.id}: {format_exc()}")
        # 同时更新多个类别的权重
        await CookieQueries.update_weights(
            cookie=cookie,  # cookie 传入的就是这个
            weights=default_weights
        )


async def __check_grok_clients_limits():
    start_time = time.perf_counter()
    all_cookies = await Cookie.get_multi()
    logger.info(f"Found {len(all_cookies)} cookies to check")

    async def check_cookie(cookie):
        try:
            grok_client = GrokClient(cookie.cookie)
            default_weights = {
                "DEFAULT": 0,
                "REASONING": 0,
                "DEEPSEARCH": 0
            }
            rate_limit = await grok_client.get_rate_limit()

            for kind, data in rate_limit.items():
                default_weights[kind] = data["remainingQueries"]

            await CookieQueries.update_weights(
                cookie=cookie,
                weights=default_weights
            )

            return f"Cookie {cookie.id}: {default_weights}"
        except Exception as e:
            error_msg = f"Error checking cookie {cookie.id}: {e}"
            logger.error(error_msg)
            return error_msg

    async def process_batch(batch):
        return await asyncio.gather(*[check_cookie(cookie) for cookie in batch])

    results = []
    batch_size = 3  # 每批处理的客户端数量
    total_batches = (len(all_cookies) + batch_size - 1) // batch_size

    for i in range(0, len(all_cookies), batch_size):
        batch = all_cookies[i: i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1} of {total_batches}"
        )
        batch_results = await process_batch(batch)
        results.extend(batch_results)
        if i + batch_size < len(all_cookies):
            logger.info("Waiting between batches...")
            await asyncio.sleep(1)  # 批次之间的间隔

    time_elapsed = time.perf_counter() - start_time
    logger.debug(f"Time elapsed: {time_elapsed:.2f} seconds")
    for result in results:
        logger.info(result)


async def check_grok_clients_limits():
    # 使用 create_task，但不等待它完成
    task = asyncio.create_task(__check_grok_clients_limits())
    return {"message": "Grok clients check started in background"}