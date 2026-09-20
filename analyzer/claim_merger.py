import numpy as np

from .embed import embed_comments
from .claim_matcher import match_claim_pairs


def flatten_claims(claim_results):
    """
    Claude의 claim 추출 결과를
    하나의 claim 리스트로 변환한다.
    """

    flattened_claims = []

    for result in claim_results:
        comment_id = result.get(
            "comment_id"
        )

        for claim in result.get(
            "claims",
            []
        ):
            text = claim.get(
                "text",
                ""
            ).strip()

            if not text:
                continue

            flattened_claims.append({
                "text": text,
                "comment_id": comment_id
            })

    return flattened_claims


def embed_claims(claims):
    """
    claim 텍스트를 E5 embedding으로 변환한다.
    """

    if not claims:
        return np.empty(
            (0, 0)
        )

    claim_comments = []

    for index, claim in enumerate(claims):
        claim_comments.append({
            "id": f"claim_{index}",
            "text": claim["text"],
            "analysis_text": claim["text"]
        })

    embeddings = embed_comments(
        claim_comments
    )

    return np.asarray(
        embeddings
    )


def calculate_similarity_matrix(embeddings):
    """
    normalize된 E5 embedding을 이용해
    claim 간 cosine similarity를 계산한다.
    """

    embeddings = np.asarray(
        embeddings
    )

    if len(embeddings) == 0:
        return np.empty(
            (0, 0)
        )

    return np.matmul(
        embeddings,
        embeddings.T
    )


def find_similar_claims(
    claims,
    embeddings,
    top_k=3
):
    """
    각 claim마다 의미적으로 가까운
    다른 claim들을 찾는다.

    전체 N x N similarity matrix를 만들지 않고
    claim 하나씩 similarity를 계산해
    메모리 사용량을 줄인다.

    임베딩 모델은 병합을 결정하지 않고
    Claude에게 전달할 후보만 찾는다.
    """

    if not claims:
        return []

    embeddings = np.asarray(
        embeddings
    )

    results = []

    for index, claim in enumerate(
        claims
    ):
        similarities = np.matmul(
            embeddings,
            embeddings[index]
        )

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        candidates = []

        for candidate_index in ranked_indices:

            if candidate_index == index:
                continue

            candidate = claims[
                candidate_index
            ]

            candidates.append({
                "index": int(
                    candidate_index
                ),
                "text": candidate["text"],
                "comment_id": candidate[
                    "comment_id"
                ],
                "similarity": round(
                    float(
                        similarities[
                            candidate_index
                        ]
                    ),
                    4
                )
            })

            if len(candidates) >= top_k:
                break

        results.append({
            "index": index,
            "claim": claim,
            "candidates": candidates
        })

    return results


def build_candidate_pairs(
    similarity_results
):
    """
    E5가 찾은 후보로 비교 pair를 만든다.

    A-B와 B-A 중복은 제거한다.
    """

    candidate_pairs = []
    seen_pairs = set()

    for result in similarity_results:
        index_a = result["index"]

        for candidate in result[
            "candidates"
        ]:
            index_b = candidate[
                "index"
            ]

            pair_key = tuple(
                sorted(
                    (index_a, index_b)
                )
            )

            if pair_key in seen_pairs:
                continue

            seen_pairs.add(
                pair_key
            )

            candidate_pairs.append({
                "index_a": pair_key[0],
                "index_b": pair_key[1],
                "claim_a": similarity_results[
                    pair_key[0]
                ]["claim"]["text"],
                "claim_b": similarity_results[
                    pair_key[1]
                ]["claim"]["text"]
            })

    return candidate_pairs


def find_same_pairs(
    candidate_pairs
):
    """
    후보 pair를 Claude에게 보내
    same으로 판정된 쌍을 찾는다.
    """

    if not candidate_pairs:
        return []

    matcher_input = []

    for pair in candidate_pairs:
        matcher_input.append({
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    decisions = match_claim_pairs(
        matcher_input
    )

    same_pairs = []

    for decision in decisions:

        if decision["decision"] != "same":
            continue

        pair_id = decision[
            "pair_id"
        ]

        if not (
            0 <= pair_id < len(
                candidate_pairs
            )
        ):
            continue

        pair = candidate_pairs[
            pair_id
        ]

        same_pairs.append({
            "index_a": pair["index_a"],
            "index_b": pair["index_b"]
        })

    return same_pairs


def make_same_lookup(same_pairs):
    """
    same 판정을 빠르게 조회할 수 있도록
    pair 집합을 만든다.
    """

    same_lookup = set()

    for pair in same_pairs:
        pair_key = tuple(
            sorted(
                (
                    pair["index_a"],
                    pair["index_b"]
                )
            )
        )

        same_lookup.add(
            pair_key
        )

    return same_lookup


def can_join_group(
    claim_index,
    group_indices,
    same_lookup
):
    """
    새 claim이 기존 그룹의 모든 claim과
    same으로 확인되었는지 검사한다.

    하나라도 same으로 확인되지 않았다면
    해당 그룹에 넣지 않는다.
    """

    for existing_index in group_indices:

        pair_key = tuple(
            sorted(
                (
                    claim_index,
                    existing_index
                )
            )
        )

        if pair_key not in same_lookup:
            return False

    return True


def build_claim_groups(
    claims,
    same_pairs
):
    """
    같은 claim들을 그룹화한다.

    단순 연결 관계로 합치지 않고,
    그룹 내부의 모든 claim이 서로 same으로
    확인된 경우에만 같은 그룹으로 만든다.
    """

    same_lookup = make_same_lookup(
        same_pairs
    )

    groups = []

    for claim_index in range(
        len(claims)
    ):
        joined = False

        for group_indices in groups:

            if can_join_group(
                claim_index,
                group_indices,
                same_lookup
            ):
                group_indices.append(
                    claim_index
                )

                joined = True
                break

        if not joined:
            groups.append([
                claim_index
            ])

    result = []

    for group_indices in groups:
        group_claims = [
            claims[index]
            for index in group_indices
        ]

        comment_ids = list(
            dict.fromkeys(
                claim["comment_id"]
                for claim in group_claims
            )
        )

        result.append({
            "claims": group_claims,
            "count": len(
                comment_ids
            ),
            "comment_ids": comment_ids
        })

    return result


def merge_claims(
    claim_results,
    top_k=3
):
    """
    전체 claim 병합 과정.

    1. claim 펼치기
    2. E5 embedding
    3. 유사 후보 탐색
    4. Claude same/different 판정
    5. 상호 일관성이 확인된 claim끼리 그룹화
    """

    claims = flatten_claims(
        claim_results
    )

    if not claims:
        return []

    if len(claims) == 1:
        return [{
            "claims": claims,
            "count": 1,
            "comment_ids": [
                claims[0]["comment_id"]
            ]
        }]

    embeddings = embed_claims(
        claims
    )

    similarity_results = (
        find_similar_claims(
            claims,
            embeddings,
            top_k=top_k
        )
    )

    candidate_pairs = (
        build_candidate_pairs(
            similarity_results
        )
    )

    same_pairs = find_same_pairs(
        candidate_pairs
    )

    groups = build_claim_groups(
        claims,
        same_pairs
    )

    return groups