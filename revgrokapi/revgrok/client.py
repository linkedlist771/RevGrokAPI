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
import time
import re
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
        self.client = AsyncSession(
            impersonate=BrowserType.chrome120,
            proxies=PROXIES,
            timeout=60.0
        )
        self.cf_clearance = self._extract_cf_clearance(cookie)

    def _extract_cf_clearance(self, cookie: str) -> str:
        """从cookie字符串中提取cf_clearance值"""
        match = re.search(r'cf_clearance=([^;]+)', cookie)
        return match.group(1) if match else ""

    async def _handle_cloudflare(self, url: str) -> bool:
        """处理Cloudflare挑战并获取所需的cookies"""
        logger.info("检测到Cloudflare挑战，尝试解决...")
        try:
            # 直接访问主页面获取Cloudflare cookies
            response = await self.client.get(
                "https://grok.com/",
                headers={k: v for k, v in self.headers.items() if k != "Content-Type"},
                impersonate=BrowserType.chrome120
            )

            # 检查是否仍在Cloudflare挑战页面
            if "Just a moment" in response.text or "challenge-running" in response.text:
                logger.warning("仍在Cloudflare挑战页面，等待5秒后重试...")
                await asyncio.sleep(5)
                return False

            # 从响应中提取新的cookies
            cookies = response.cookies
            if cookies:
                # 更新cookie
                for name, value in cookies.items():
                    if name == "cf_clearance" and value:
                        self.cf_clearance = value
                        if "cf_clearance=" in self.cookie:
                            self.cookie = re.sub(r'cf_clearance=[^;]+', f'cf_clearance={value}', self.cookie)
                        else:
                            self.cookie += f"; cf_clearance={value}"
                        logger.info("成功获取新的cf_clearance")
                return True

            return False
        except Exception as e:
            logger.error(f"处理Cloudflare挑战时出错: {e}")
            return False

    @async_retry(retries=3, delay=2)
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

        try:
            async with self.client.stream(
                    method="POST",
                    url=CHAT_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=600.0,
            ) as response:
                # 检查是否遇到Cloudflare挑战
                # 注意：curl_cffi的响应对象没有aread方法，需要使用text属性
                if response.status_code == 403 or response.status_code == 503:
                    # 对于curl_cffi，直接使用response.text获取内容
                    if "Just a moment" in response.text or "challenge-running" in response.text:
                        # 处理Cloudflare挑战
                        success = await self._handle_cloudflare(CHAT_URL)
                        if success:
                            # 重新尝试请求
                            raise Exception("需要重试请求")  # 触发async_retry装饰器
                        else:
                            yield "Cloudflare挑战失败，请检查cookie或更换IP", {"error": "Cloudflare challenge failed"}
                            return

                # 常规响应处理
                is_first_chunk = True
                async for chunk_bytes in response.aiter_lines():
                    chunk = chunk_bytes.decode("utf-8")
                    if is_first_chunk:
                        logger.debug(f"First chunk: {chunk}")
                        is_first_chunk = False
                    try:
                        chunk_json = json.loads(chunk)
                    except json.JSONDecodeError:
                        logger.debug(chunk)
                        chunk_json = {}
                        yield chunk, {}

                    if "error" in chunk and "isThinking" not in chunk:
                        yield chunk, chunk_json
                        return

                    response_token = (
                        chunk_json.get("result", {}).get("response", {}).get("token", "")
                    )
                    yield response_token, chunk_json

        except Exception as e:
            logger.error(f"聊天请求出错: {e}")
            # 检查是否是连接问题，可能是被Cloudflare阻止
            if "Connection" in str(e) or "Timeout" in str(e):
                # 尝试处理Cloudflare
                await self._handle_cloudflare(CHAT_URL)
            yield f"请求出错: {str(e)}", {"error": str(e)}

    # 为rate_limit请求也添加Cloudflare处理
    async def _get_single_rate_limit(self, request_kind, model_name="grok-3"):
        """Helper method to fetch rate limit for a specific request kind"""
        url = RATE_LIMIT_URL
        payload = {
            "requestKind": request_kind,
            "modelName": model_name,
        }
        json_response = {
            "windowSizeSeconds": 0,
            "remainingQueries": 0,
        }
        try:
            rate_limit_response = await self.client.post(
                url, headers=self.headers, json=payload
            )

            # 检查是否遇到Cloudflare挑战
            if rate_limit_response.status_code == 403 or rate_limit_response.status_code == 503:
                # 对于curl_cffi，使用text属性
                if "Just a moment" in rate_limit_response.text or "challenge-running" in rate_limit_response.text:
                    # 处理Cloudflare挑战
                    success = await self._handle_cloudflare(url)
                    if success:
                        # 重新尝试请求
                        raise Exception("需要重试请求")  # 触发async_retry装饰器

            json_response = rate_limit_response.json()
        except Exception as e:
            logger.error(f"获取rate limit时出错: {e}")
            pass
        logger.debug(json_response)
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

        return rate_limits