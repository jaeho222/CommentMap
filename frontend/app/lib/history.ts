import type { OpinionMap } from "../types";

/**
 * 사용자가 직접 분석한 결과를 이 브라우저(localStorage)에 저장해서
 * 데모 토픽 카드 옆에 '내 분석' 카드로 다시 띄우기 위한 저장소.
 *
 * - 서버/DB/로그인 없이 동작한다.
 * - 저장된 카드를 클릭하면 /analyze 를 다시 호출하지 않고 저장해둔 JSON을 그대로 쓴다.
 * - 같은 영상을 다시 분석하면 카드를 새로 만들지 않고 기존 카드를 최신 결과로 교체한다.
 */

const STORAGE_KEY = "commentmap_history_v1";
const MAX_ENTRIES = 12;

export type HistoryEntry = {
  /** 영상 ID(있으면) 또는 URL. 중복 판단 기준 */
  id: string;
  url: string;
  topic: string;
  /** YouTube 썸네일 URL (영상 ID를 못 찾으면 빈 문자열) */
  thumbnail: string;
  analyzedAt: string; // ISO
  data: OpinionMap;
};

/** YouTube URL에서 영상 ID 추출 (watch?v=, youtu.be/, shorts/, embed/ 지원) */
export function extractVideoId(url: string): string | null {
  try {
    const u = new URL(url.trim());
    const host = u.hostname.replace(/^www\./, "");

    if (host === "youtu.be") {
      const id = u.pathname.split("/")[1];
      return id || null;
    }
    if (host.endsWith("youtube.com")) {
      const v = u.searchParams.get("v");
      if (v) return v;
      const parts = u.pathname.split("/").filter(Boolean); // ["shorts","ID"] 등
      if (parts.length >= 2 && ["shorts", "embed", "live", "v"].includes(parts[0])) {
        return parts[1];
      }
    }
    return null;
  } catch {
    return null; // URL 형식이 아니면 그냥 null
  }
}

export function thumbnailFor(url: string): string {
  const id = extractVideoId(url);
  return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : "";
}

function isBrowser() {
  return typeof window !== "undefined";
}

function readRaw(): HistoryEntry[] {
  if (!isBrowser()) return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return []; // 저장값이 깨졌으면 빈 기록으로 취급 (화면이 죽으면 안 되니까)
  }
}

function writeRaw(entries: HistoryEntry[]): boolean {
  if (!isBrowser()) return false;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
    return true;
  } catch {
    return false; // 용량 초과 등
  }
}

/** 최신순 목록 */
export function loadHistory(): HistoryEntry[] {
  return [...readRaw()].sort(
    (a, b) => new Date(b.analyzedAt).getTime() - new Date(a.analyzedAt).getTime()
  );
}

/** 분석 성공 직후 호출. 같은 영상이면 기존 카드를 최신 결과로 교체 */
export function saveToHistory(url: string, topic: string, data: OpinionMap) {
  if (!isBrowser()) return;

  const trimmedUrl = url.trim();
  const entry: HistoryEntry = {
    id: extractVideoId(trimmedUrl) ?? trimmedUrl,
    url: trimmedUrl,
    topic: topic.trim() || data.topic,
    thumbnail: thumbnailFor(trimmedUrl),
    analyzedAt: new Date().toISOString(),
    data,
  };

  let entries = readRaw().filter((e) => e.id !== entry.id); // 중복 제거 = 교체
  entries = [entry, ...entries].slice(0, MAX_ENTRIES);

  // 용량 초과로 저장이 실패하면 오래된 것부터 버리며 재시도
  while (entries.length > 0 && !writeRaw(entries)) {
    entries = entries.slice(0, -1);
  }
}

export function removeFromHistory(id: string) {
  writeRaw(readRaw().filter((e) => e.id !== id));
}
