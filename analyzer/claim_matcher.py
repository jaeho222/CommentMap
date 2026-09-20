import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are a claim matching system for CommentMap.

Your task is to determine whether two claims express essentially
the same opinion or assertion.

The purpose of this step is deduplication.
Two claims should be merged only when combining them would not
remove meaningful information from either claim.

Rules:
1. Return "same" only when the two claims express substantially
   the same assertion.
2. Different wording, paraphrasing, or grammatical structure can
   still be "same".
3. Claims that are merely about the same topic are "different".
4. The main subject and the main conclusion of the two claims must
   match for them to be "same".
5. A broad or general claim and a narrower, specific example,
   instance, consequence, or subset of that claim are "different"
   unless they are genuinely equivalent assertions.
6. If one claim contains an important detail, limitation, cause,
   prediction, example, or conclusion that the other claim does not
   contain, return "different" when merging them would lose that
   information.
7. Claims with different levels of certainty must be "different"
   when the difference changes their meaning.
8. Claims with different causes, effects, predictions, evaluations,
   or conclusions must be "different".
9. Opposing or contradictory claims must always be "different".
10. Do not infer unstated context in order to make two claims match.
11. Do not judge whether either claim is factually true.
12. When uncertain whether two claims are equivalent, prefer
    "different". It is safer for CommentMap to preserve two distinct
    opinions than to incorrectly merge them.
13. Return JSON only. Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "pair_id": 0,
      "decision": "same"
    }
  ]
}
"""


def build_prompt(claim_pairs):
    """
    비교할 claim 쌍을 Claude에 전달할 형태로 만든다.
    """

    pair_data = []

    for pair in claim_pairs:
        pair_data.append({
            "pair_id": pair["pair_id"],
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    return (
        "Determine whether each pair contains the same claim.\n\n"
        + json.dumps(
            pair_data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    """
    Claude가 JSON을 Markdown 코드 블록으로 감싼 경우
    코드 블록을 제거한다.
    """

    text = response_text.strip()

    code_block_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if code_block_match:
        text = code_block_match.group(1).strip()

    return text


def parse_response(response_text):
    """
    Claude의 JSON 응답을 Python 객체로 변환하고
    기본적인 응답 구조를 검증한다.
    """

    cleaned_response = clean_json_response(
        response_text
    )

    try:
        data = json.loads(
            cleaned_response
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            "Claude claim 비교 응답을 "
            "JSON으로 변환하지 못했습니다.\n"
            f"응답 내용:\n{response_text}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "Claude 응답의 최상위 구조가 객체가 아닙니다."
        )

    results = data.get(
        "results"
    )

    if not isinstance(results, list):
        raise ValueError(
            "Claude 응답에 results 리스트가 없습니다."
        )

    validated_results = []

    for result in results:

        if not isinstance(result, dict):
            continue

        pair_id = result.get(
            "pair_id"
        )

        decision = result.get(
            "decision"
        )

        if not isinstance(pair_id, int):
            continue

        if decision not in {
            "same",
            "different"
        }:
            continue

        validated_results.append({
            "pair_id": pair_id,
            "decision": decision
        })

    return validated_results


def make_cache_data(claim_pairs):
    """
    claim matching 결과를 구분하기 위한
    캐시 입력 데이터를 만든다.

    모델이나 프롬프트가 변경되면
    기존 캐시를 사용하지 않는다.
    """

    pair_data = []

    for pair in claim_pairs:
        pair_data.append({
            "pair_id": pair["pair_id"],
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "pairs": pair_data
    }


def match_claim_pairs(
    claim_pairs,
    batch_size=20
):
    """
    claim 후보 쌍들을 Claude가
    same / different로 판정한다.

    후보가 많으면 batch로 나누며,
    동일한 batch 결과가 캐시에 있으면
    API를 다시 호출하지 않는다.
    """

    if not claim_pairs:
        return []

    indexed_pairs = []

    for pair_id, pair in enumerate(
        claim_pairs
    ):
        indexed_pairs.append({
            "pair_id": pair_id,
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    all_results = []

    for start in range(
        0,
        len(indexed_pairs),
        batch_size
    ):
        batch = indexed_pairs[
            start:start + batch_size
        ]

        cache_data = make_cache_data(
            batch
        )

        cached_result = load_cache(
            "claim_matcher",
            cache_data
        )

        if cached_result is not None:
            print(
                "Claim matching: 캐시 사용 "
                "(API 호출 없음)"
            )

            all_results.extend(
                cached_result
            )

            continue

        print(
            "Claim matching: Claude API 호출"
        )

        prompt = build_prompt(
            batch
        )

        response = ask_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048
        )

        batch_results = parse_response(
            response
        )

        save_cache(
            "claim_matcher",
            cache_data,
            batch_results
        )

        all_results.extend(
            batch_results
        )

    return all_results