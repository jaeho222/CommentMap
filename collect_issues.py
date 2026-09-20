import json
import os
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

from collector import collect
from collector.youtube import get_video_title
from run_collector import validate_comments


load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY가 없습니다. 프로젝트 루트의 .env를 확인하세요.")

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY,
    cache_discovery=False,
)

MAX_COMMENTS = 300
OUTPUT_DIR = Path("data/issues")
SCHEMA_PATH = Path("contracts/comments.schema.json")

ISSUES = [
    {
        "slug": "hormuz_deployment",
        "label": "호르무즈 해협 파병 논의",
        "video_id": "eRYeVfjiIf8",
        "query": "호르무즈 해협 파병 논란 2026 한국 뉴스",
    },
    {
        "slug": "samsung_hynix_stock",
        "label": "삼성전자·SK하이닉스 주가",
        "video_id": "wOk2qTjgKKw",
        "query": "삼성전자 SK하이닉스 지금 사도 되나요 2026 주식",
    },
    {
        "slug": "asian_games_operation",
        "label": "2026 아시안게임 운영 논란",
        "video_id": None,
        "query": "2026 아시안게임 부실 운영 선수촌 컨테이너 MBC뉴스",
    },
    {
        "slug": "iphone_18_pro",
        "label": "아이폰 18 Pro",
        "video_id": "y3Vm53Yql_o",
        "query": "아이폰 18 프로 리뷰 2026 한국",
    },
    {
        "slug": "yeosu_island_expo",
        "label": "여수세계섬박람회 논란",
        "video_id": "ZvFaV7Far14",
        "query": "2026 여수세계섬박람회 논란 트럭배",
    },
    {
        "slug": "north_korea_missile",
        "label": "북한 동해상 발사체",
        "video_id": "3C2DnEIeSSw",
        "query": "북한 동해상 발사체 2026 9월 뉴스",
    },
    {
        "slug": "president_press_conference",
        "label": "대통령 대국민 기자회견",
        "video_id": "WKNpIByKxQA",
        "query": "이재명 대통령 대국민 기자회견 2026 9월 18일",
    },
    {
        "slug": "real_estate_flattening",
        "label": "부동산 '평탄화' 발언",
        "video_id": "wR-b0lwKuXQ",
        "query": "강남 하락 외곽 상승 평탄화 대통령 부동산 2026",
    },
    {
        "slug": "newjeans_return",
        "label": "뉴진스 활동 재개",
        "video_id": "NNbaTJX_9go",
        "query": "뉴진스 복귀 2026 Summer of NewJeans",
    },
]


def search_video_ids(query: str, max_results: int = 10) -> list[str]:
    response = (
        youtube.search()
        .list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="relevance",
            regionCode="KR",
            relevanceLanguage="ko",
        )
        .execute()
    )

    return [
        item["id"]["videoId"]
        for item in response.get("items", [])
        if item.get("id", {}).get("videoId")
    ]


def candidate_video_ids(issue: dict) -> list[str]:
    candidates = []

    if issue.get("video_id"):
        candidates.append(issue["video_id"])

    candidates.extend(search_video_ids(issue["query"]))
    return list(dict.fromkeys(candidates))


def collect_first_working_video(issue: dict) -> tuple[str, str, list[dict]]:
    errors = []

    for video_id in candidate_video_ids(issue):
        try:
            title = get_video_title(video_id)
            comments = collect(
                video_id,
                max_comments=MAX_COMMENTS,
            )

            if not comments:
                errors.append(f"{video_id}: 댓글 0개")
                continue

            return video_id, title, comments

        except Exception as error:
            errors.append(f"{video_id}: {error}")

    raise RuntimeError(
        f"[{issue['label']}] 댓글 수집 가능한 영상을 찾지 못했습니다.\n"
        + "\n".join(errors)
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = []

    for issue in ISSUES:
        print()
        print("=" * 70)
        print(f"수집 시작: {issue['label']}")

        try:
            video_id, video_title, comments = collect_first_working_video(issue)

            validate_comments(
                comments,
                SCHEMA_PATH,
            )

            output_path = OUTPUT_DIR / f"{issue['slug']}.json"

            with output_path.open("w", encoding="utf-8") as file:
                json.dump(
                    comments,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            index.append(
                {
                    "slug": issue["slug"],
                    "label": issue["label"],
                    "video_id": video_id,
                    "video_title": video_title,
                    "comment_count": len(comments),
                    "comments_file": str(output_path).replace("\\", "/"),
                }
            )

            print(f"영상 제목: {video_title}")
            print(f"video_id: {video_id}")
            print(f"댓글 수: {len(comments)}")
            print("스키마 검증: PASS")
            print(f"저장: {output_path}")

        except Exception as error:
            print(f"실패: {error}")

    index_path = OUTPUT_DIR / "issues.json"

    with index_path.open("w", encoding="utf-8") as file:
        json.dump(
            index,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print(f"완료: {len(index)}개 이슈 수집")
    print(f"메인페이지용 인덱스: {index_path}")


if __name__ == "__main__":
    main()
