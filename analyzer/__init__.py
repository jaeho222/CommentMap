from .preprocess import preprocess_comments
from .claim_extractor import extract_claims_with_claude
from .claim_merger import merge_claims
from .claim_builder import build_final_claims
from .stance_classifier import classify_claim_stances
from .relation_builder import build_relations
from .hidden import find_hidden_opinions


def empty_result(
    total_comments=0,
    topic=""
):
    """
    분석 결과가 없는 경우의
    기본 OpinionMap 구조를 반환한다.
    """

    return {
        "topic": topic,
        "meta": {
            "total_comments": total_comments,
            "analyzed_comments": 0,
            "topic_count": 0,
            "claim_count": 0
        },
        "claims": [],
        "relations": [],
        "hidden_opinions": []
    }


def analyze(
    comments,
    topic="",
    use_api=False
):
    """
    CommentMap 전체 분석 파이프라인.

    댓글에서 개별 claim을 추출한 뒤,
    동일한 의견을 병합한다.

    이후 topic relevance와 stance를 판정하고,
    관련 있는 claim만 OpinionMap에 포함한다.

    마지막으로 claim 사이의 관계와
    hidden opinion을 분석한다.

    topic:
        collector 또는 웹페이지에서 얻은
        게시물/영상의 제목이나 주제.

    use_api:
        True일 때만 Claude 기반 분석을 허용한다.
    """

    if not comments:
        return empty_result(
            topic=topic
        )

    processed_comments = (
        preprocess_comments(
            comments
        )
    )

    if not processed_comments:
        return empty_result(
            total_comments=len(
                comments
            ),
            topic=topic
        )

    if not use_api:
        raise RuntimeError(
            "Claude API 사용이 비활성화되어 있습니다. "
            "API 테스트가 필요한 경우에만 "
            "analyze(..., use_api=True)를 사용하세요."
        )

    # 1. 댓글에서 개별 claim 추출
    claim_results = (
        extract_claims_with_claude(
            processed_comments
        )
    )

    # 2. 같은 의미의 claim 병합
    groups = merge_claims(
        claim_results
    )

    # 3. 최종 OpinionMap claim 후보 생성
    claims = build_final_claims(
        groups,
        processed_comments
    )

    # build_final_claims에서 유효하지 않은
    # group이 제외될 가능성에 대비해
    # 최종 claim과 대응되는 group만 유지한다.
    valid_groups = [
        group
        for group in groups
        if any(
            claim.get(
                "text",
                ""
            ).strip()
            for claim in group.get(
                "claims",
                []
            )
        )
    ]

    # 4. topic relevance와 stance 판정
    classified_claims = (
        classify_claim_stances(
            claims,
            topic
        )
    )

    # 5. topic과 관련 있는 claim과
    # 대응 group만 함께 유지한다.
    filtered_pairs = [
        (claim, group)
        for claim, group in zip(
            classified_claims,
            valid_groups
        )
        if claim.get(
            "relevant",
            False
        )
    ]

    claims = []
    filtered_groups = []

    for index, (
        claim,
        group
    ) in enumerate(
        filtered_pairs,
        start=1
    ):
        final_claim = dict(
            claim
        )

        # relevance는 내부 판정용이므로
        # 최종 OpinionMap에는 포함하지 않는다.
        final_claim.pop(
            "relevant",
            None
        )

        # 필터링 후 claim ID를 다시 정리한다.
        final_claim["id"] = (
            f"c{index}"
        )

        claims.append(
            final_claim
        )

        filtered_groups.append(
            group
        )

    # 관련 claim이 하나도 없으면
    # 빈 OpinionMap을 반환한다.
    if not claims:
        return {
            "topic": topic,
            "meta": {
                "total_comments": len(
                    comments
                ),
                "analyzed_comments": len(
                    processed_comments
                ),
                "topic_count": 0,
                "claim_count": 0
            },
            "claims": [],
            "relations": [],
            "hidden_opinions": []
        }

    # 관련 claim이 등장한 고유 댓글 수 계산
    topic_comment_ids = set()

    for group in filtered_groups:
        for comment_id in group.get(
            "comment_ids",
            []
        ):
            topic_comment_ids.add(
                comment_id
            )

    topic_count = len(
        topic_comment_ids
    )

    # 6. 관련 claim 사이 관계 생성
    relations = build_relations(
        claims
    )

    # 7. 전체 댓글 분포와 인기댓글 분포를
    # 비교해 hidden opinion 탐색
    hidden_opinions = (
        find_hidden_opinions(
            claims,
            filtered_groups,
            processed_comments
        )
    )

    return {
        "topic": topic,
        "meta": {
            "total_comments": len(
                comments
            ),
            "analyzed_comments": len(
                processed_comments
            ),
            "topic_count": topic_count,
            "claim_count": len(
                claims
            )
        },
        "claims": claims,
        "relations": relations,
        "hidden_opinions": (
            hidden_opinions
        )
    }