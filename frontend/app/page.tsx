"use client";

import { useState } from "react";
import sampleData from "@/data/sample.opinionmap.json";
import OpinionMapOverlay from "./components/OpinionMapOverlay";
import type { OpinionMap } from "./types";

// 실제 작동하는 3개 토픽 (sample JSON 의 key 와 매칭)
const REAL_TOPICS = [
  {
    key: "politics",
    label: "주 4일제,\n도입해야 하나",
    tag: "정치",
    bg: "bg-gradient-to-br from-rose-100 to-orange-100",
    text: "text-rose-900",
  },
  {
    key: "tech",
    label: "신제품 가격 인상,\n정당한가",
    tag: "테크",
    bg: "bg-gradient-to-br from-sky-100 to-indigo-100",
    text: "text-indigo-900",
  },
  {
    key: "movie",
    label: "화제작,\n명작 vs 과대평가",
    tag: "영화",
    bg: "bg-gradient-to-br from-emerald-100 to-teal-100",
    text: "text-emerald-900",
  },
] as const;

// 그리드를 채우는 더미 타일 (아직 분석 안 된 토픽 — Coming soon)
const DUMMY_TILES = [
  { label: "AI 규제 논쟁", tag: "정치" },
  { label: "전기차 보조금", tag: "정책" },
  { label: "리메이크 열풍", tag: "영화" },
  { label: "구독 서비스 피로", tag: "테크" },
  { label: "재택근무 존폐", tag: "노동" },
  { label: "스포일러 논란", tag: "영화" },
];

const data = sampleData as Record<string, OpinionMap>;

export default function Home() {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [url, setUrl] = useState("");

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-6 px-6 py-8 lg:flex-row">
        {/* ─── 왼쪽: 토픽 타일 그리드 ─── */}
        <main className="flex-1">
          <header className="mb-6">
            <div className="flex items-center gap-2.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo-mark.svg" alt="" width={36} height={36} />
              <h1 className="text-2xl font-bold tracking-tight uppercase" style={{
              fontFamily: "var(--font-archivo)",
              fontWeight: 700,
              transform: "scaleX(1.12)",   // width 112%
              transformOrigin: "left",
              }}>
              CommentMap</h1>
            </div>
            <p className="mt-1 text-sm text-neutral-500">
              댓글을 요약하지 않고, 논쟁의 구조를 지도로 보여줍니다.
            </p>
          </header>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            {/* 실제 작동 타일 */}
            {REAL_TOPICS.map((t) => (
              <button
                key={t.key}
                onClick={() => setOpenKey(t.key)}
                className={`group relative flex aspect-square flex-col justify-between rounded-2xl ${t.bg} ${t.text} p-5 text-left shadow-sm transition hover:scale-[1.02] hover:shadow-md`}
              >
                <span className="inline-block w-fit rounded-full bg-white/70 px-2.5 py-1 text-xs font-medium">
                  {t.tag}
                </span>
                <span className="whitespace-pre-line text-xl font-bold leading-snug">
                  {t.label}
                </span>
                <span className="text-xs font-medium opacity-70 group-hover:opacity-100">
                  논쟁 지도 보기 →
                </span>
              </button>
            ))}

            {/* 더미 타일 (Coming soon) */}
            {DUMMY_TILES.map((t, i) => (
              <div
                key={i}
                className="flex aspect-square cursor-not-allowed flex-col justify-between rounded-2xl border border-dashed border-neutral-200 bg-white p-5 text-left"
              >
                <span className="inline-block w-fit rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-400">
                  {t.tag}
                </span>
                <span className="text-xl font-bold leading-snug text-neutral-300">
                  {t.label}
                </span>
                <span className="text-xs font-medium text-neutral-300">
                  Coming soon
                </span>
              </div>
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
                <button
                  onClick={() => alert("분석 기능은 백엔드 연결 후 작동합니다 (지금은 아래 토픽 데모를 눌러보세요)")}
                  className="rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-700"
                >
                  Analyze
                </button>
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
                      onClick={() => setOpenKey(t.key)}
                      className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition hover:bg-neutral-100"
                    >
                      <span>{data[t.key].topic}</span>
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

      {/* ─── 오버레이 (타일 클릭 시) ─── */}
      {openKey && (
        <OpinionMapOverlay
          data={data[openKey]}
          onClose={() => setOpenKey(null)}
        />
      )}
    </div>
  );
}
