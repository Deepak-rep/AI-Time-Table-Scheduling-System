"""
ExamScheduler: Central coordinator and execution engine for all 6 AI algorithms in Examora.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from core.models import (
    AlgorithmResult,
    ExamAssignment,
    Schedule,
    SchedulingProblem,
)
from core.constraints import ConstraintChecker
from core.cost_function import CostEvaluator


class ExamScheduler:
    """
    Coordinates execution, validation, and benchmarking of examination scheduling algorithms.
    """

    SUPPORTED_ALGORITHMS = [
        "Breadth-First Search (BFS)",
        "A* Search",
        "Hill Climbing",
        "Simulated Annealing",
        "CSP Backtracking",
        "AC-3 with Backtracking",
    ]

    def __init__(self, problem: SchedulingProblem):
        self.problem = problem

    def generate_initial_valid_schedule(self) -> Optional[Schedule]:
        """
        Generates a fast, greedily constructed valid schedule satisfying all hard constraints.
        Used as the starting state for local search algorithms (Hill Climbing & Simulated Annealing).
        """
        schedule = Schedule()
        # Sort exams by student count descending (most constrained first)
        sorted_exams = sorted(
            self.problem.exams.values(),
            key=lambda e: (e.student_count, len(e.enrolled_student_ids)),
            reverse=True,
        )

        for exam in sorted_exams:
            assigned = False
            # Find compatible rooms with capacity >= exam.student_count
            compatible_rooms = sorted(
                self.problem.compatible_rooms.get(exam.id, []),
                key=lambda r: r.capacity,  # best fit first
            )

            for slot in self.problem.time_slots_list:
                for room in compatible_rooms:
                    if ConstraintChecker.is_assignment_valid(
                        exam_id=exam.id,
                        slot_id=slot.id,
                        room_id=room.id,
                        schedule=schedule,
                        problem=self.problem,
                    ):
                        schedule.assign(exam.id, slot.id, room.id)
                        assigned = True
                        break
                if assigned:
                    break

            if not assigned:
                return None  # Could not construct greedy initial schedule

        return schedule

    def run_algorithm(
        self,
        algorithm_name: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """
        Executes the chosen scheduling algorithm and audits the resulting timetable.
        """
        # Late import to prevent circular dependencies
        from algorithms.bfs import BFSScheduler
        from algorithms.astar import AStarScheduler
        from algorithms.hill_climbing import HillClimbingScheduler
        from algorithms.simulated_annealing import SimulatedAnnealingScheduler
        from algorithms.csp_backtracking import CSPBacktrackingScheduler
        from algorithms.ac3 import AC3Scheduler

        algo_lower = algorithm_name.lower()

        if "breadth-first" in algo_lower or "bfs" in algo_lower:
            runner = BFSScheduler(self.problem)
        elif "a*" in algo_lower or "astar" in algo_lower:
            runner = AStarScheduler(self.problem)
        elif "hill climbing" in algo_lower:
            runner = HillClimbingScheduler(self.problem)
        elif "simulated annealing" in algo_lower:
            runner = SimulatedAnnealingScheduler(self.problem)
        elif "csp" in algo_lower and "ac-3" not in algo_lower:
            runner = CSPBacktrackingScheduler(self.problem)
        elif "ac-3" in algo_lower or "ac3" in algo_lower:
            runner = AC3Scheduler(self.problem)
        else:
            raise ValueError(f"Unsupported algorithm: '{algorithm_name}'. Must be one of {self.SUPPORTED_ALGORITHMS}")

        result = runner.solve(progress_callback=progress_callback, **kwargs)

        # Audit result if schedule was returned
        if result.schedule and len(result.schedule.assignments) > 0:
            total_cost, hard_count, soft_penalty, msgs = CostEvaluator.evaluate(
                result.schedule, self.problem
            )
            result.hard_violations = hard_count
            result.soft_penalty = soft_penalty
            result.total_cost = total_cost
            result.violation_details = msgs
            # If any hard violations remain, mark success as False
            if hard_count > 0:
                result.success = False

        return result

    def compare_all(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> Dict[str, AlgorithmResult]:
        """
        Runs all 6 algorithms on the same dataset with identical constraints.
        Returns a dictionary mapping algorithm name to its AlgorithmResult.
        """
        results: Dict[str, AlgorithmResult] = {}
        total = len(self.SUPPORTED_ALGORITHMS)

        for idx, algo in enumerate(self.SUPPORTED_ALGORITHMS):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"Evaluating {algo} ({idx + 1}/{total})...",
                )
            res = self.run_algorithm(algo, **kwargs)
            results[algo] = res

        if progress_callback:
            progress_callback(1.0, "All 6 algorithms completed successfully!")

        return results
