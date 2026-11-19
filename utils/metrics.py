"""
Benchmark analysis and comparison metrics for Examora scheduling algorithms.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.models import AlgorithmResult
from core.cost_function import CostEvaluator


class BenchmarkAnalyzer:
    """
    Analyzes, formats, and ranks algorithmic benchmarking results across all 6 AI paradigms.
    """

    @classmethod
    def create_comparison_rows(
        cls, results: Dict[str, AlgorithmResult], total_exams: int
    ) -> List[Dict[str, Any]]:
        """
        Builds a comprehensive comparison dataset from actual execution results.
        Never generates simulated or fake values.
        """
        rows: List[Dict[str, Any]] = []

        for name, res in results.items():
            quality = CostEvaluator.get_quality_score(
                hard_violations=res.hard_violations,
                soft_penalty=res.soft_penalty,
                total_exams=total_exams,
            )

            rows.append({
                "Algorithm": res.algorithm_name,
                "Status": "Solved" if res.success else "Failed / Incomplete",
                "Execution Time (s)": round(res.execution_time, 4),
                "Explored States": res.explored_states,
                "Hard Violations": res.hard_violations,
                "Soft Penalty": round(res.soft_penalty, 2),
                "Total Cost": round(res.total_cost, 2),
                "Quality Score (%)": quality,
                "Message": res.message,
            })

        return rows

    @classmethod
    def get_rankings(cls, rows: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Computes key winners:
        - Fastest algorithm
        - Lowest state space / most memory efficient
        - Highest solution quality / lowest soft penalty
        """
        valid_rows = [r for r in rows if r["Hard Violations"] == 0 and r["Status"] == "Solved"]
        if not valid_rows:
            return {
                "fastest": "None (No valid solution found)",
                "most_efficient": "None",
                "best_quality": "None",
            }

        fastest = min(valid_rows, key=lambda x: x["Execution Time (s)"])["Algorithm"]
        most_efficient = min(valid_rows, key=lambda x: x["Explored States"])["Algorithm"]
        best_quality = min(valid_rows, key=lambda x: x["Total Cost"])["Algorithm"]

        return {
            "fastest": fastest,
            "most_efficient": most_efficient,
            "best_quality": best_quality,
        }
