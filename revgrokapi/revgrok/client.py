# import json
# from loguru import logger
#
# import httpx
#
# from .configs import CHAT_URL
# from .utils import get_default_chat_payload, get_default_user_agent
#
#
# class GrokClient:
#     @property
#     def headers(self):
#         return {
#             "Accept": "*/*",
#             "Accept-Encoding": "gzip, deflate, br",
#             "Accept-Language": "en-US,en;q=0.9",
#             "Content-Type": "application/json",
#             "Cookie": self.cookie,
#             "Origin": "https://grok.com",
#             "Referer": "https://grok.com/",
#             "Sec-Fetch-Dest": "empty",
#             "Sec-Fetch-Mode": "cors",
#             "Sec-Fetch-Site": "same-origin",
#             "User-Agent": self.user_agent,
#         }
#
#     def __init__(self, cookie: str, user_agent: str | None = None):
#         self.cookie = cookie
#         self.user_agent = user_agent if user_agent else get_default_user_agent()
#         self.client = httpx.AsyncClient()
#
#     async def chat(self, prompt: str, model: str, reasoning: bool=False, deepresearch: bool=False):
#         default_payload = get_default_chat_payload()
#         update_payload = {
#             "modelName": model,
#             "message": prompt,
#             "isReasoning": reasoning,
#             "deepsearchPreset": "default" if deepresearch else "",
#         }
#
#         default_payload.update(update_payload)
#         payload = default_payload
#         async with self.client.stream(
#             method="POST",
#             url=CHAT_URL,
#             headers=self.headers,
#             json=payload,
#             timeout=600.0,  # 30 seconds timeout
#
#         ) as response:
#             async for chunk in response.aiter_lines():
#                 try:
#                     # yield parsed_output_and the chunk it self,
#                     chunk_json = json.loads(chunk)
#                 except json.JSONDecodeError:
#                     logger.debug(chunk)
#                     chunk_json = {}
#                     yield chunk, {}
#                     # return
#                 if "error" in chunk:
#                     # error_message = chunk_json.get("error").get("message")
#                     yield chunk, chunk_json
#                     return
#                 response = (
#                     chunk_json.get("result", {}).get("response", {}).get("token", "")
#                 )
#                 yield response, chunk_json
import asyncio
import json

from curl_cffi.requests import AsyncSession, BrowserType
from loguru import logger

from .configs import CHAT_URL, RATE_LIMIT_URL
from .utils import get_default_chat_payload, get_default_user_agent
from ..configs import PROXIES
from ..utils.async_utils import async_retry


class GrokClient:
    @property
    def headers(self):
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Origin": "https://grok.com",
            "Referer": "https://grok.com/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.user_agent,
        }

    def __init__(self, cookie: str, user_agent: str | None = None):
        self.cookie = cookie
        self.user_agent = user_agent if user_agent else get_default_user_agent()
        self.client = AsyncSession(impersonate=BrowserType.chrome120,
                                   proxies=PROXIES
                                   )

    async def chat(
        self,
        prompt: str,
        model: str,
        reasoning: bool = False,
        deepresearch: bool = False,
    ):
        default_payload = get_default_chat_payload()
        update_payload = {
            "modelName": model,
            "message": prompt,
            "isReasoning": reasoning,
            "deepsearchPreset": "default" if deepresearch else "",
        }

        default_payload.update(update_payload)
        payload = default_payload

        async with self.client.stream(
            method="POST",
            url=CHAT_URL,
            headers=self.headers,
            json=payload,
            timeout=600.0,
        ) as response:
            # curl_cffi 返回的是字节，需要解码
            is_first_chunk = True
            async for chunk_bytes in response.aiter_lines():
                chunk = chunk_bytes.decode("utf-8")
                if is_first_chunk:
                    logger.debug(f"First chunk: {chunk}")
                    is_first_chunk = False
                try:
                    # yield parsed_output_and the chunk it self,
                    chunk_json = json.loads(chunk)
                except json.JSONDecodeError:
                    logger.debug(chunk)
                    chunk_json = {}
                    yield chunk, {}
                    # return

                if "error" in chunk and "isThinking" not in chunk:
                    # error_message = chunk_json.get("error").get("message")
                    yield chunk, chunk_json
                    return

                response = (
                    chunk_json.get("result", {}).get("response", {}).get("token", "")
                )
                yield response, chunk_json

    # @async_retry(retries=4, delay=3)
    async def _get_single_rate_limit(self, request_kind, model_name="grok-3"):
        """Helper method to fetch rate limit for a specific request kind"""
        url = RATE_LIMIT_URL
        payload = {
            "requestKind": request_kind,
            "modelName": model_name,
        }
        rate_limit_response = await self.client.post(
            url, headers=self.headers, json=payload
        )
        json_response = rate_limit_response
        logger.debug(rate_limit_response)
        return request_kind, json_response

    async def get_rate_limit(self):
        """Fetch rate limits for all model types concurrently using asyncio.gather"""
        model_types = ["DEFAULT", "REASONING", "DEEPSEARCH"]

        # Use asyncio.gather to run all requests concurrently
        results = await asyncio.gather(
            *[self._get_single_rate_limit(kind) for kind in model_types]
        )

        # Format results into a dictionary {request_kind: rate_limit_data}
        rate_limits = {kind: data for kind, data in results}
        # {'DEFAULT': {'windowSizeSeconds': 7200, 'remainingQueries': 75, 'totalQueries': 100},
        #  'REASONING': {'windowSizeSeconds': 7200, 'remainingQueries': 17, 'totalQueries': 30},
        #  'DEEPSEARCH': {'windowSizeSeconds': 7200, 'remainingQueries': 25, 'totalQueries': 30}}
        return rate_limits
