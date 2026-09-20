import json

from analyzer.preprocess import preprocess_comments
from analyzer.claim_extractor import extract_claims_with_claude


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

    # 비용을 아끼기 위해 우선 10개만 테스트
    test_comments = processed_comments[:10]

    print(
        f"테스트 댓글 수: {len(test_comments)}"
    )

    print("\n[원본 댓글]")

    for index, comment in enumerate(
        test_comments,
        start=1
    ):
        print(
            f"\n{index}. {comment['text']}"
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Claude claim 추출 중..."
    )

    results = extract_claims_with_claude(
        test_comments
    )

    print(
        "\n[추출 결과]"
    )

    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()