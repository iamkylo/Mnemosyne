from memory_engine.evaluation.evaluator import MemoryEvaluator
from schemas.evaluation import EvaluationRequest


def test_evaluator_precision() -> None:
    evaluator = MemoryEvaluator()
    req = EvaluationRequest(
        query="test query",
        context="FastAPI is a fast web framework.",
        references=["FastAPI", "framework", "missing_word"],
    )
    res = evaluator.evaluate(req)
    # 2 out of 3 references found -> 2/3 = 0.6667
    assert res.metrics.retrieval_precision == 0.6667


def test_evaluator_redundancy() -> None:
    evaluator = MemoryEvaluator()
    req = EvaluationRequest(
        query="test query",
        context="- Duplicate bullet\n- Duplicate bullet\n- Unique bullet",
        references=[],
    )
    res = evaluator.evaluate(req)
    # total 3 lines, 1 duplicate -> redundancy = 1/3 = 0.3333
    assert res.metrics.redundancy_ratio == 0.3333


def test_evaluator_token_efficiency() -> None:
    evaluator = MemoryEvaluator()
    req = EvaluationRequest(query="test query", context="x" * 8192, references=[])
    res = evaluator.evaluate(req)
    # 8192 chars / 16384.0 budget = 0.5 efficiency
    assert res.metrics.token_efficiency == 0.5
