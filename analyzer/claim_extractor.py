import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


BATCH_SIZE = 10


SYSTEM_PROMPT = """
You are a claim extraction system for CommentMap.

CommentMap analyzes the structure of opinions in online comments.

Your task is to extract explicit claims or opinions from each comment.

A single comment may contain:
- zero claims,
- one claim,
- or multiple independent claims.

Rules:

1. Extract only claims or opinions that are explicitly expressed
   in the supplied comment.

2. Do not invent, infer, strengthen, or generalize claims beyond
   what the commenter actually says.

3. Split a comment into multiple claims when it clearly expresses
   multiple independent opinions.

4. Ignore content that does not express a meaningful opinion or claim,
   such as isolated timestamps, meaningless reactions, or unrelated noise.

5. Preserve the language of the original comment.
   - Korean comments must produce Korean claims.
   - English comments must produce English claims.
   - Comments in other languages must remain in their original language.
   - Do not translate claims into English unless the original claim
     itself is written in English.
   - For mixed-language comments, preserve the language naturally used
     for the relevant claim.

6. Preserve names, titles, product names, song names, group names,
   people names, and other proper nouns as written in the source
   whenever possible.
   Do not replace a proper noun with another entity.
   Do not guess what an unfamiliar proper noun refers to.

7. Normalize a claim only enough to make it concise and understandable.
   Preserve the original meaning, tone, subject, and level of specificity.

8. A specific claim must not be rewritten as a broader claim.
   A broad claim must not be rewritten as a more specific claim.

9. Do not classify sentiment or stance.

10. Do not judge whether a claim is factually true.

11. Return JSON only.
    Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "comment_id": "original comment id",
      "claims": [
        {
          "text": "extracted claim"
        }
      ]
    }
  ]
}
"""


def build_comment_data(comments):
    """
    Claude 입력과 캐시에서 공통으로 사용하는
    댓글 데이터를 만든다.
    """

    comment_data = []

    for comment in comments:
        comment_data.append({
            "id": comment["id"],
            "text": comment["text"]
        })

    return comment_data


def build_prompt(comments):
    """
    댓글들을 Claude에게 전달할
    JSON 형태의 프롬프트로 만든다.
    """

    comment_data = build_comment_data(
        comments
    )

    return (
        "Extract explicit claims from each comment.\n\n"
        + json.dumps(
            comment_data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    """
    JSON 응답이 Markdown 코드 블록으로
    감싸져 있으면 제거한다.
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
    Claude 응답을 JSON으로 변환하고
    필요한 구조만 검증한다.
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
            "Claude claim extraction 응답을 "
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

        comment_id = result.get(
            "comment_id"
        )

        claims = result.get(
            "claims",
            []
        )

        if comment_id is None:
            continue

        if not isinstance(claims, list):
            continue

        validated_claims = []

        for claim in claims:

            if not isinstance(claim, dict):
                continue

            text = claim.get(
                "text"
            )

            if not isinstance(text, str):
                continue

            text = text.strip()

            if not text:
                continue

            validated_claims.append({
                "text": text
            })

        validated_results.append({
            "comment_id": str(
                comment_id
            ),
            "claims": validated_claims
        })

    return validated_results


def make_cache_data(comments):
    """
    모델, 프롬프트, 댓글 내용을 포함해
    claim extraction 결과의 캐시 키를 만든다.
    """

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "comments": build_comment_data(
            comments
        )
    }


def split_batches(
    items,
    batch_size
):
    """
    입력 데이터를 일정한 크기의 batch로 나눈다.
    """

    return [
        items[
            start:start + batch_size
        ]
        for start in range(
            0,
            len(items),
            batch_size
        )
    ]


def extract_claims_batch(
    comments,
    batch_number,
    total_batches
):
    """
    하나의 댓글 batch에서 claim을 추출한다.
    """

    cache_data = make_cache_data(
        comments
    )

    cached_result = load_cache(
        "claim_extractor",
        cache_data
    )

    if cached_result is not None:
        print(
            f"Claim extraction: batch "
            f"{batch_number}/{total_batches} "
            "캐시 사용 (API 호출 없음)"
        )

        return cached_result

    print(
        f"Claim extraction: batch "
        f"{batch_number}/{total_batches} "
        "Claude API 호출"
    )

    prompt = build_prompt(
        comments
    )

    response = ask_claude(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=4096
    )

    try:
        batch_results = parse_response(
            response
        )

    except ValueError as error:
        raise ValueError(
            f"Claim extraction batch "
            f"{batch_number}/{total_batches} 처리 실패.\n"
            f"{error}"
        ) from error

    save_cache(
        "claim_extractor",
        cache_data,
        batch_results
    )

    return batch_results


def extract_claims_with_claude(comments):
    """
    댓글에서 claim을 추출한다.

    긴 입력으로 Claude 응답이 잘리는 것을 막기 위해
    댓글을 여러 batch로 나누어 처리한다.

    각 batch는 독립적으로 캐시된다.
    """

    if not comments:
        return []

    batches = split_batches(
        comments,
        BATCH_SIZE
    )

    total_batches = len(
        batches
    )

    all_results = []

    for batch_number, batch in enumerate(
        batches,
        start=1
    ):
        batch_results = extract_claims_batch(
            batch,
            batch_number,
            total_batches
        )

        all_results.extend(
            batch_results
        )

    return all_results