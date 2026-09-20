"use client";

import { useEffect, useState } from "react";

/**
 * 첫 화면(인트로 슬라이드).
 * - "계속하기" 버튼, Enter / Space / → 키로 넘어감 (PPT 넘기듯)
 * - 넘길 때 화면 전체가 위로 밀려 올라가며 본 페이지가 드러남
 * - 같은 탭에서 새로고침하면 다시 안 뜸 (sessionStorage). 새 탭/새 방문이면 다시 뜸.
 */

const SEEN_KEY = "commentmap_intro_seen";
const EXIT_MS = 700;

// 배경에 깔리는 장식용 '의견 지도' (노드 + 연결선)
const NODES = [
  { x: 14, y: 22, r: 10, c: "#0284c7" },
  { x: 30, y: 12, r: 6, c: "#71717a" },
  { x: 24, y: 40, r: 7, c: "#e11d48" },
  { x: 78, y: 18, r: 9, c: "#e11d48" },
  { x: 88, y: 36, r: 6, c: "#0284c7" },
  { x: 70, y: 34, r: 5, c: "#71717a" },
  { x: 12, y: 74, r: 7, c: "#e11d48" },
  { x: 28, y: 86, r: 9, c: "#0284c7" },
  { x: 82, y: 78, r: 10, c: "#0284c7" },
  { x: 66, y: 88, r: 6, c: "#e11d48" },
  { x: 92, y: 62, r: 5, c: "#71717a" },
];
const LINKS: [number, number, string][] = [
  [0, 1, "#a1a1aa"],
  [0, 2, "#dc2626"],
  [1, 2, "#16a34a"],
  [3, 4, "#dc2626"],
  [3, 5, "#16a34a"],
  [4, 5, "#a1a1aa"],
  [6, 7, "#dc2626"],
  [8, 9, "#dc2626"],
  [8, 10, "#16a34a"],
];

export default function IntroScreen({ onDone }: { onDone: () => void }) {
  const [leaving, setLeaving] = useState(false);

  function next() {
    if (leaving) return;
    setLeaving(true);
    try {
      window.sessionStorage.setItem(SEEN_KEY, "1");
    } catch {
      // 저장 못 해도 동작에는 문제 없음
    }
    window.setTimeout(onDone, EXIT_MS);
  }

  // 키보드로도 넘기기 (Enter, Space, →)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") {
        e.preventDefault();
        next();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leaving]);

  // 인트로가 떠 있는 동안 뒤 페이지 스크롤 막기
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  return (
    <div
      className="intro-root fixed inset-0 z-[60] flex items-center justify-center overflow-hidden bg-neutral-950 px-6 text-white"
      style={{
        transform: leaving ? "translateY(-100%)" : "translateY(0)",
        transition: `transform ${EXIT_MS}ms cubic-bezier(0.76, 0, 0.24, 1)`,
      }}
    >
      <style>{`
        @keyframes intro-rise {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes intro-fade { from { opacity: 0; } to { opacity: 1; } }
        @keyframes intro-draw { from { stroke-dashoffset: 100; } to { stroke-dashoffset: 0; } }
        @keyframes intro-drift {
          0%, 100% { transform: translateY(0); }
          50%      { transform: translateY(-6px); }
        }
        .intro-rise { opacity: 0; animation: intro-rise 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
        .intro-bg   { opacity: 0; animation: intro-fade 1.6s ease forwards; }
        .intro-line { stroke-dasharray: 100; stroke-dashoffset: 100; animation: intro-draw 1.4s ease 0.4s forwards; }
        .intro-node { animation: intro-drift 6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
        @media (prefers-reduced-motion: reduce) {
          .intro-rise, .intro-bg { opacity: 1; animation: none; }
          .intro-line { stroke-dashoffset: 0; animation: none; }
          .intro-node { animation: none; }
          .intro-root { transition: none !important; }
        }
      `}</style>

      {/* 배경 장식: 흐릿한 의견 지도 */}
      <svg
        className="intro-bg pointer-events-none absolute inset-0 h-full w-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {LINKS.map(([a, b, color], i) => (
          <line
            key={i}
            className="intro-line"
            x1={NODES[a].x}
            y1={NODES[a].y}
            x2={NODES[b].x}
            y2={NODES[b].y}
            stroke={color}
            strokeOpacity={0.45}
            strokeWidth={0.25}
            pathLength={100}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="intro-bg pointer-events-none absolute inset-0" aria-hidden="true">
        {NODES.map((n, i) => (
          <span
            key={i}
            className="intro-node absolute rounded-full"
            style={{
              left: `${n.x}%`,
              top: `${n.y}%`,
              width: n.r * 2,
              height: n.r * 2,
              marginLeft: -n.r,
              marginTop: -n.r,
              background: n.c,
              opacity: 0.35,
              boxShadow: `0 0 24px ${n.c}`,
              animationDelay: `${i * 0.4}s`,
            }}
          />
        ))}
      </div>
      {/* 가운데 글씨가 잘 보이게 중앙을 살짝 어둡게 */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(10,10,10,0.9) 0%, rgba(10,10,10,0.6) 45%, rgba(10,10,10,0) 80%)",
        }}
        aria-hidden="true"
      />

      {/* 본문 */}
      <div className="relative z-10 flex flex-col items-center text-center">
        <p
          className="intro-rise break-keep text-lg font-medium text-white/70 sm:text-2xl"
          style={{ animationDelay: "0.2s" }}
        >
          댓글의 여론을 한눈에,
        </p>

        <div
          className="intro-rise mt-4 flex items-center gap-3 sm:mt-5 sm:gap-4"
          style={{ animationDelay: "0.45s" }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-mark.svg"
            alt=""
            className="h-10 w-10 sm:h-16 sm:w-16"
            style={{ filter: "invert(1)" }}
          />
          <h1
            className="text-4xl font-bold uppercase tracking-tight sm:text-7xl"
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

        <p
          className="intro-rise mt-5 max-w-md break-keep text-sm leading-relaxed text-white/55 sm:text-base"
          style={{ animationDelay: "0.7s" }}
        >
          댓글을 요약하지 않고, 논쟁의 구조를 지도로 보여줍니다.
        </p>

        <button
          onClick={next}
          autoFocus
          className="intro-rise group mt-10 flex items-center gap-2 rounded-full bg-white px-7 py-3 text-sm font-semibold text-neutral-900 transition hover:bg-neutral-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-950 sm:text-base"
          style={{ animationDelay: "1s" }}
        >
          계속하기
          <span className="transition-transform group-hover:translate-x-1">→</span>
        </button>

        <p
          className="intro-rise mt-4 hidden text-xs text-white/35 sm:block"
          style={{ animationDelay: "1.3s" }}
        >
          Enter 키로도 넘어갈 수 있어요
        </p>
      </div>
    </div>
  );
}

/** 이 탭에서 이미 인트로를 봤는지 */
export function hasSeenIntro(): boolean {
  try {
    return window.sessionStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return false;
  }
}
