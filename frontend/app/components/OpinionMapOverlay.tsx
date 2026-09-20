"use client";

import { useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import type { OpinionMap, Claim, Relation, RelationType } from "../types";
import { AnalyzeError } from "../lib/api";

// stance 별 노드 색 (밝은 배경 모던 팔레트)
const STANCE_STYLE: Record<string, { bg: string; border: string }> = {
  positive: { bg: "#e0f2fe", border: "#0284c7" }, // 파랑
  negative: { bg: "#ffe4e6", border: "#e11d48" }, // 빨강
  neutral: { bg: "#f4f4f5", border: "#71717a" }, // 회색
};

// relation 별 엣지 색
const RELATION_STYLE: Record<RelationType, { stroke: string; label: string }> = {
  support: { stroke: "#16a34a", label: "지지" },
  attack: { stroke: "#dc2626", label: "반박" },
  related: { stroke: "#a1a1aa", label: "연관" },
};

// 처음에 보여줄 핵심 주장 개수 / 한 번 클릭할 때 펼쳐지는 최대 개수
const CORE_SIZE = 10;
const EXPAND_BATCH = 8;

// ── 핵심 주장 고르기: 댓글 수(count)가 주 기준, 연결 강도는 동점일 때만 보조 ──
// count 1~2짜리인데 '연관' 선만 잔뜩 걸린 노드가 상위로 뽑히는 걸 막기 위해
// count 가중치를 크게 두고 degree는 상한(8)을 둬서 타이브레이커 정도로만 반영.
function computeCoreIds(data: OpinionMap, limit: number): Set<string> {
  const degree: Record<string, number> = {};
  for (const r of data.relations) {
    const w = r.type === "related" ? 1 : 2; // 지지/반박이 연관보다 중요
    degree[r.from] = (degree[r.from] ?? 0) + w;
    degree[r.to] = (degree[r.to] ?? 0) + w;
  }
  const scored = data.claims.map((c) => ({
    id: c.id,
    score: c.count * 20 + Math.min(degree[c.id] ?? 0, 8),
  }));
  scored.sort((a, b) => b.score - a.score);
  return new Set(scored.slice(0, Math.min(limit, scored.length)).map((s) => s.id));
}

// id -> 연결된 다른 claim id 목록
function buildNeighborMap(relations: Relation[]): Record<string, string[]> {
  const map: Record<string, string[]> = {};
  const add = (a: string, b: string) => {
    (map[a] ??= []).push(b);
  };
  for (const r of relations) {
    add(r.from, r.to);
    add(r.to, r.from);
  }
  return map;
}

type Pt = { x: number; y: number; vx: number; vy: number };

// 가벼운 force-directed 레이아웃 (외부 라이브러리 없이 직접 구현)
// - 서로 밀어내고(반발력), 연결된 것끼리는 당기고(스프링), 중앙으로 살짝 모음
function forceLayout(ids: string[], edges: { from: string; to: string }[]): Record<string, Pt> {
  const W = 900;
  const H = 640;
  const pos: Record<string, Pt> = {};
  ids.forEach((id, i) => {
    const angle = (2 * Math.PI * i) / Math.max(ids.length, 1);
    const r = 60 + Math.random() * 40;
    pos[id] = {
      x: W / 2 + r * Math.cos(angle) * (i === 0 ? 0 : 3),
      y: H / 2 + r * Math.sin(angle) * (i === 0 ? 0 : 3),
      vx: 0,
      vy: 0,
    };
  });

  const validEdges = edges.filter((e) => pos[e.from] && pos[e.to]);
  const iterations = 220;
  const repulsion = 15000;
  const springLen = 170;
  const springK = 0.02;
  const damping = 0.82;

  for (let it = 0; it < iterations; it++) {
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a = pos[ids[i]];
        const b = pos[ids[j]];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distSq = Math.max(dx * dx + dy * dy, 1);
        const dist = Math.sqrt(distSq);
        const force = repulsion / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
    }
    for (const e of validEdges) {
      const a = pos[e.from];
      const b = pos[e.to];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = springK * (dist - springLen);
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }
    for (const id of ids) {
      const p = pos[id];
      p.vx += (W / 2 - p.x) * 0.0015;
      p.vy += (H / 2 - p.y) * 0.0015;
      p.vx *= damping;
      p.vy *= damping;
      p.x += p.vx;
      p.y += p.vy;
    }
  }
  return pos;
}

