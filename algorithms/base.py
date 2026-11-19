"""
Base classes and interfaces for Examora scheduling algorithms.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from core.models import AlgorithmResult, Schedule, SchedulingProblem
from core.cost_function import CostEvaluator


class BaseScheduler(ABC):
    """
    Abstract base class for all examination scheduling algorithms.
    """

    def __init__(self, problem: SchedulingProblem, name: str):
        self.problem = problem
        self.name = name
        self.explored_states = 0
        self.start_time = 0.0

    @abstractmethod
    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """Executes the scheduling algorithm."""
        pass

    def _create_result(
        self,
        success: bool,
        schedule: Optional[Schedule],
        execution_time: float,
        details: Optional[Dict[str, Any]] = None,
        message: str = "",
    ) -> AlgorithmResult:
        hard_count = 0
        soft_penalty = 0.0
        total_cost = 0.0
        msgs: List[str] = []

        if schedule and len(schedule.assignments) > 0:
            total_cost, hard_count, soft_penalty, msgs = CostEvaluator.evaluate(
                schedule, self.problem
            )
            if hard_count > 0:
                success = False

        return AlgorithmResult(
            algorithm_name=self.name,
            success=success,
            schedule=schedule,
            execution_time=execution_time,
            explored_states=self.explored_states,
            hard_violations=hard_count,
            soft_penalty=soft_penalty,
            total_cost=total_cost,
            violation_details=msgs,
            details=details or {},
            message=message,
        )
