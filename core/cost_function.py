"""
Cost function and evaluation metrics for Examora.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from core.models import Schedule, SchedulingProblem
from core.constraints import ConstraintChecker, HardConstraintViolation, SoftConstraintViolation


class CostEvaluator:
    """
    Evaluates timetable quality by computing hard and soft constraint costs.
    """
    HARD_VIOLATION_WEIGHT: float = 10000.0

    @classmethod
    def evaluate(
        cls,
        schedule: Schedule,
        problem: SchedulingProblem,
    ) -> Tuple[float, int, float, List[str]]:
        """
        Calculates total cost, hard violations count, soft penalty, and readable violation summaries.
        
        Returns:
            (total_cost, hard_violations_count, soft_penalty, violation_messages)
        """
        hard_count, hard_violations = ConstraintChecker.check_hard_constraints(schedule, problem)
        soft_penalty, soft_violations = ConstraintChecker.evaluate_soft_constraints(schedule, problem)

        total_cost = (hard_count * cls.HARD_VIOLATION_WEIGHT) + soft_penalty

        messages: List[str] = [hv.message for hv in hard_violations]
        # Include top soft violation notices if helpful
        for sv in soft_violations[:5]:
            messages.append(f"[Soft] {sv.message} (penalty: {sv.penalty:.1f})")

        return round(total_cost, 2), hard_count, round(soft_penalty, 2), messages

    @classmethod
    def get_quality_score(cls, hard_violations: int, soft_penalty: float, total_exams: int) -> float:
        """
        Computes a normalized quality score between 0% and 100%.
        100% means 0 hard violations and 0 soft penalties.
        """
        if hard_violations > 0:
            # Significant reduction for invalid schedules
            return max(0.0, round(45.0 - (hard_violations * 8.0), 1))

        # Baseline expected soft penalty scales with exams and student enrollment density
        baseline = max(500.0, total_exams * 250.0)
        penalty_ratio = soft_penalty / baseline
        quality = max(55.0, 100.0 - (penalty_ratio * 25.0))
        return min(99.5, round(quality, 1))