function buildNodes(claims: Claim[], visibleIds: Set<string>, coreIds: Set<string>): Node[] {
  const shown = claims.filter((c) => visibleIds.has(c.id));
  const positions = forceLayout(
    shown.map((c) => c.id),
    [] // 엣지는 buildEdges에서 별도로 넣음 (아래 컴포넌트에서 relations로 다시 계산)
  );
  return shown.map((c) => {
    const p = positions[c.id];
    // 원형 대신 부드러운 사각형: 너비 고정, 높이는 내용에 맞춰 자동으로 늘어남
    const width = 150 + Math.min(c.count * 4, 40);
    const style = STANCE_STYLE[c.stance] ?? STANCE_STYLE.neutral;
    const isCore = coreIds.has(c.id);
    return {
      id: c.id,
      position: { x: p.x, y: p.y },
      data: { label: `${c.text}\n(${c.count.toLocaleString()})` },
      style: {
        width,
        minHeight: 64,
        borderRadius: 14,
        background: style.bg,
        border: `${isCore ? 3 : 2}px solid ${style.border}`,
        fontSize: 12,
        fontWeight: 600,
        lineHeight: 1.35,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center" as const,
        padding: "10px 12px",
        whiteSpace: "pre-line" as const,
        color: "#1f2937",
        cursor: "pointer",
      },
    };
  });
}

