import numpy as np

from .embed import embed_comments
from .relation_matcher import match_claim_relations


def embed_final_claims(claims):
    """
    최종 claim들을 E5 embedding으로 변환한다.
    """

    if not claims:
        return np.empty((0, 0))

    claim_comments = []

    for claim in claims:
        claim_comments.append({
            "id": claim["id"],
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
        return np.empty((0, 0))

    return np.matmul(
        embeddings,
        embeddings.T
    )


def build_relation_candidates(
    claims,
    embeddings,
    top_k=3
):
    """
    E5를 이용해 관계가 있을 가능성이 높은
    claim 조합을 찾는다.

    E5는 후보만 선택하고 관계 종류나 방향은
    결정하지 않는다.

    relation 판단에 사용할 수 있도록
    각 claim의 원댓글 예시도 함께 보존한다.
    """

    if len(claims) < 2:
        return []

    similarity_matrix = (
        calculate_similarity_matrix(
            embeddings
        )
    )

    candidate_pairs = []
    seen_pairs = set()

    for index_a in range(
        len(claims)
    ):
        similarities = similarity_matrix[
            index_a
        ]

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        selected_count = 0

        for index_b in ranked_indices:

            if index_a == index_b:
                continue

            index_b = int(
                index_b
            )

            pair_key = tuple(
                sorted(
                    (
                        index_a,
                        index_b
                    )
                )
            )

            if pair_key not in seen_pairs:
                seen_pairs.add(
                    pair_key
                )

                claim_a = claims[
                    pair_key[0]
                ]

                claim_b = claims[
                    pair_key[1]
                ]

                candidate_pairs.append({
                    "index_a": pair_key[0],
                    "index_b": pair_key[1],
                    "claim_a": claim_a["text"],
                    "claim_b": claim_b["text"],
                    "context_a": claim_a.get(
                        "sample_comments",
                        []
                    ),
                    "context_b": claim_b.get(
                        "sample_comments",
                        []
                    )
                })

            selected_count += 1

            if selected_count >= top_k:
                break

    return candidate_pairs


def classify_relation_candidates(
    candidate_pairs
):
    """
    claim뿐 아니라 해당 claim이 나온 원댓글 맥락도
    Claude에게 전달해 관계를 판정한다.
    """

    if not candidate_pairs:
        return []

    matcher_input = []

    for pair in candidate_pairs:
        matcher_input.append({
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"],
            "context_a": pair.get(
                "context_a",
                []
            ),
            "context_b": pair.get(
                "context_b",
                []
            )
        })

    decisions = match_claim_relations(
        matcher_input
    )

    classified = []

    for decision in decisions:

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

        classified.append({
            "index_a": pair["index_a"],
            "index_b": pair["index_b"],
            "decision": decision[
                "decision"
            ]
        })

    return classified


def convert_to_relation(
    result,
    claims
):
    """
    Claude의 방향성 decision을
    OpinionMap relation 구조로 변환한다.
    """

    decision = result[
        "decision"
    ]

    index_a = result[
        "index_a"
    ]

    index_b = result[
        "index_b"
    ]

    claim_a = claims[
        index_a
    ]

    claim_b = claims[
        index_b
    ]

    if decision == "a_supports_b":
        return {
            "from": claim_a["id"],
            "to": claim_b["id"],
            "type": "support"
        }

    if decision == "b_supports_a":
        return {
            "from": claim_b["id"],
            "to": claim_a["id"],
            "type": "support"
        }

    if decision == "a_attacks_b":
        return {
            "from": claim_a["id"],
            "to": claim_b["id"],
            "type": "attack"
        }

    if decision == "b_attacks_a":
        return {
            "from": claim_b["id"],
            "to": claim_a["id"],
            "type": "attack"
        }

    if decision == "related":
        return {
            "from": claim_a["id"],
            "to": claim_b["id"],
            "type": "related"
        }

    return None


def build_relations(
    claims,
    top_k=3
):
    """
    최종 claim 사이의 관계를 만든다.

    과정:
    1. E5로 관계 후보 탐색
    2. claim + 원댓글 맥락을 Claude에 전달
    3. 관계 종류와 방향을 한 번에 판정
    4. none 제거
    5. OpinionMap relation 형태로 변환
    """

    if len(claims) < 2:
        return []

    embeddings = embed_final_claims(
        claims
    )

    candidate_pairs = (
        build_relation_candidates(
            claims,
            embeddings,
            top_k=top_k
        )
    )

    classified = (
        classify_relation_candidates(
            candidate_pairs
        )
    )

    relations = []
    seen_relations = set()

    for result in classified:

        relation = convert_to_relation(
            result,
            claims
        )

        if relation is None:
            continue

        relation_key = (
            relation["from"],
            relation["to"],
            relation["type"]
        )

        if relation_key in seen_relations:
            continue

        seen_relations.add(
            relation_key
        )

        relations.append(
            relation
        )

    return relations