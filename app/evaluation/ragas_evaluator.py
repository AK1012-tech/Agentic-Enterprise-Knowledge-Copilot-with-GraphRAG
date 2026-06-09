def evaluate_answers(samples: list[dict]) -> dict[str, float]:
    if not samples:
        return {"citation_coverage": 0.0, "answer_rate": 0.0}
    answer_rate = sum(1 for sample in samples if sample.get("answer")) / len(samples)
    citation_coverage = sum(1 for sample in samples if sample.get("citations")) / len(samples)
    return {"citation_coverage": citation_coverage, "answer_rate": answer_rate}

