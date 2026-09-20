import math


def find_hidden_opinions(
    claims,
    groups,
    comments
):
    """
    전체 댓글에서는 반복적으로 존재하지만
    좋아요 상위 댓글에서는 상대적으로
    덜 보이는 의견을 찾는다.

    전체 분포와 인기댓글 분포를 비교한다.
    """

    if (
        not comments
        or not claims
        or not groups
    ):
        return []

    comment_lookup = {
        comment["id"]: comment
        for comment in comments
        if comment.get("id")
    }

    if not comment_lookup:
        return []

    sorted_comments = sorted(
        comment_lookup.values(),
        key=lambda comment: comment.get(
            "likes",
            0
        ),
        reverse=True
    )

    # 원래 설계대로 좋아요 상위 30%를
    # 인기댓글 집합으로 사용한다.
    # 작은 데이터에서도 비교 가능하도록
    # 최대 3개까지 최소 표본을 확보한다.
    top_count = max(
        3,
        math.ceil(
            len(sorted_comments) * 0.3
        )
    )

    top_count = min(
        top_count,
        len(sorted_comments)
    )

    top_comments = sorted_comments[
        :top_count
    ]

    top_ids = {
        comment["id"]
        for comment in top_comments
    }

    total_comments = len(
        sorted_comments
    )

    hidden_opinions = []

    for claim, group in zip(
        claims,
        groups
    ):
        comment_ids = {
            comment_id
            for comment_id in group.get(
                "comment_ids",
                []
            )
            if comment_id in comment_lookup
        }

        if not comment_ids:
            continue

        # 하나의 댓글에서 여러 비슷한 claim이
        # 나왔더라도 댓글 하나로 계산한다.
        claim_count = len(
            comment_ids
        )

        share = (
            claim_count
            / total_comments
        )

        top_claim_count = len(
            comment_ids
            & top_ids
        )

        top_share = (
            top_claim_count
            / len(top_comments)
        )

        # 단 한 댓글에서만 나타난 의견은
        # 숨은 '분포'라고 보기 어렵기 때문에 제외한다.
        if claim_count < 2:
            continue

        # 전체 댓글에서 관측되는 비율보다
        # 인기댓글에서의 비율이 절반 이하라면
        # 인기댓글에 의해 상대적으로 가려진
        # 의견 후보로 본다.
        if top_share <= share * 0.5:
            hidden_opinions.append({
                "text": claim["text"],
                "share": round(
                    share,
                    4
                ),
                "top_share": round(
                    top_share,
                    4
                )
            })

    return hidden_opinions