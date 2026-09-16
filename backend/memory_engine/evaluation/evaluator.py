"""
memory_engine/evaluation/evaluator.py

Core evaluation logic for scoring context quality, redundancy, and efficiency.
"""

from __future__ import annotations

import re

from schemas.evaluation import EvaluationMetrics, EvaluationRequest, EvaluationResult


class MemoryEvaluator:
    """Evaluate context quality and format correctness."""

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Analyse a context string and compute precision, redundancy, and token efficiency.
        """
        context_lower = request.context.lower()

        # 1. Retrieval Precision (Reference term coverage)
        precision = 1.0
        if request.references:
            found = 0
            for ref in request.references:
                # Use word-boundary or simple substring matching
                if ref.lower() in context_lower:
                    found += 1
            precision = float(found) / len(request.references)

        # 2. Redundancy Ratio
        lines = [line.strip() for line in request.context.split("\n") if line.strip()]
        total_lines = len(lines)
        redundancy = 0.0

        if total_lines > 0:
            seen_lines: set[str] = set()
            duplicate_lines = 0
            for line in lines:
                # Normalise bullet points, numbering, and headers
                clean_line = re.sub(r"^[-*#\s\d.]+", "", line).strip().lower()
                if not clean_line:
                    continue
                if clean_line in seen_lines:
                    duplicate_lines += 1
                else:
                    seen_lines.add(clean_line)
            redundancy = float(duplicate_lines) / total_lines

        # 3. Token Efficiency (ratio of filled content vs. target 4096-token budget)
        # 4096 tokens ≈ 16384 characters
        chars_budget = 16384.0
        efficiency = min(1.0, len(request.context) / chars_budget)

        return EvaluationResult(
            query=request.query,
            metrics=EvaluationMetrics(
                retrieval_precision=round(precision, 4),
                redundancy_ratio=round(redundancy, 4),
                token_efficiency=round(efficiency, 4),
            ),
        )
