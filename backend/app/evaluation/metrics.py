"""Metric computation helpers for RAG evaluation."""

from __future__ import annotations

from statistics import quantiles
from typing import Any


def latency_p95_ms(latencies_ms: list[float]) -> float:
    if not latencies_ms:
        return 0.0
    if len(latencies_ms) == 1:
        return round(float(latencies_ms[0]), 2)
    p95 = quantiles(latencies_ms, n=100, method="inclusive")[94]
    return round(float(p95), 2)


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    total = len(records)
    if total == 0:
        return {
            "match_accuracy": 0.0,
            "retrieval_precision_at_k": 0.0,
            "hallucination_rate": 0.0,
            "abstain_rate": 0.0,
            "latency_p95_ms": 0.0,
        }

    correct = sum(1 for row in records if row.get("is_correct"))
    precision_sum = sum(float(row.get("precision_at_k", 0.0)) for row in records)
    abstained = sum(1 for row in records if row.get("abstained"))

    non_abstained = [row for row in records if not row.get("abstained")]
    hallucinations = sum(1 for row in non_abstained if row.get("hallucinated"))
    hallucination_denominator = max(1, len(non_abstained))

    latencies = [float(row.get("latency_ms", 0.0)) for row in records]

    return {
        "match_accuracy": round(correct / total, 4),
        "retrieval_precision_at_k": round(precision_sum / total, 4),
        "hallucination_rate": round(hallucinations / hallucination_denominator, 4),
        "abstain_rate": round(abstained / total, 4),
        "latency_p95_ms": latency_p95_ms(latencies),
    }
