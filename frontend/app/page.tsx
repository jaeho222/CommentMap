"use client";

import { useEffect, useState, type MouseEvent as ReactMouseEvent } from "react";
import OpinionMapOverlay from "./components/OpinionMapOverlay";
import IntroScreen, { hasSeenIntro } from "./components/IntroScreen";
import {
  loadHistory,
  saveToHistory,
  removeFromHistory,
  type HistoryEntry,
} from "./lib/history";
import type { OpinionMap } from "./types";
import { analyzeUrl, AnalyzeError } from "./lib/api";
import { fetchTopic, fetchTopicIndex, TopicLoadError, type TopicMeta } from "./lib/topics";

export default function Home() {
  // ─── 데모 토픽 (public/data 에서 불러옴) ───
  const [topics, setTopics] = useState<TopicMeta[]>([]);
  const [topicCache, setTopicCache] = useState<Record<string, OpinionMap>>({});
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [topicError, setTopicError] = useState<string | null>(null);

  // ─── 라이브 분석 (URL 입력) ───
  const [url, setUrl] = useState("");
  const [topic, setTopic] = useState("");
  const [liveResult, setLiveResult] = useState<OpinionMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── 내가 분석한 결과 (이 브라우저에만 저장) ───
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  // ─── 첫 화면(인트로) ───
  const [showIntro, setShowIntro] = useState(true);

  // 처음 한 번: 토픽 목록 + 저장된 분석 기록 불러오기
  useEffect(() => {
    fetchTopicIndex()
      .then(setTopics)
      .catch((e) =>
        setTopicError(e instanceof TopicLoadError ? e.message : "토픽 목록 오류")
      );
    setHistory(loadHistory());
    // 같은 탭에서 이미 봤으면(새로고침 등) 인트로 건너뛰기
    if (hasSeenIntro()) setShowIntro(false);
  }, []);

  // 타일 클릭: 해당 토픽 데이터만 불러오기 (한 번 불러온 건 캐시)
  async function openTopic(key: string) {
    if (loadingKey) return;
    if (topicCache[key]) {
      setOpenKey(key);
      return;
    }
    setLoadingKey(key);
    setTopicError(null);
    try {
      const data = await fetchTopic(key);
      setTopicCache((prev) => ({ ...prev, [key]: data }));
      setOpenKey(key);
    } catch (e) {
      setTopicError(e instanceof TopicLoadError ? e.message : "토픽을 불러오지 못했습니다.");
    } finally {
      setLoadingKey(null);
    }
  }

  async function runAnalyze() {
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeUrl(url.trim(), { topic: topic.trim() });
      setLiveResult(result);
      saveToHistory(url.trim(), topic.trim(), result); // 카드로 저장 (같은 영상이면 교체)
      setHistory(loadHistory());
    } catch (e) {
      setError(e instanceof AnalyzeError ? e.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  // 그래프 오버레이 안(다른 영상 분석하기)에서 호출되는 함수.
  // 성공하면 지금 열려있는 오버레이를 새 분석 결과로 교체한다.
  async function analyzeFromOverlay(inputUrl: string, inputTopic: string) {
    const result = await analyzeUrl(inputUrl, { topic: inputTopic });
    setOpenKey(null); // 데모 토픽 오버레이였다면 닫고
    setLiveResult(result); // 라이브 결과 오버레이로 교체
    saveToHistory(inputUrl, inputTopic, result);
    setHistory(loadHistory());
  }

  // 저장된 카드 클릭: 서버 재호출 없이 저장해둔 JSON을 그대로 맵에 전달
  function openSaved(entry: HistoryEntry) {
    setLiveResult(entry.data);
  }

  function deleteSaved(e: ReactMouseEvent, id: string) {
    e.stopPropagation(); // 카드 클릭(맵 열기)으로 번지지 않게
    e.preventDefault();
    removeFromHistory(id);
    setHistory(loadHistory());
  }

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 lg:flex-row">
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
            <p className="mt-1 text-sm" style={{ color: "#000" }}>
              댓글의 여론을 한눈에
            </p>
          </header>

          {topicError && (
            <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {topicError}
            </p>
          )}

          <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3">
            {topics.map((t) => (
              <button
                key={t.key}
                onClick={() => openTopic(t.key)}
                disabled={loadingKey !== null}
                className="group relative aspect-square overflow-hidden rounded-2xl text-left transition hover:scale-[1.02] disabled:cursor-wait"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={t.image}
                  alt={t.label}
                  className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/0" />
                <div className="relative z-10 flex h-full flex-col justify-between p-3 sm:p-6">
                  <span className="text-[10px] font-mono uppercase tracking-wide text-white/80 sm:text-xs">
                    {t.tag}
                  </span>
                  <span className="break-keep text-sm font-semibold leading-snug text-white sm:text-xl">
                    {t.label}
                    {loadingKey === t.key && (
                      <span className="ml-2 text-xs font-normal text-white/70">
                        불러오는 중…
                      </span>
                    )}
                  </span>
                </div>
              </button>
            ))}

            {/* 내가 분석한 결과 카드 (데모 토픽 뒤에 붙음) */}
            {history.map((h) => (
              <div
                key={h.id}
                onClick={() => openSaved(h)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") openSaved(h);
                }}
                className="group relative aspect-square cursor-pointer overflow-hidden rounded-2xl text-left transition hover:scale-[1.02]"
              >
                {h.thumbnail ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={h.thumbnail}
                    alt={h.topic}
                    className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="absolute inset-0 bg-gradient-to-br from-neutral-700 to-neutral-900" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/0" />

                {/* 삭제 버튼 */}
                <button
                  onClick={(e) => deleteSaved(e, h.id)}
                  title="이 분석 삭제"
                  className="absolute right-2 top-2 z-20 rounded-full bg-black/50 px-2 py-0.5 text-xs text-white/70 opacity-0 transition hover:bg-black/70 hover:text-white group-hover:opacity-100"
                >
                  ✕
                </button>

                <div className="relative z-10 flex h-full flex-col justify-between p-3 sm:p-6">
                  <span className="text-[10px] font-mono uppercase tracking-wide text-white/80 sm:text-xs">
                    내 분석
                  </span>
                  <span className="break-keep text-sm font-semibold leading-snug text-white sm:text-xl">
                    {h.topic}
                    <span className="mt-0.5 block text-[10px] font-normal text-white/60 sm:text-xs">
                      {new Date(h.analyzedAt).toLocaleDateString("ko-KR", {
                        month: "numeric",
                        day: "numeric",
                      })}{" "}
                      · {h.data.claims.length} claims
                    </span>
                  </span>
                </div>
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
                <input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="주제 (선택, 예: 아이폰 18 Pro 가격 논란)"
                  className="w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                />
                <button
                  onClick={runAnalyze}
                  disabled={loading || !url.trim()}
                  className="rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-40"
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
                {topics.map((t) => (
                  <li key={t.key}>
                    <button
                      onClick={() => openTopic(t.key)}
                      disabled={loadingKey !== null}
                      className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition hover:bg-neutral-100 disabled:cursor-wait"
                    >
                      <span>{t.label}</span>
                      <span className="text-neutral-400">
                        {loadingKey === t.key ? "…" : "→"}
                      </span>
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

      {/* ─── 첫 화면(인트로) ─── */}
      {showIntro && <IntroScreen onDone={() => setShowIntro(false)} />}

      {/* ─── 오버레이 ─── */}
      {openKey && topicCache[openKey] && (
        <OpinionMapOverlay
          data={topicCache[openKey]}
          onClose={() => setOpenKey(null)}
          onAnalyze={analyzeFromOverlay}
        />
      )}
      {liveResult && (
        <OpinionMapOverlay
          data={liveResult}
          onClose={() => setLiveResult(null)}
          onAnalyze={analyzeFromOverlay}
        />
      )}
    </div>
  );
}
