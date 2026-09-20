from analyzer.claim_matcher import match_claim_pairs


def main():
    claim_pairs = [
        {
            "claim_a": (
                "The video needs an updated version "
                "to reflect recent advances"
            ),
            "claim_b": (
                "An update would be desired, "
                "especially given the rise of ChatGPT"
            )
        },
        {
            "claim_a": (
                "The predictions in the video are "
                "unfolding exactly as predicted"
            ),
            "claim_b": (
                "The predictions in the video "
                "are coming true quickly"
            )
        },
        {
            "claim_a": (
                "Writing and art will be wiped out by AI"
            ),
            "claim_b": (
                "AI art is spreading like wildfire"
            )
        },
        {
            "claim_a": (
                "Using technology to eliminate jobs "
                "causes unemployment"
            ),
            "claim_b": (
                "Technology is advancing rapidly"
            )
        },
        {
            "claim_a": (
                "AI will replace many human workers"
            ),
            "claim_b": (
                "AI will not replace many human workers"
            )
        }
    ]

    print("Claude claim 비교 중...")

    results = match_claim_pairs(
        claim_pairs
    )

    print()

    for result in results:
        pair_id = result["pair_id"]
        decision = result["decision"]
        pair = claim_pairs[pair_id]

        print("=" * 70)
        print(f"[Pair #{pair_id + 1}]")
        print(f"A: {pair['claim_a']}")
        print(f"B: {pair['claim_b']}")
        print(f"판정: {decision}")


if __name__ == "__main__":
    main()