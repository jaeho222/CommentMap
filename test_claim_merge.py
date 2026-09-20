import json

import numpy as np

from analyzer.preprocess import preprocess_comments
from analyzer.claim_extractor import extract_claims_with_claude
from analyzer.claim_merger import (
    flatten_claims,
    merge_claims
)


def select_comments(comments, sample_count=20):
    """
    데이터 전체 구간에서 댓글을 골고루 선택한다.
    """

    if len(comments) <= sample_count:
        return comments

    indices = np.linspace(
        0,
        len(comments) - 1,
        sample_count,
        dtype=int
    )

    indices = np.unique(indices)

    return [
        comments[index]
        for index in indices
    ]


def main():
    file_path = "data/comments_ai_jobs.json"

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        comments = json.load(file)

    processed_comments = preprocess_comments(
        comments
    )

    test_comments = select_comments(
        processed_comments,
        sample_count=20
    )

    print(
        f"전체 댓글 수: {len(processed_comments)}"
    )

    print(
        f"테스트 댓글 수: {len(test_comments)}"
    )

    print(
        "\n1. Claude claim 추출 중..."
    )

    claim_results = extract_claims_with_claude(
        test_comments
    )

    claims = flatten_claims(
        claim_results
    )

    print(
        f"추출된 claim 수: {len(claims)}"
    )

    print(
        "\n2. E5 후보 탐색 + Claude 병합 판정 중..."
    )

    groups = merge_claims(
        claim_results,
        top_k=3
    )

    print(
        f"\n최종 의견 그룹 수: {len(groups)}"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "[병합 결과]"
    )

    for index, group in enumerate(
        groups,
        start=1
    ):
        print(
            "\n"
            + "=" * 70
        )

        print(
            f"[Group #{index}]"
        )

        print(
            f"댓글 수: {group['count']}"
        )

        print(
            f"포함 claim 수: {len(group['claims'])}"
        )

        for claim_index, claim in enumerate(
            group["claims"],
            start=1
        ):
            print(
                f"\n  {claim_index}. {claim['text']}"
            )

            print(
                f"     comment_id: {claim['comment_id']}"
            )


if __name__ == "__main__":
    main()