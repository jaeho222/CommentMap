from collector import collect
from analyzer import analyze


def analyze_url(
    url: str,
    max_comments: int | None = 100,
    topic: str = "",
    use_api: bool = False,
) -> dict:
    """
    YouTube URL 하나를 입력받아
    댓글 수집부터 OpinionMap 생성까지 연결한다.

    흐름:
        YouTube URL
        -> Collector
        -> Analyzer
        -> OpinionMap

    Parameters
    ----------
    url:
        분석할 YouTube URL

    max_comments:
        수집할 최대 댓글 수.
        None이면 가능한 댓글을 모두 수집한다.

    topic:
        영상 제목 또는 분석 주제.
        현재는 외부에서 선택적으로 전달한다.

    use_api:
        True일 때만 Claude API 분석을 실행한다.
        기본값은 False다.
    """

    if not url or not url.strip():
        raise ValueError(
            "YouTube URL이 비어 있습니다."
        )

    # 1. 실시간 댓글 수집 + Collector 전처리
    comments = collect(
        url=url.strip(),
        max_comments=max_comments,
    )

    if not comments:
        return {
            "topic": topic,
            "meta": {
                "total_comments": 0,
                "analyzed_comments": 0,
                "topic_count": 0,
                "claim_count": 0,
            },
            "claims": [],
            "relations": [],
            "hidden_opinions": [],
        }

    # 2. 수집된 댓글을 Analyzer에 전달
    return analyze(
        comments=comments,
        topic=topic,
        use_api=use_api,
    )