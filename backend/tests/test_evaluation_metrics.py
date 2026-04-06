from __future__ import annotations

from app.evaluation.metrics import compute_metrics


def test_compute_metrics_aggregates_expected_fields():
    records = [
        {
            "is_correct": True,
            "precision_at_k": 0.8,
            "abstained": False,
            "hallucinated": False,
            "latency_ms": 100,
        },
        {
            "is_correct": False,
            "precision_at_k": 0.4,
            "abstained": True,
            "hallucinated": False,
            "latency_ms": 200,
        },
        {
            "is_correct": True,
            "precision_at_k": 0.6,
            "abstained": False,
            "hallucinated": True,
            "latency_ms": 400,
        },
    ]

    metrics = compute_metrics(records)

    assert metrics["match_accuracy"] == 0.6667
    assert metrics["retrieval_precision_at_k"] == 0.6
    assert metrics["hallucination_rate"] == 0.5
    assert metrics["abstain_rate"] == 0.3333
    assert metrics["latency_p95_ms"] >= 100
