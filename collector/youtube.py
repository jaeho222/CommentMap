import os
import re
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _validate_video_id(video_id: str) -> str:
    video_id = video_id.strip()

    if not _VIDEO_ID_RE.fullmatch(video_id):
        raise ValueError(f"유효한 YouTube video id가 아닙니다: {video_id}")

    return video_id


def extract_video_id(url: str) -> str:
    """
    YouTube URL 또는 11자리 video id에서 video id를 추출합니다.

    지원 예:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - VIDEO_ID
    """
    value = url.strip()

    if _VIDEO_ID_RE.fullmatch(value):
        return value

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    host = parsed.netloc.lower().split(":")[0]

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
        return _validate_video_id(video_id)

    youtube_hosts = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
    }

    if host in youtube_hosts:
        if parsed.path.rstrip("/") == "/watch":
            query = parse_qs(parsed.query)
            if "v" in query and query["v"]:
                return _validate_video_id(query["v"][0])

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"shorts", "live", "embed"}:
            return _validate_video_id(parts[1])

    raise ValueError("지원하지 않는 YouTube URL 형식입니다.")


def _get_api_key() -> str:
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY가 없습니다. 프로젝트 루트의 .env 파일을 확인하세요."
        )

    return api_key


def _friendly_http_error(error: HttpError) -> RuntimeError:
    status = getattr(error.resp, "status", None)

    if status == 403:
        return RuntimeError(
            "YouTube API 요청이 거부되었습니다. "
            "API 키/YouTube Data API v3 활성화 여부를 확인하고, "
            "해당 영상의 댓글이 비활성화되어 있지 않은지도 확인하세요."
        )

    if status == 404:
        return RuntimeError(
            "영상을 찾을 수 없습니다. 삭제/비공개 영상이거나 URL이 잘못되었을 수 있습니다."
        )

    return RuntimeError(f"YouTube API 오류가 발생했습니다: {error}")

def get_video_title(video_id: str) -> str:
    """
    YouTube video_id를 받아 영상 제목을 반환합니다.
    analyzer에서 topic으로 사용할 수 있습니다.
    """
    video_id = _validate_video_id(video_id)

    youtube = build(
        "youtube",
        "v3",
        developerKey=_get_api_key(),
        cache_discovery=False,
    )

    try:
        response = (
            youtube.videos()
            .list(
                part="snippet",
                id=video_id,
                maxResults=1,
            )
            .execute()
        )

        items = response.get("items", [])

        if not items:
            raise RuntimeError(
                "영상 정보를 찾을 수 없습니다. "
                "삭제/비공개 영상이거나 video_id가 잘못되었을 수 있습니다."
            )

        return items[0]["snippet"]["title"]

    except HttpError as error:
        raise _friendly_http_error(error) from error
    
def fetch_comments(
    url: str,
    max_comments: int | None = None,
) -> list[dict]:
    """
    YouTube 영상의 최상위 댓글을 수집합니다.

    반환 형식은 contracts/comments.schema.json에 맞춰
    id / text / likes / time 네 필드만 반환합니다.
    """
    if max_comments is not None and max_comments <= 0:
        return []

    video_id = extract_video_id(url)

    youtube = build(
        "youtube",
        "v3",
        developerKey=_get_api_key(),
        cache_discovery=False,
    )

    comments: list[dict] = []
    page_token: str | None = None

    try:
        while True:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                textFormat="plainText",
                order="time",
            )

            response = request.execute()

            for item in response.get("items", []):
                top_level_comment = item["snippet"]["topLevelComment"]
                snippet = top_level_comment["snippet"]

                text = (
                    snippet.get("textOriginal")
                    or snippet.get("textDisplay")
                    or ""
                )

                comments.append(
                    {
                        "id": str(top_level_comment["id"]),
                        "text": str(text),
                        "likes": int(snippet.get("likeCount", 0)),
                        "time": str(snippet["publishedAt"]),
                    }
                )

                if max_comments is not None and len(comments) >= max_comments:
                    return comments[:max_comments]

            page_token = response.get("nextPageToken")

            if not page_token:
                break

    except HttpError as error:
        raise _friendly_http_error(error) from error

    return comments
