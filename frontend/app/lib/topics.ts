import type { OpinionMap } from "../types";

/**
 * 토픽 데이터 로더
 *
 * 파일 구조 (frontend/public 기준):
 *   public/data/topics.json          ← 토픽 목록 (타일에 뭘 보여줄지)
 *   public/data/topics/<key>.json    ← 토픽별 분석 결과 (OpinionMap)
 *   public/tiles/<이미지>             ← 타일 배경 사진
 *
 * 새 토픽 추가 = 코드 수정 없이
 *   1) topics/<key>.json 넣고
 *   2) tiles/ 에 사진 넣고
 *   3) topics.json 에 한 줄 추가
 */

export type TopicMeta = {
  key: string;
  label: string;
  tag: string;
  image: string;
};

export class TopicLoadError extends Error {}

export async function fetchTopicIndex(): Promise<TopicMeta[]> {
  const res = await fetch("/data/topics.json");
  if (!res.ok) throw new TopicLoadError("토픽 목록을 불러오지 못했습니다.");
  return (await res.json()) as TopicMeta[];
}

export async function fetchTopic(key: string): Promise<OpinionMap> {
  const res = await fetch(`/data/topics/${encodeURIComponent(key)}.json`);
  if (!res.ok) throw new TopicLoadError(`'${key}' 토픽 데이터를 불러오지 못했습니다.`);
  return (await res.json()) as OpinionMap;
}
