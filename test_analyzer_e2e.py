import json

import numpy as np

from analyzer import analyze


# =========================
# TEST CONFIG
# =========================

DATA_PATH = "comments.json"
TOPIC = "한국어 댓글 테스트"

SAMPLE_SIZE = 20
SAMPLE_METHOD = "even"

# 실제 E2E 테스트이므로 Claude API 사용
USE_API = True


def load_comments():
    """
    JSON 파일에서 댓글을 불러오고
    설정된 방식으로 테스트 표본을 선택한다.
    """

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        comments = json.load(file)

    if SAMPLE_SIZE is None:
        return comments

    sample_size = min(
        SAMPLE_SIZE,
        len(comments)
    )

    if SAMPLE_METHOD == "first":
        return comments[
            :sample_size
        ]

    if SAMPLE_METHOD == "even":
        indices = np.linspace(
            0,
            len(comments) - 1,
            sample_size,
            dtype=int
        )

        return [
            comments[index]
            for index in indices
        ]

    raise ValueError(
        f"지원하지 않는 SAMPLE_METHOD: "
        f"{SAMPLE_METHOD}"
    )


def print_selected_comments(comments):
    """
    실제 분석에 사용되는 댓글을 출력한다.
    """

    print(
        "\n========== TEST CONFIG =========="
    )

    print(
        f"Data: {DATA_PATH}"
    )

    print(
        f"Topic: {TOPIC}"
    )

    print(
        f"Sample method: {SAMPLE_METHOD}"
    )

    print(
        f"Sample size: {len(comments)}"
    )

    print(
        "\n========== INPUT COMMENTS =========="
    )

    for index, comment in enumerate(
        comments,
        start=1
    ):
        print(
            f"\n[{index}] "
            f"{comment.get('text', '')}"
        )


def print_result(result):
    """
    OpinionMap 분석 결과를 사람이 확인하기 쉬운
    형태로 출력한다.
    """

    print(
        "\n========== TOPIC =========="
    )

    print(
        result.get(
            "topic",
            ""
        )
    )

    print(
        "\n========== META =========="
    )

    print(
        json.dumps(
            result.get(
                "meta",
                {}
            ),
            ensure_ascii=False,
            indent=2
        )
    )

    print(
        "\n========== CLAIMS =========="
    )

    for claim in result.get(
        "claims",
        []
    ):
        print(
            f"\n[{claim['id']}] "
            f"{claim['text']}"
        )

        print(
            f"  count: "
            f"{claim.get('count', 0)}"
        )

        print(
            f"  stance: "
            f"{claim.get('stance', '')}"
        )

        for sample in claim.get(
            "sample_comments",
            []
        ):
            print(
                f"  - {sample}"
            )

    print(
        "\n========== RELATIONS =========="
    )

    relations = result.get(
        "relations",
        []
    )

    if not relations:
        print(
            "(관계 없음)"
        )

    for relation in relations:
        print(
            f"{relation['from']} "
            f"--{relation['type']}--> "
            f"{relation['to']}"
        )

    print(
        "\n========== HIDDEN OPINIONS =========="
    )

    hidden_opinions = result.get(
        "hidden_opinions",
        []
    )

    if not hidden_opinions:
        print(
            "(숨은 의견 없음)"
        )

    for opinion in hidden_opinions:
        print(
            f"- {opinion['text']} "
            f"(share={opinion['share']}, "
            f"top_share={opinion['top_share']})"
        )


def main():
    comments = load_comments()

    print_selected_comments(
        comments
    )

    print(
        "\n========== ANALYZER START =========="
    )

    result = analyze(
        comments,
        topic=TOPIC,
        use_api=USE_API
    )

    print_result(
        result
    )


if __name__ == "__main__":
    main()