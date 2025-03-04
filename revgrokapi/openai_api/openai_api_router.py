import asyncio
import json
import time
import uuid
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

from revgrokapi.configs import POE_OPENAI_LIKE_API_KEY
from revgrokapi.openai_api.schemas import ChatCompletionRequest, ChatMessage
from revgrokapi.openai_api.utils import grok_chat

# from rev_claude.client.claude_router import (ClientManager,
#                                              select_client_by_usage)
# from rev_claude.configs import POE_OPENAI_LIKE_API_KEY
# from rev_claude.history.conversation_history_manager import \
#     conversation_history_manager
# from rev_claude.openai_api.schemas import ChatCompletionRequest, ChatMessage
# from rev_claude.openai_api.utils import (extract_messages_and_images,
#                                          summarize_a_title)
# from utility import get_client_status

# Add this constant at the top of the file after the imports
VALID_API_KEY = POE_OPENAI_LIKE_API_KEY

router = APIRouter()


async def _async_resp_generator(original_generator, model: str):
    i = 0
    response_text = ""
    first_chunk = True
    async for data in original_generator:
        response_text += data
        chunk = {
            "id": i,
            "object": "chat.completion.chunk",
            "created": time.time(),
            "model": model,
            "choices": [
                {
                    "delta": {
                        "content": f"{data}",
                        **(
                            {"role": "assistant"} if first_chunk else {}
                        ),  # 只在第一个chunk添加role
                    }
                }
            ],
        }
        first_chunk = False

        yield f"data: {json.dumps(chunk)}\n\n"
        i += 1

    yield f"data: {json.dumps({'choices':[{'index': 0, 'delta': {}, 'logprobs': None, 'finish_reason': 'stop'}]})}\n\n"
    yield "data: [DONE]\n\n"


async def streaming_message(request: ChatCompletionRequest, api_key: str = None):
    # Add API key validation
    if api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    model = request.model
    # Validate API key here if needed
    # done_data = build_sse_data(message="closed", id=conversation_id)
    # basic_clients = clients["basic_clients"]
    # plus_clients = clients["plus_clients"]
    # client_type = "plus"
    # client_idx = 0
    # status_list = await get_client_status(basic_clients, plus_clients)
    # claude_client = await select_client_by_usage(
    #     client_type, client_idx, basic_clients, plus_clients, status_list
    # )
    # conversation_id = str(uuid4())
    # attachments = []
    # files = []
    messages = request.messages
    # messages, file_paths = await extract_messages_and_images(messages)
    prompt = "\n".join([f"{message.role}: {message.content}" for message in messages])
    return grok_chat(model, prompt)
    # last_message = messages[-1]
    # request_model = request.model
    # if "r1" in request_model.lower():
    #     force_think_template = """\
    # 上面是之前的历史记录,对于下面的问题，不管多简单，多复杂，都需要详细思考后给出答案。下面是你的回复格式:
    # <think>
    # # put your thinking here
    # </think>"""
    #     prompt = prompt.replace(force_think_template, "")
    #     prompt += f"\n{force_think_template}\n"
    # prompt += f"""{last_message.role}: {last_message.content}"""
    # # logger.debug(f"Prompt: {prompt}")
    # call_back = None
    # if request.stream:
    #     streaming_res = claude_client.stream_message(
    #         prompt,
    #         conversation_id,
    #         model,
    #         client_type=client_type,
    #         client_idx=client_idx,
    #         attachments=attachments,
    #         files=files,
    #         call_back=call_back,
    #         api_key=api_key,
    #         file_paths=file_paths,
    #     )

    # return streaming_res
    # else:

    #     title = await conversation_history_manager.get_conversation_title(
    #         api_key=api_key, conversation_id=conversation_id
    #     )
    #     if title:
    #         return title
    #     else:
    #         conversation_str = "\n".join(
    #             [f"{message.role}: {message.content}" for message in messages]
    #         )[:1000]
    #         title = await summarize_a_title(
    #             conversation_str, conversation_id, client_idx, api_key, claude_client
    #         )
    #         await conversa
    #         tion_history_manager.set_conversation_title(
    #             api_key=api_key, conversation_id=conversation_id, title=title
    #         )
    #         return title


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, authorization: str = Header(None)
):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    # logger.debug(f"authorization: {authorization}")
    # Extract API key from Authorization header
    api_key = None
    if authorization:
        if authorization.startswith("Bearer"):
            api_key = authorization.replace("Bearer", "").strip()

    # logger.debug(f"API key: {api_key}")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header. Format should be 'Bearer YOUR_API_KEY'",
        )

    resp_content = await streaming_message(request, api_key=api_key)
    if request.stream:
        return StreamingResponse(
            _async_resp_generator(resp_content, request.model),
            media_type="text/event-stream",
        )

    return {
        "id": uuid.uuid4(),
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [{"message": ChatMessage(role="assistant", content="not implemented")}],
    }
