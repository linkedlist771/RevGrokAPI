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
import json
from loguru import logger

from curl_cffi.requests import AsyncSession, BrowserType

from .configs import CHAT_URL
from .utils import get_default_chat_payload, get_default_user_agent


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
        self.client = AsyncSession(impersonate=BrowserType.chrome120)

    async def chat(self, prompt: str, model: str, reasoning: bool = False, deepresearch: bool = False):
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
            async for chunk_bytes in response.aiter_lines():
                chunk = chunk_bytes.decode('utf-8')
                logger.debug(chunk)
                try:
                    # yield parsed_output_and the chunk it self,
                    chunk_json = json.loads(chunk)
                except json.JSONDecodeError:
                    logger.debug(chunk)
                    chunk_json = {}
                    yield chunk, {}
                    # return

                if "error" in chunk:
                    # error_message = chunk_json.get("error").get("message")
                    yield chunk, chunk_json
                    return

                response = (
                    chunk_json.get("result", {}).get("response", {}).get("token", "")
                )
                yield response, chunk_json