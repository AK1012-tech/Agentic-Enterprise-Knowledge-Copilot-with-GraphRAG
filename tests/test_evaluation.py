from app.evaluation.ragas_evaluator import evaluate_answers


def test_evaluation_smoke_metrics():
    metrics = evaluate_answers([{"answer": "A", "citations": ["c1"]}, {"answer": "", "citations": []}])
    assert metrics["answer_rate"] == 0.5
    assert metrics["citation_coverage"] == 0.5

