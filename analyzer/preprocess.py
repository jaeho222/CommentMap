import re
import unicodedata


def normalize_text(text):
    """
    댓글 텍스트의 기본적인 형식을 정리한다.

    의미 자체를 바꾸는 전처리는 하지 않고,
    분석에 방해가 되는 형식적인 노이즈만 정리한다.
    """

    if not isinstance(text, str):
        return ""

    # Unicode 문자 표현 통일
    text = unicodedata.normalize("NFC", text)

    # URL 제거
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # 줄바꿈 / 탭 → 공백
    text = re.sub(
        r"[\r\n\t]+",
        " ",
        text
    )

    # 연속된 공백 정리
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def is_meaningful_comment(text):
    """
    분석할 만한 내용이 있는 댓글인지 확인한다.

    이모지나 특수문자를 무조건 제거하지 않는다.
    감정이나 의견을 표현하는 데 사용될 수 있기 때문이다.
    """

    if not text:
        return False

    # 문자 또는 숫자가 하나라도 있는지 확인
    if re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9]", text):
        return True

    return False


def preprocess_comments(comments):
    """
    댓글 리스트 전체를 전처리한다.

    원본 text는 보존하고,
    분석용 텍스트를 analysis_text에 별도로 저장한다.
    """

    processed_comments = []

    for comment in comments:
        original_text = comment.get("text", "")

        cleaned_text = normalize_text(
            original_text
        )

        if not is_meaningful_comment(cleaned_text):
            continue

        processed_comment = comment.copy()

        # 원문은 그대로 유지
        processed_comment["text"] = original_text

        # 모델 분석용 정제 텍스트
        processed_comment["analysis_text"] = cleaned_text

        processed_comments.append(
            processed_comment
        )

    return processed_comments