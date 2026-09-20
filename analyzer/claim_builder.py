def select_representative_claim(group):
    """
    그룹 안에서 대표 claim을 선택한다.

    불필요하게 긴 표현보다 비교적 간결한
    기존 claim을 대표로 사용한다.

    새로운 문장을 생성하지 않으므로
    원래 의견을 임의로 변경하지 않는다.
    """

    claims = group.get(
        "claims",
        []
    )

    valid_claims = [
        claim
        for claim in claims
        if claim.get(
            "text",
            ""
        ).strip()
    ]

    if not valid_claims:
        return ""

    representative = min(
        valid_claims,
        key=lambda claim: len(
            claim["text"]
        )
    )

    return representative["text"]


def build_sample_comments(
    group,
    comment_lookup,
    max_samples=3
):
    """
    claim 그룹에 포함된 실제 댓글 중
    프론트에서 보여줄 대표 댓글을 선택한다.
    """

    samples = []

    for comment_id in group.get(
        "comment_ids",
        []
    ):
        comment = comment_lookup.get(
            comment_id
        )

        if not comment:
            continue

        text = comment.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        if text in samples:
            continue

        samples.append(
            text
        )

        if len(samples) >= max_samples:
            break

    return samples


def build_final_claims(
    groups,
    comments
):
    """
    병합된 claim 그룹을 OpinionMap contract의
    claim 형태로 변환한다.

    stance는 이후 stance_classifier에서
    실제 의미를 기반으로 판정한다.
    """

    comment_lookup = {
        comment["id"]: comment
        for comment in comments
        if comment.get("id")
    }

    final_claims = []

    for group in groups:
        representative_text = (
            select_representative_claim(
                group
            )
        )

        if not representative_text:
            continue

        sample_comments = (
            build_sample_comments(
                group,
                comment_lookup
            )
        )

        final_claims.append({
            "id": (
                f"c{len(final_claims) + 1}"
            ),
            "text": representative_text,
            "count": group.get(
                "count",
                0
            ),
            "stance": "neutral",
            "sample_comments": sample_comments
        })

    return final_claims