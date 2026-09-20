import hashlib
import json
from pathlib import Path


CACHE_DIR = Path(".cache")


def _make_cache_key(data):
    """
    입력 데이터를 기반으로
    동일한 요청을 구분할 수 있는 키를 만든다.
    """

    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def _get_cache_path(
    namespace,
    data
):
    """
    namespace와 입력 데이터를 이용해
    캐시 파일 경로를 만든다.
    """

    cache_key = _make_cache_key(
        data
    )

    directory = (
        CACHE_DIR
        / namespace
    )

    return (
        directory
        / f"{cache_key}.json"
    )


def load_cache(
    namespace,
    data
):
    """
    기존 캐시가 있으면 반환하고,
    없으면 None을 반환한다.
    """

    cache_path = _get_cache_path(
        namespace,
        data
    )

    if not cache_path.exists():
        return None

    try:
        with open(
            cache_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):
        return None


def save_cache(
    namespace,
    data,
    result
):
    """
    API 결과를 JSON 파일로 저장한다.
    """

    cache_path = _get_cache_path(
        namespace,
        data
    )

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        cache_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )