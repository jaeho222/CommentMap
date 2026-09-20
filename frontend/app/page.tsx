"use client";

import { useState } from "react";
import sampleData from "@/data/sample.opinionmap.json";
import OpinionMapOverlay from "./components/OpinionMapOverlay";
import type { OpinionMap } from "./types";
import { analyzeUrl, AnalyzeError } from "./lib/api";

const REAL_TOPICS = [
  {
    key: "hormuz",
    label: "호르무즈 해협 파병",
    tag: "안보/외교",
    image: "/tiles/hormuz_deployment.jpg",
  },
  {
    key: "samsung_hynix",
    label: "삼전·하이닉스 주식 현황",
    tag: "경제",
    image: "/tiles/samsung_hynix_stock.jpg",
  },
  {
    key: "asian_games",
    label: "아시안게임 운영 논란",
    tag: "스포츠",
    image: "/tiles/asian_games_operation.jpg",
  },
  {
    key: "iphone18",
    label: "아이폰 18 Pro",
    tag: "테크",
    image: "/tiles/iphone_18_pro.jpeg",
  },
  {
    key: "yeosu_expo",
    label: "여수 섬 박람회",
    tag: "지역/사회",
    image: "/tiles/yeosu_island_expo.jpg",
  },
  {
    key: "missile",
    label: "북한 동해상 미사일 발사",
    tag: "안보",
    image: "/tiles/north_korea_missile.jpg",
  },
  {
    key: "press_conference",
    label: "대통령 대국민 기자회견",
    tag: "정치",
    image: "/tiles/president_press_conference.jpg",
  },
  {
    key: "real_estate",
    label: "오세훈 부동산 평탄화 비판",
    tag: "정치/부동산",
    image: "/tiles/real_estate_flattening.jpg",
  },
  {
    key: "newjeans",
    label: "뉴진스 복귀",
    tag: "연예",
    image: "/tiles/newjeans_return.jpg",
  },
];

const data = sampleData as Record<string, OpinionMap>;

export default function Home() {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [topic, setTopic] = useState("");
  const [liveResult, setLiveResult] = useState<OpinionMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-6 px-6 py-8 lg:flex-row">
        {/* ─── 왼쪽: 토픽 타일 그리드 ─── */}
        <main className="flex-1">
          <header className="mb-6">
            <div className="flex items-center gap-2.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo-mark.svg" alt="" width={36} height={36} />
              <h1
                className="text-2xl font-bold tracking-tight uppercase"
                style={{
                  fontFamily: "var(--font-archivo)",
                  fontWeight: 700,
                  transform: "scaleX(1.12)",
                  transformOrigin: "left",
                }}
              >
                CommentMap
              </h1>
            </div>
            <p className="mt-1 text-sm text-neutral-500">
              댓글을 요약하지 않고, 논쟁의 구조를 지도로 보여줍니다.
            </p>
          </header>

          <div className="grid grid-cols-3 gap-4 md:grid-cols-3">
            {REAL_TOPICS.map((t) => (
              <button
                key={t.key}
                onClick={() => data[t.key] && setOpenKey(t.key)}
                disabled={!data[t.key]}
                className="group relative aspect-square overflow-hidden rounded-2xl text-left transition hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {/* 배경 사진 */}
                <img
                  src={t.image}
                  alt={t.label}
                  className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-105"
                />
                {/* 가독성용 어두운 그라데이션 오버레이 */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/0" />
                {/* 텍스트 */}
                <div className="relative z-10 flex h-full flex-col justify-between p-6">
                  <span className="text-xs font-mono uppercase tracking-wide text-white/80">
                    {t.tag}
                  </span>
                  <span className="text-xl font-semibold text-white">
                    {t.label}
                    {!data[t.key] && (
                      <span className="ml-2 text-xs font-normal text-white/70">
                        (준비중)
                      </span>
                    )}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </main>

        {/* ─── 오른쪽: 흰 사이드 패널 ─── */}
        <aside className="w-full shrink-0 lg:w-80">
          <div className="sticky top-8 rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm">
            {/* URL 직접 입력 */}
            <div>
              <h2 className="text-sm font-semibold">직접 분석하기</h2>
              <p className="mt-1 text-xs text-neutral-500">
                YouTube URL을 넣으면 댓글 논쟁을 분석합니다.
              </p>
              <div className="mt-3 flex flex-col gap-2">
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                />
                <input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="주제 (선택, 예: 아이폰 18 Pro 가격 논란)"
                  className="w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                />
                <button
                  onClick={async () => {
                    if (!url.trim()) return;
                    setLoading(true);
                    setError(null);
                    try {
                      const result = await analyzeUrl(url.trim(), {
                        topic: topic.trim(),
                      });
                      setLiveResult(result);
                    } catch (e) {
                      setError(
                        e instanceof AnalyzeError
                          ? e.message
                          : "알 수 없는 오류가 발생했습니다."
                      );
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={loading || !url.trim()}
                  className="rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {loading ? "분석 중... (1~2분 소요)" : "Analyze"}
                </button>
                {error && <p className="text-xs text-red-600">{error}</p>}
              </div>
            </div>

            <hr className="my-5 border-neutral-100" />

            {/* 토픽 리스트 */}
            <div>
              <h2 className="mb-3 text-sm font-semibold">데모 토픽</h2>
              <ul className="flex flex-col gap-1">
                {REAL_TOPICS.map((t) => (
                  <li key={t.key}>
                    <button
                      onClick={() => data[t.key] && setOpenKey(t.key)}
                      disabled={!data[t.key]}
                      className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <span>{data[t.key]?.topic ?? t.label}</span>
                      <span className="text-neutral-400">→</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <hr className="my-5 border-neutral-100" />

            {/* 인디케이터 미리보기 */}
            <div className="flex flex-col gap-2 text-xs">
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 px-3 py-2">
                <span>🔥</span>
                <span className="text-neutral-600">가장 큰 논쟁을 자동 탐지</span>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 px-3 py-2">
                <span>👀</span>
                <span className="text-neutral-600">인기 댓글에 묻힌 숨은 의견</span>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 px-3 py-2">
                <span>⚡</span>
                <span className="text-neutral-600">떠오르는 쟁점 추적</span>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* ─── 오버레이 ─── */}
      {openKey && (
        <OpinionMapOverlay data={data[openKey]} onClose={() => setOpenKey(null)} />
      )}
      {liveResult && (
        <OpinionMapOverlay data={liveResult} onClose={() => setLiveResult(null)} />
      )}
    </div>
  );
}