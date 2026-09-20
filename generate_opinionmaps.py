import json
import sys
from pathlib import Path

from analyzer import analyze


ISSUES_PATH = Path("data/issues/issues.json")
OUTPUT_DIR = Path("data/opinionmaps")

USE_API = True


def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def generate_opinionmap(issue):
    slug = issue["slug"]
    topic = issue["label"]
    comments_path = Path(
        issue["comments_file"]
    )

    output_path = (
        OUTPUT_DIR / f"{slug}.json"
    )

    print()
    print("=" * 60)
    print(f"ISSUE: {topic}")
    print(f"INPUT: {comments_path}")
    print(f"OUTPUT: {output_path}")
    print("=" * 60)

    comments = load_json(
        comments_path
    )

    result = analyze(
        comments,
        topic=topic,
        use_api=USE_API
    )

    save_json(
        output_path,
        result
    )

    print()
    print(
        f"완료: {output_path}"
    )
    print(
        f"claims={len(result['claims'])}, "
        f"relations={len(result['relations'])}, "
        f"hidden={len(result['hidden_opinions'])}"
    )


def find_issue(issues, slug):
    for issue in issues:
        if issue.get("slug") == slug:
            return issue

    return None


def main():
    issues = load_json(
        ISSUES_PATH
    )

    if not isinstance(issues, list):
        raise ValueError(
            "issues.json의 최상위 구조는 "
            "리스트여야 합니다."
        )

    # slug를 입력한 경우:
    # 해당 이슈 하나만 생성
    if len(sys.argv) >= 2:
        slug = sys.argv[1]

        issue = find_issue(
            issues,
            slug
        )

        if issue is None:
            available_slugs = [
                item.get("slug", "")
                for item in issues
            ]

            raise ValueError(
                f"존재하지 않는 slug입니다: {slug}\n"
                f"사용 가능한 slug: "
                f"{', '.join(available_slugs)}"
            )

        print(
            f"단일 OpinionMap 생성: {slug}"
        )

        generate_opinionmap(
            issue
        )

        return

    # slug가 없으면 전체 생성
    print(
        f"총 {len(issues)}개 이슈의 "
        "OpinionMap을 생성합니다."
    )

    for issue in issues:
        generate_opinionmap(
            issue
        )

    print()
    print("=" * 60)
    print("모든 OpinionMap 생성 완료")
    print(f"저장 위치: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()