import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are a topic relevance and stance classification system
for CommentMap.

For each claim, determine:

1. Whether the claim is relevant to the supplied topic.
2. If relevant, its stance toward the topic.

Allowed stance labels:
- positive
- negative
- neutral

RELEVANCE

A claim is relevant when understanding the claim helps explain
the discussion, reasoning, disagreement, consequences, background,
or positions surrounding the supplied topic.

Relevant claims may include:
- direct support or opposition
- reasons for supporting or opposing the topic
- consequences or risks of the topic
- factual or contextual claims used to discuss the topic
- predictions that are used as reasoning about the topic
- conditions or alternatives directly connected to the topic

A claim is irrelevant when it is merely present in the same comment
but does not materially contribute to understanding the discussion
about the supplied topic.

Examples of irrelevant content include:
- unrelated opinions about people or organizations
- unrelated political or social commentary
- insults or praise with no meaningful connection to the topic
- unrelated events mentioned in the same comment

Do not require the exact topic words to appear in the claim.
Judge relevance by meaning and context.

STANCE

The stance describes the claim's position toward the supplied topic.
It does NOT describe whether the sentence itself sounds emotionally
positive or negative.

positive:
The claim clearly supports, favors, recommends, defends, or argues
in favor of the topic or a position directly supporting it.

negative:
The claim clearly opposes, rejects, discourages, warns against, or
argues against the topic or a position directly opposing it.

neutral:
The claim is relevant to the topic but does not establish a clear
position for or against it.

This includes:
- factual or descriptive background
- relevant predictions
- relevant contextual information
- ambiguous or mixed positions

RULES

1. Judge relevance before stance.

2. Always judge stance relative to the supplied topic.

3. Do not classify emotional tone as stance.

4. A positive-sounding sentence is not automatically positive.
   A negative-sounding sentence is not automatically negative.

5. Source comments are provided only to resolve references or omitted
   information needed to understand what the claim itself means.

6. Relevance must be justified by the proposition expressed in the
   displayed claim itself after references are resolved.

7. Do NOT make a claim relevant merely because its source comment also
   contains another claim that is relevant to the topic.

8. Do NOT transfer the stance or argumentative role of other sentences
   in the source comment to the displayed claim.

9. A useful relevance test is:
   If a reader saw this claim by itself, after any references were
   resolved, would it still help explain the discussion, reasoning,
   disagreement, consequences, background, or positions surrounding
   the supplied topic?

   If not, set:
   "relevant": false
   "stance": "neutral"

10. Source context may clarify what words such as "it", "they",
    "this decision", or similar references mean, but it must not supply
    a separate argument that makes the claim relevant.

11. Do not infer political, ideological, personal, or other attitudes
   that are not supported by the claim and its immediate context.

12. Do not translate or rewrite the claim.

13. If a claim is irrelevant, set:
   "relevant": false
   "stance": "neutral"

14. If a relevant claim has no clear positive or negative position,
    use neutral.

15. If uncertain about stance, choose neutral.

16. If uncertain about relevance, prefer false unless there is a
    meaningful connection to the topic.

17. Return JSON only.
    Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "claim_id": "c1",
      "relevant": true,
      "stance": "positive"
    }
  ]
}
"""


VALID_STANCES = {
    "positive",
    "negative",
    "neutral"
}


def build_claim_data(claims):
    """
    Claude 입력과 캐시에 사용할
    claim 데이터를 만든다.
    """

    return [
        {
            "claim_id": claim["id"],
            "text": claim["text"],
            "sample_comments": claim.get(
                "sample_comments",
                []
            )
        }
        for claim in claims
    ]


def build_prompt(claims, topic):
    """
    topic과 claim batch를 Claude에 전달한다.
    """

    data = {
        "topic": topic,
        "claims": build_claim_data(
            claims
        )
    }

    return (
        "Determine topic relevance and topic-relative "
        "stance for every claim.\n\n"
        + json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    """
    Claude 응답이 Markdown JSON 코드 블록으로
    감싸져 있으면 제거한다.
    """

    text = response_text.strip()

    match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if match:
        text = match.group(1).strip()

    return text


def parse_response(response_text):
    """
    Claude 응답을 JSON으로 변환하고
    relevance와 stance 값을 검증한다.
    """

    cleaned = clean_json_response(
        response_text
    )

    try:
        data = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            "Claude stance 응답을 JSON으로 "
            "변환하지 못했습니다.\n"
            f"응답 내용:\n{response_text}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "Claude stance 응답의 "
            "최상위 구조가 객체가 아닙니다."
        )

    results = data.get(
        "results"
    )

    if not isinstance(results, list):
        raise ValueError(
            "Claude stance 응답에 "
            "results 리스트가 없습니다."
        )

    validated = []

    for result in results:
        if not isinstance(
            result,
            dict
        ):
            continue

        claim_id = result.get(
            "claim_id"
        )

        relevant = result.get(
            "relevant"
        )

        stance = result.get(
            "stance"
        )

        if not isinstance(
            claim_id,
            str
        ):
            continue

        if not isinstance(
            relevant,
            bool
        ):
            continue

        if stance not in VALID_STANCES:
            continue

        if not relevant:
            stance = "neutral"

        validated.append({
            "claim_id": claim_id,
            "relevant": relevant,
            "stance": stance
        })

    return validated


def make_cache_data(
    claims,
    topic
):
    """
    한 batch에 대한 캐시 키 데이터를 만든다.
    """

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "topic": topic,
        "claims": build_claim_data(
            claims
        )
    }


def classify_claim_stances(
    claims,
    topic="",
    batch_size=20
):
    """
    최종 claim들의 topic relevance와
    topic-relative stance를 batch 단위로 판정한다.

    batch별 결과를 각각 캐시하므로
    중간에 실패하더라도 성공한 batch는
    다음 실행에서 다시 API를 호출하지 않는다.

    응답에서 누락된 claim은 보수적으로
    relevant=False, stance=neutral로 처리한다.
    """

    if not claims:
        return []

    all_results = []

    total_batches = (
        len(claims)
        + batch_size
        - 1
    ) // batch_size

    for batch_index, start in enumerate(
        range(
            0,
            len(claims),
            batch_size
        ),
        start=1
    ):
        batch = claims[
            start:start + batch_size
        ]

        cache_data = make_cache_data(
            batch,
            topic
        )

        cached = load_cache(
            "stance_classifier",
            cache_data
        )

        if cached is not None:
            print(
                f"Stance classification: "
                f"batch {batch_index}/"
                f"{total_batches} 캐시 사용 "
                f"(API 호출 없음)"
            )

            all_results.extend(
                cached
            )

            continue

        print(
            f"Stance classification: "
            f"batch {batch_index}/"
            f"{total_batches} Claude API 호출"
        )

        response = ask_claude(
            prompt=build_prompt(
                batch,
                topic
            ),
            system_prompt=SYSTEM_PROMPT,
            max_tokens=1536
        )

        batch_results = parse_response(
            response
        )

        save_cache(
            "stance_classifier",
            cache_data,
            batch_results
        )

        all_results.extend(
            batch_results
        )

    result_lookup = {
        result["claim_id"]: result
        for result in all_results
    }

    classified_claims = []

    for claim in claims:
        result = result_lookup.get(
            claim["id"],
            {
                "relevant": False,
                "stance": "neutral"
            }
        )

        classified_claim = dict(
            claim
        )

        classified_claim["relevant"] = (
            result["relevant"]
        )

        classified_claim["stance"] = (
            result["stance"]
        )

        classified_claims.append(
            classified_claim
        )

    return classified_claims