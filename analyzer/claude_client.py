import os

from anthropic import Anthropic
from dotenv import load_dotenv


# 프로젝트 루트의 .env 파일 로드
load_dotenv()


API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL_NAME = os.getenv(
    "CLAUDE_MODEL",
    "claude-haiku-4-5-20251001"
)


def get_client():
    """
    Anthropic API Client를 생성한다.
    """

    if not API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY가 없습니다. "
            ".env 파일을 확인해주세요."
        )

    return Anthropic(
        api_key=API_KEY
    )


def ask_claude(
    prompt,
    system_prompt=None,
    max_tokens=1024
):
    """
    Claude에게 요청을 보내고
    생성된 텍스트를 반환한다.
    """

    client = get_client()

    request = {
        "model": MODEL_NAME,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    if system_prompt:
        request["system"] = system_prompt

    response = client.messages.create(
        **request
    )

    if not response.content:
        return ""

    text_parts = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]

    return "\n".join(text_parts)