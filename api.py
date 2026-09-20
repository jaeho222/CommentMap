from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline import analyze_url


app = FastAPI(
    title="CommentMap API",
    version="1.0.0",
)


# 개발 중 Next.js 프론트엔드에서
# Python API를 호출할 수 있도록 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://comment-map-one.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=1,
        description="분석할 YouTube URL",
    )

    max_comments: int | None = Field(
        default=100,
        ge=1,
        le=1000,
        description="수집할 최대 댓글 수",
    )

    topic: str = Field(
        default="",
        description="영상 제목 또는 분석 주제",
    )


@app.get("/health")
def health() -> dict:
    """
    서버가 정상적으로 실행 중인지 확인한다.
    외부 API를 호출하지 않는다.
    """

    return {
        "status": "ok",
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    """
    YouTube URL을 받아
    Collector -> Analyzer 파이프라인을 실행하고
    OpinionMap을 반환한다.
    """

    try:
        return analyze_url(
            url=request.url,
            max_comments=request.max_comments,
            topic=request.topic,
            use_api=True,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error