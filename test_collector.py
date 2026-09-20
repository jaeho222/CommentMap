import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from collector import collect
from collector.clean import clean_comments
from collector.youtube import (
    extract_video_id,
    get_video_title,
)


SCHEMA_PATH = Path("contracts/comments.schema.json")


def validate_against_schema(data: list[dict]) -> None:
    with SCHEMA_PATH.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    Draft7Validator(
        schema,
        format_checker=FormatChecker(),
    ).validate(data)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://youtu.be/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "https://www.youtube.com/live/dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
        (
            "dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
    ],
)
def test_extract_video_id(url: str, expected: str) -> None:
    assert extract_video_id(url) == expected


def test_clean_comments() -> None:
    raw = [
        {
            "id": "cmt_001",
            "text": "  가격이   너무 올랐다  ",
            "likes": 1241,
            "time": "2026-01-10T12:00:00Z",
        },
        {
            "id": "cmt_002",
            "text": "가격이 너무 올랐다",
            "likes": 10,
            "time": "2026-01-10T12:01:00Z",
        },
        {
            "id": "cmt_003",
            "text": "🔥🔥🔥",
            "likes": 2,
            "time": "2026-01-10T12:02:00Z",
        },
        {
            "id": "cmt_004",
            "text": "a",
            "likes": 0,
            "time": "2026-01-10T12:03:00Z",
        },
        {
            "id": "cmt_005",
            "text": "https://spam.example",
            "likes": 0,
            "time": "2026-01-10T12:04:00Z",
        },
        {
            "id": "cmt_006",
            "text": "환율 생각하면 이 정도는 납득됨",
            "likes": 532,
            "time": "2026-01-10T12:05:00Z",
        },
    ]

    cleaned = clean_comments(raw)

    assert len(cleaned) == 2
    assert cleaned[0]["text"] == "가격이 너무 올랐다"
    assert cleaned[1]["text"] == "환율 생각하면 이 정도는 납득됨"

    validate_against_schema(cleaned)


def test_schema_example_shape() -> None:
    sample = [
        {
            "id": "cmt_001",
            "text": "가격이 너무 올랐다",
            "likes": 1241,
            "time": "2026-01-10T12:00:00Z",
        }
    ]

    validate_against_schema(sample)


@pytest.mark.skipif(
    not (
        os.getenv("YOUTUBE_API_KEY")
        and os.getenv("TEST_YOUTUBE_URL")
    ),
    reason="YOUTUBE_API_KEY 또는 TEST_YOUTUBE_URL이 없어 실제 API 테스트는 건너뜁니다.",
)
def test_real_youtube_collect() -> None:
    comments = collect(
        os.environ["TEST_YOUTUBE_URL"],
        max_comments=20,
    )

    assert isinstance(comments, list)
    validate_against_schema(comments)


def test_get_video_title() -> None:
    video_id = extract_video_id(
        os.environ["TEST_YOUTUBE_URL"]
    )

    title = get_video_title(video_id)

    assert isinstance(title, str)
    assert len(title.strip()) > 0