export default function OpinionMapOverlay({
  data,
  onClose,
  onAnalyze,
}: {
  data: OpinionMap;
  onClose: () => void;
  /** URL(+ 선택적 주제)을 받아 실제 분석을 돌리는 함수. 성공하면 알아서 새 결과 화면으로 전환됨. */
  onAnalyze?: (url: string, topic: string) => Promise<void>;
}) {
  const [selected, setSelected] = useState<Claim | null>(null);
  const [innerUrl, setInnerUrl] = useState("");
  const [innerTopic, setInnerTopic] = useState("");
  const [innerLoading, setInnerLoading] = useState(false);
  const [innerError, setInnerError] = useState<string | null>(null);

  async function handleInnerAnalyze() {
    if (!innerUrl.trim() || !onAnalyze) return;
    setInnerLoading(true);
    setInnerError(null);
    try {
      await onAnalyze(innerUrl.trim(), innerTopic.trim());
      // 성공하면 부모가 새 데이터로 오버레이를 다시 그려주므로 여기선 따로 할 일 없음
    } catch (e) {
      setInnerError(
        e instanceof AnalyzeError ? e.message : "알 수 없는 오류가 발생했습니다."
      );
    } finally {
      setInnerLoading(false);
    }
  }

  const claimById = useMemo(() => {
    const m: Record<string, Claim> = {};
    data.claims.forEach((c) => (m[c.id] = c));
    return m;
  }, [data]);

  const neighborMap = useMemo(() => buildNeighborMap(data.relations), [data]);

  const coreIds = useMemo(() => computeCoreIds(data, CORE_SIZE), [data]);

  const [visibleIds, setVisibleIds] = useState<Set<string>>(coreIds);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // 토픽(data)이 바뀌면 핵심 주장만 보이는 상태로 리셋
  useEffect(() => {
    setVisibleIds(coreIds);
    setExpandedIds(new Set());
    setSelected(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.topic]);

  function handleNodeClick(id: string) {
    const c = claimById[id];
    if (c) setSelected(c);

    if (expandedIds.has(id)) return; // 이미 펼친 노드는 다시 안 펼침

    const neighbors = neighborMap[id] ?? [];
    const candidates = neighbors
      .filter((nid) => !visibleIds.has(nid))
      .sort((a, b) => (claimById[b]?.count ?? 0) - (claimById[a]?.count ?? 0))
      .slice(0, EXPAND_BATCH);

    if (candidates.length > 0) {
      setVisibleIds((prev) => {
        const next = new Set(prev);
        candidates.forEach((nid) => next.add(nid));
        return next;
      });
    }
    setExpandedIds((prev) => new Set(prev).add(id));
  }

  function resetToCore() {
    setVisibleIds(coreIds);
    setExpandedIds(new Set());
    setSelected(null);
  }

  const nodes = useMemo(
    () => buildNodes(data.claims, visibleIds, coreIds),
    [data, visibleIds, coreIds]
  );

  const edges: Edge[] = useMemo(
    () =>
      data.relations
        .filter((r) => visibleIds.has(r.from) && visibleIds.has(r.to))
        .map((r, i) => {
          const s = RELATION_STYLE[r.type];
          return {
            id: `e${i}`,
            source: r.from,
            target: r.to,
            label: s.label,
            animated: r.type === "attack",
            style: { stroke: s.stroke, strokeWidth: 2 },
            labelStyle: { fill: s.stroke, fontSize: 10, fontWeight: 600 },
            markerEnd: { type: MarkerType.ArrowClosed, color: s.stroke },
          };
        }),
    [data, visibleIds]
  );

  // 가장 큰 논쟁 / 숨은 의견은 전체 데이터 기준 (표시 여부와 무관)
  const biggest = [...data.claims].sort((a, b) => b.count - a.count)[0];
  const hidden = data.hidden_opinions[0];

  const hiddenCount = data.claims.length - visibleIds.size;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex h-[85vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        {/* 헤더 */}
        <div className="flex items-center justify-between border-b border-neutral-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold">{data.topic}</h2>
            {data.meta && (
              <p className="text-xs text-neutral-500">
                {data.meta.total_comments?.toLocaleString()} comments ·{" "}
                {data.claims.length} claims
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-sm text-neutral-500 transition hover:bg-neutral-100"
          >
            ✕ 닫기
          </button>
        </div>

        {/* 본문: 그래프 + 우측 상세 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 그래프 */}
          <div className="relative flex-1">
            <ReactFlow
              key={visibleIds.size /* 노드 집합 바뀌면 fitView 다시 */}
              nodes={nodes}
              edges={edges}
              onNodeClick={(_, node) => handleNodeClick(node.id)}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#e5e7eb" gap={20} />
              <Controls showInteractive={false} />
            </ReactFlow>

            {/* 범례 */}
            <div className="absolute left-4 top-4 flex flex-col gap-1 rounded-lg bg-white/90 px-3 py-2 text-xs shadow">
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-green-600" /> 지지
              </span>
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-red-600" /> 반박
              </span>
              <span className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-neutral-400" /> 연관
              </span>
            </div>

            {/* 표시 개수 + 초기화 */}
            <div className="absolute right-4 top-4 flex items-center gap-2 rounded-lg bg-white/90 px-3 py-2 text-xs shadow">
              <span className="text-neutral-500">
                핵심 주장 {visibleIds.size}개 표시 중
                {hiddenCount > 0 && ` · 나머지 ${hiddenCount}개는 클릭해서 펼치기`}
              </span>
              {visibleIds.size > coreIds.size && (
                <button
                  onClick={resetToCore}
                  className="rounded bg-neutral-100 px-2 py-1 font-medium text-neutral-600 hover:bg-neutral-200"
                >
                  핵심만 보기
                </button>
              )}
            </div>
          </div>

          {/* 우측 상세 패널 */}
          <div className="w-80 shrink-0 overflow-y-auto border-l border-neutral-100 p-5">
            {selected ? (
              <div>
                <button
                  onClick={() => setSelected(null)}
                  className="mb-3 text-xs text-neutral-400 hover:text-neutral-600"
                >
                  ← 인사이트로 돌아가기
                </button>
                <h3 className="text-base font-bold">{selected.text}</h3>
                <p className="mt-1 text-xs text-neutral-500">
                  {selected.count.toLocaleString()}개 댓글 · {selected.stance}
                </p>
                <h4 className="mt-4 mb-2 text-xs font-semibold text-neutral-400">
                  실제 대표 댓글
                </h4>
                <ul className="flex flex-col gap-2">
                  {selected.sample_comments.map((c, i) => (
                    <li
                      key={i}
                      className="rounded-lg bg-neutral-50 px-3 py-2 text-sm text-neutral-700"
                    >
                      "{c}"
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <h3 className="text-sm font-semibold">이 댓글창의 인사이트</h3>

                <div className="rounded-xl border border-neutral-100 p-3">
                  <p className="text-xs font-medium text-neutral-400">
                    🔥 가장 큰 논쟁
                  </p>
                  <p className="mt-1 text-sm font-semibold">{biggest.text}</p>
                  <p className="text-xs text-neutral-500">
                    {biggest.count.toLocaleString()}개 댓글
                  </p>
                </div>

                {hidden && (
                  <div className="rounded-xl border border-neutral-100 p-3">
                    <p className="text-xs font-medium text-neutral-400">
                      👀 숨은 의견
                    </p>
                    <p className="mt-1 text-sm font-semibold">{hidden.text}</p>
                    <p className="text-xs text-neutral-500">
                      전체 {Math.round(hidden.share * 100)}% · 인기댓글{" "}
                      {Math.round(hidden.top_share * 100)}%
                    </p>
                  </div>
                )}

                <p className="text-xs text-neutral-400">
                  진하게 테두리 된 노드가 핵심 주장이에요. 노드를 클릭하면 연결된
                  주장이 펼쳐지고, 대표 댓글도 볼 수 있어요.
                </p>

                {/* 맵 안에서 다른 URL 직접 입력 */}
                <div className="mt-2 border-t border-neutral-100 pt-4">
                  <p className="mb-2 text-xs font-semibold">
                    다른 영상 분석하기
                  </p>
                  <input
                    value={innerUrl}
                    onChange={(e) => setInnerUrl(e.target.value)}
                    placeholder="YouTube URL"
                    className="mb-2 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                  />
                  <input
                    value={innerTopic}
                    onChange={(e) => setInnerTopic(e.target.value)}
                    placeholder="주제 (선택)"
                    className="mb-2 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm outline-none focus:border-neutral-400"
                  />
                  <button
                    onClick={handleInnerAnalyze}
                    disabled={innerLoading || !innerUrl.trim()}
                    className="w-full rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {innerLoading ? "분석 중... (1~2분 소요)" : "Analyze"}
                  </button>
                  {innerError && (
                    <p className="mt-2 text-xs text-red-600">{innerError}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
