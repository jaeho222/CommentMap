from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"

_model = None


def get_model():
    """
    E5 모델이 실제로 필요한 시점에만 로딩한다.

    이미 로딩된 모델이 있으면
    같은 모델 객체를 다시 사용한다.
    """

    global _model

    if _model is None:
        _model = SentenceTransformer(
            MODEL_NAME
        )

    return _model


def embed_comments(comments):
    """
    댓글을 의미 벡터(embedding)로 변환한다.

    preprocess를 거친 댓글은 analysis_text를 사용하고,
    없는 경우 기존 text를 사용한다.
    """

    if not comments:
        return []

    texts = []

    for comment in comments:
        text = comment.get(
            "analysis_text",
            comment.get("text", "")
        )

        texts.append(
            f"passage: {text}"
        )

    model = get_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings