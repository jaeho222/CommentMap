# 2026-wanted
원티드 챔피언쉽

Collector

YouTube URL을 입력하면 댓글을 수집·전처리하여
contracts/comments.schema.json 형식의 comments.json을 생성합니다.

설치

프로젝트 루트에서 가상환경을 활성화한 뒤 필요한 패키지를 설치합니다.

pip install -r requirements.txt

프로젝트 루트에 .env 파일을 만들고 YouTube Data API v3 키를 설정합니다.

YOUTUBE_API_KEY=YOUR_API_KEY

.env는 GitHub에 커밋하지 않습니다.

테스트

pytest -q

댓글 수집

처음에는 댓글 100개만 테스트하는 것을 권장합니다.

python run_collector.py "YOUTUBE_URL" --max-comments 100

전체 수집:

python run_collector.py "YOUTUBE_URL"

정상 실행되면 프로젝트 루트에 comments.json이 생성되고,
contracts/comments.schema.json 검증까지 통과합니다.

Python에서 직접 사용

from collector import collect

comments = collect("YOUTUBE_URL")

출력 형식

[
  {
    "id": "Ugx...",
    "text": "댓글 내용",
    "likes": 12,
    "time": "2026-09-19T03:20:00Z"
  }
]

각 필드는 다음 의미입니다.

필드

설명

id

YouTube 댓글 고유 ID

text

전처리된 댓글 본문

likes

댓글 좋아요 수

time

댓글 작성 시각(ISO 8601)

전처리

Collector에서는 다음 항목을 제거합니다.

중복 댓글

스팸성 댓글

이모지만 있는 댓글

너무 짧은 댓글

링크만 있거나 링크가 과도하게 포함된 댓글

파일 구성

collector/youtube.py — YouTube URL 파싱 및 댓글 수집

collector/clean.py — 댓글 전처리

collector/__init__.py — collect(url) 제공

run_collector.py — comments.json 생성

test_collector.py — Collector 테스트

토픽 분류, 클러스터링, 주장/반론 분석은 analyzer/에서 처리합니다.

Analyzer

Collector에서 전달받은 댓글을 분석하여
contracts/opinionmap.schema.json 형식의 OpinionMap을 생성합니다.

분석 과정

댓글 전처리
→ Claude를 이용한 개별 claim 추출
→ E5 Embedding을 이용한 유사 claim 후보 생성
→ Claude를 이용한 동일 의견 판정 및 병합
→ 각 claim의 stance(positive / negative / neutral) 분석
→ claim 사이 support / attack / related 관계 분석
→ 전체 댓글 분포와 인기댓글 분포를 비교한 hidden opinion 분석
→ OpinionMap JSON 생성

주요 파일

analyzer/preprocess.py — 분석 전 댓글 전처리

analyzer/embed.py — E5 Embedding

analyzer/claim_extractor.py — 댓글에서 claim 추출

analyzer/claim_matcher.py — 동일 의견 판정

analyzer/claim_merger.py — 동일한 claim 병합

analyzer/claim_builder.py — 최종 claim 구성 및 대표댓글 연결

analyzer/stance_classifier.py — claim의 stance 분석

analyzer/relation_builder.py — claim 사이 관계 생성

analyzer/relation_matcher.py — support / attack / related 관계 판정

analyzer/hidden.py — 전체 댓글과 인기댓글 분포를 비교하여 hidden opinion 탐색

analyzer/claude_client.py — Claude API 연결

analyzer/cache.py — API 분석 결과 캐시

analyzer/__init__.py — 전체 analyze() 파이프라인

실시간 분석 연결

pipeline.py — URL 입력부터 Collector와 Analyzer를 연결하는 전체 파이프라인

api.py — 프론트엔드에서 분석을 요청할 수 있는 API

API 키는 .env에 저장하며 GitHub에 커밋하지 않습니다.