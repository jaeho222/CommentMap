import type { OpinionMap } from "../types";

// analyzer(api.py)가 뜨는 주소. 로컬 개발 기준 8000번 포트.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class AnalyzeError extends Error {}

/**
 * YouTube URL을 백엔드(/analyze)로 보내서
 * OpinionMap(계약서 ②) 결과를 받아온다.
 *
 * B의 api.py 스펙:
 *   POST /analyze
 *   body: { url, max_comments?, topic? }
 *   성공 -> OpinionMap JSON
 *   실패 -> 400(잘못된 URL) 또는 500(서버 에러), body.detail에 메시지
 */
export async function analyzeUrl(
  url: string,
  options?: { maxComments?: number; topic?: string }
): Promise<OpinionMap> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        max_comments: options?.maxComments ?? 100,
        topic: options?.topic ?? "",
      }),
    });
  } catch {
    // 서버가 아예 안 떠 있을 때 (fetch 자체가 실패)
    throw new AnalyzeError(
      "서버에 연결할 수 없습니다. 백엔드(analyzer)가 실행 중인지 확인해주세요."
    );
  }

  if (!res.ok) {
    let detail = "분석 중 오류가 발생했습니다.";
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // 응답이 JSON이 아니면 기본 메시지 사용
    }
    throw new AnalyzeError(detail);
  }

  return (await res.json()) as OpinionMap;
}
