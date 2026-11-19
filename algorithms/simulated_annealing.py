"""
Simulated Annealing Optimization Algorithm for Examination Scheduling.
Probabilistically accepts sub-optimal moves based on a decreasing thermal schedule to escape local optima.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from algorithms.base import BaseScheduler
from core.models import (
    AlgorithmResult,
    ExamAssignment,
    Schedule,
    SchedulingProblem,
)
from core.cost_function import CostEvaluator
from core.constraints import ConstraintChecker


class SimulatedAnnealingScheduler(BaseScheduler):
    """
    Simulated Annealing metaheuristic for examination timetabling.
    
    Guarantees:
    - Never returns an invalid hard-constraint-violating schedule if a valid one was encountered.
    - Uses geometric cooling schedule: T(k+1) = T(k) * alpha.
    - Tracks temperature transitions, acceptance rates, and energy curves.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "Simulated Annealing")

    def _generate_initial_schedule(self) -> Schedule:
        """Generates initial valid schedule via greedy constructive heuristic."""
        from core.scheduler import ExamScheduler
        scheduler = ExamScheduler(self.problem)
        sched = scheduler.generate_initial_valid_schedule()
        if sched is not None and len(sched.assignments) == len(self.problem.exams):
            return sched

        # Fallback assignment
        sched = Schedule()
        all_slots = list(self.problem.time_slots.keys())
        all_rooms = list(self.problem.rooms.keys())
        for idx, (eid, exam) in enumerate(self.problem.exams.items()):
            compat = self.problem.compatible_rooms.get(eid, [])
            room_id = compat[0].id if compat else all_rooms[0]
            slot_id = all_slots[idx % len(all_slots)]
            sched.assign(eid, slot_id, room_id)
        return sched

    def _generate_neighbor(
        self,
        current_schedule: Schedule,
        rng: random.Random,
    ) -> Schedule:
        """Generates a neighboring schedule via assignment mutation or pairwise swap."""
        neighbor = current_schedule.copy()
        exam_ids = list(neighbor.assignments.keys())
        if not exam_ids:
            return neighbor

        all_slots = self.problem.time_slots_list
        move_type = rng.choice(["reassign", "swap"])

        if move_type == "reassign" or len(exam_ids) < 2:
            eid = rng.choice(exam_ids)
            compatible = self.problem.compatible_rooms.get(eid, list(self.problem.rooms.values()))
            if compatible:
                new_room = rng.choice(compatible)
                new_slot = rng.choice(all_slots)
                neighbor.assign(eid, new_slot.id, new_room.id)
        else:
            e1, e2 = rng.sample(exam_ids, 2)
            a1 = neighbor.assignments[e1]
            a2 = neighbor.assignments[e2]
            r1 = self.problem.rooms.get(a1.room_id)
            r2 = self.problem.rooms.get(a2.room_id)
            exam1 = self.problem.exams.get(e1)
            exam2 = self.problem.exams.get(e2)

            if r1 and r2 and exam1 and exam2 and r2.capacity >= exam1.student_count and r1.capacity >= exam2.student_count:
                neighbor.assign(e1, a2.slot_id, a2.room_id)
                neighbor.assign(e2, a1.slot_id, a1.room_id)

        return neighbor

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        initial_temperature: float = 100.0,
        cooling_rate: float = 0.985,
        min_temperature: float = 0.05,
        max_iterations: int = 1500,
        random_seed: int = 42,
        **kwargs: Any,
    ) -> AlgorithmResult:
        start_time = time.time()
        self.explored_states = 0
        rng = random.Random(random_seed)

        current_schedule = self._generate_initial_schedule()
        current_cost, current_hard, _, _ = CostEvaluator.evaluate(current_schedule, self.problem)
        self.explored_states += 1

        best_schedule: Schedule = current_schedule.copy()
        best_cost = current_cost
        best_hard = current_hard

        # Specifically track the best VALID schedule (hard violations == 0)
        best_valid_schedule: Optional[Schedule] = current_schedule.copy() if current_hard == 0 else None
        best_valid_cost: float = current_cost if current_hard == 0 else float("inf")

        temperature = initial_temperature
        iteration = 0
        accepted_worse_moves = 0
        total_worse_moves = 0
        cost_history: List[float] = [current_cost]
        temp_history: List[float] = [temperature]

        while temperature > min_temperature and iteration < max_iterations:
            iteration += 1

            if progress_callback and iteration % 50 == 0:
                prog = min(0.95, iteration / max_iterations)
                progress_callback(
                    prog,
                    f"Simulated Annealing (Iter {iteration}, T={temperature:.2f}): Cost={current_cost:.1f}, BestValid={best_valid_cost:.1f}",
                )

            # Generate candidate neighbor
            neighbor = self._generate_neighbor(current_schedule, rng=rng)
            self.explored_states += 1
            neighbor_cost, neighbor_hard, _, _ = CostEvaluator.evaluate(neighbor, self.problem)

            delta_e = neighbor_cost - current_cost

            # Acceptance decision
            accept = False
            if delta_e < 0:
                accept = True
            else:
                total_worse_moves += 1
                acceptance_prob = math.exp(-delta_e / max(1e-6, temperature))
                if rng.random() < acceptance_prob:
                    accept = True
                    accepted_worse_moves += 1

            if accept:
                current_schedule = neighbor
                current_cost = neighbor_cost
                current_hard = neighbor_hard

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_hard = current_hard
                    best_schedule = current_schedule.copy()

                if current_hard == 0 and current_cost < best_valid_cost:
                    best_valid_cost = current_cost
                    best_valid_schedule = current_schedule.copy()

            # Geometric cooling
            temperature *= cooling_rate

            if iteration % max(1, max_iterations // 50) == 0:
                cost_history.append(current_cost)
                temp_history.append(temperature)

        elapsed = time.time() - start_time

        # Final acceptance rule: NEVER accept an invalid schedule if a valid one was found
        final_schedule = best_valid_schedule if best_valid_schedule is not None else best_schedule
        final_cost = best_valid_cost if best_valid_schedule is not None else best_cost
        final_hard = 0 if best_valid_schedule is not None else best_hard
        success = final_hard == 0 and final_schedule is not None

        acceptance_rate = (accepted_worse_moves / max(1, total_worse_moves)) * 100.0

        return self._create_result(
            success=success,
            schedule=final_schedule,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "total_iterations": iteration,
                "initial_temperature": initial_temperature,
                "final_temperature": round(temperature, 4),
                "cooling_rate": cooling_rate,
                "accepted_worse_moves": accepted_worse_moves,
                "total_worse_moves": total_worse_moves,
                "acceptance_rate_percent": round(acceptance_rate, 2),
                "cost_history": cost_history,
                "temp_history": temp_history,
                "best_cost": round(final_cost, 2),
                "hard_violations": final_hard,
            },
            message=(
                f"Simulated Annealing completed {iteration} iterations. "
                f"Final Cost: {final_cost:.1f} (Violations: {final_hard}, Acceptance: {acceptance_rate:.1f}%)."
            ),
        )
