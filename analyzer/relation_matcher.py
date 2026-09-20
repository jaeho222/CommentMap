import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are a conservative claim relation classification system for CommentMap.

CommentMap visualizes explicit argumentative structure across comments.
Its graph should contain only relationships that are useful for
understanding how opinions connect.

For each pair you receive:
- Claim A
- source context for Claim A
- Claim B
- source context for Claim B

The source context is provided only to resolve references or omitted
information needed to understand what each claim means.

The relationship itself must be justified by the propositions
expressed in Claim A and Claim B.

Do NOT use an additional argument, opinion, reason, or conclusion
found only in the source context to create a relationship between
the displayed claims.

A useful test is:
If a reader saw only Claim A and Claim B after their references were
resolved, would the support, attack, or related relationship still
be understandable?

If not, choose "none".
Possible decisions:

- "a_supports_b":
  Claim A provides a direct reason, evidence, explanation, example,
  or argumentative basis for Claim B.

- "b_supports_a":
  Claim B provides a direct reason, evidence, explanation, example,
  or argumentative basis for Claim A.

- "a_attacks_b":
  Claim A directly contradicts, rejects, challenges, or provides
  a direct reason against Claim B.

- "b_attacks_a":
  Claim B directly contradicts, rejects, challenges, or provides
  a direct reason against Claim A.

- "related":
  The claims have a specific and useful semantic relationship,
  but neither directly supports nor attacks the other.

- "none":
  There is no relationship strong enough to display.

Decision procedure:

First consider SUPPORT.

Before choosing support, verify BOTH conditions:

1. The supporting claim contains a reason, evidence, explanation,
   example, or basis relevant to the other claim.

2. Accepting the supporting claim would directly give a reader
   a reason to accept the other claim.

If either condition fails, do not choose support.

Then consider ATTACK.

Before choosing attack, verify at least one of these conditions:

1. The claims directly contradict each other and cannot both hold
   in the intended sense.

2. One claim explicitly rejects or challenges the other.

3. One claim provides a direct reason for rejecting the other.

Different preferences, different aspects, different evaluations,
or alternative suggestions are not attacks by themselves.

Then consider RELATED.

Choose related only when there is a specific relationship between
the actual propositions expressed by the claims that would be useful
to visualize.

Sharing the same:
- topic,
- product,
- person,
- song,
- video,
- sentiment,
- technology,
- or general subject

is not enough for "related".

If none of the above tests is satisfied, choose "none".

Additional rules:

1. Choose exactly one decision for each pair.

2. Prefer a sparse graph with high-confidence relationships.

3. Claims appearing in the same source comment are not automatically
   related. A comment may contain independent opinions.

4. Claims from the same source comment may be related only when the
   original comment explicitly establishes that relationship.

5. Do not invent missing premises, intentions, causal links,
   implications, or argumentative steps.

6. Do not transform correlation, similarity, or shared sentiment
   into support.

7. Do not transform disagreement in tone or preference into attack.

8. Do not infer that a positive statement supports another positive
   statement merely because both praise the same subject.

9. Do not infer that a negative statement supports another negative
   statement merely because both criticize the same subject.

10. Do not infer attack merely because one claim is positive and
    another is negative.

11. If two claims can reasonably both be true without contradiction,
    that is evidence against classifying them as attack.

12. When uncertain between support/attack and related,
    choose "related".

13. When uncertain between related and none,
    choose "none".

14. False-positive edges are more harmful than missing weak edges.

15. Do not judge factual truth.

16. Return JSON only.
    Do not include Markdown or explanations.
    
17. Source context may clarify what a claim refers to, but it must
    not supply a missing premise that creates the edge.
    
18. Do not infer an attack relationship merely because two claims
    appear to have different stances toward the topic.

19. Do not infer a support relationship merely because two claims
    appear to have the same stance toward the topic.

20. The relationship must exist between the propositions expressed
    by Claim A and Claim B themselves.

21. For "a_attacks_b" or "b_attacks_a", one claim must directly
    contradict, reject, challenge, or undermine a proposition,
    reason, assumption, or conclusion expressed by the other claim.

22. For "a_supports_b" or "b_supports_a", one claim must provide
    a reason, evidence, justification, consequence, or premise that
    makes the other claim more convincing.

23. If two claims merely discuss the same topic, share a general
    position, or express different preferences without a direct
    argumentative connection, do not label them support or attack.

24. When deciding between a relationship and "none", prefer "none"
    unless the argumentative connection is clear from the displayed
    claims themselves.

Output format:

{
  "results": [
    {
      "pair_id": 0,
      "decision": "a_supports_b"
    }
  ]
}
"""


VALID_DECISIONS = {
    "a_supports_b",
    "b_supports_a",
    "a_attacks_b",
    "b_attacks_a",
    "related",
    "none"
}


def build_pair_data(claim_pairs):
    """
    Claude 입력과 캐시에서 공통으로 사용하는
    claim pair 데이터를 만든다.
    """

    pair_data = []

    for pair in claim_pairs:
        pair_data.append({
            "pair_id": pair["pair_id"],
            "claim_a": pair["claim_a"],
            "context_a": pair.get(
                "context_a",
                []
            ),
            "claim_b": pair["claim_b"],
            "context_b": pair.get(
                "context_b",
                []
            )
        })

    return pair_data


def build_prompt(claim_pairs):
    """
    claim과 원댓글 맥락을
    Claude에 전달할 형태로 만든다.
    """

    pair_data = build_pair_data(
        claim_pairs
    )

    return (
        "Classify each claim pair using exactly one "
        "of the allowed decisions. Apply the decision "
        "procedure strictly and prefer none when the "
        "relationship requires inference.\n\n"
        + json.dumps(
            pair_data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    text = response_text.strip()

    code_block_match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if code_block_match:
        return code_block_match.group(1).strip()

    start = text.find("{")

    if start == -1:
        return text

    decoder = json.JSONDecoder()

    try:
        _, end = decoder.raw_decode(
            text[start:]
        )

        return text[start:start + end].strip()

    except json.JSONDecodeError:
        return text


def parse_response(response_text):
    """
    Claude 응답을 JSON으로 변환하고
    decision 값을 검증한다.
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
            "Claude relation 응답을 "
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

        if decision not in VALID_DECISIONS:
            continue

        validated_results.append({
            "pair_id": pair_id,
            "decision": decision
        })

    return validated_results


def make_cache_data(claim_pairs):
    """
    모델, 프롬프트, claim, 원댓글 맥락을 포함해
    relation 결과의 캐시 키를 만든다.
    """

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "pairs": build_pair_data(
            claim_pairs
        )
    }


def match_claim_relations(
    claim_pairs,
    batch_size=20
):
    """
    claim pair의 관계와 방향을
    한 번에 판정한다.

    동일한 batch의 캐시가 존재하면
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
            "context_a": pair.get(
                "context_a",
                []
            ),
            "claim_b": pair["claim_b"],
            "context_b": pair.get(
                "context_b",
                []
            )
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
            "relation_matcher",
            cache_data
        )

        if cached_result is not None:
            print(
                "Relation matching: 캐시 사용 "
                "(API 호출 없음)"
            )

            all_results.extend(
                cached_result
            )

            continue

        print(
            "Relation matching: Claude API 호출"
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
            "relation_matcher",
            cache_data,
            batch_results
        )

        all_results.extend(
            batch_results
        )

    return all_results