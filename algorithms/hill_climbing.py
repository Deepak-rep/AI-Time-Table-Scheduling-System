"""
Hill Climbing Optimization Algorithm for Examination Scheduling.
Iteratively explores neighboring timetable states to minimize hard and soft constraint costs.
"""
from __future__ import annotations

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


class HillClimbingScheduler(BaseScheduler):
    """
    Hill Climbing local search optimizer.
    
    Starts from an initial timetable (either provided or greedily constructed).
    Evaluates neighborhood transitions (single moves and pairwise swaps).
    Steepest-ascent variant with optional random restarts to escape local optima.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "Hill Climbing")

    def _generate_initial_schedule(self) -> Schedule:
        """Constructs an initial greedy valid schedule if possible, or best effort."""
        from core.scheduler import ExamScheduler
        scheduler = ExamScheduler(self.problem)
        initial = scheduler.generate_initial_valid_schedule()
        if initial is not None and len(initial.assignments) == len(self.problem.exams):
            return initial

        # Fallback: assign each exam to any valid room and slot
        sched = Schedule()
        all_slots = list(self.problem.time_slots.keys())
        all_rooms = list(self.problem.rooms.keys())

        for idx, (eid, exam) in enumerate(self.problem.exams.items()):
            compatible = self.problem.compatible_rooms.get(eid, [])
            room_id = compatible[0].id if compatible else all_rooms[0]
            slot_id = all_slots[idx % len(all_slots)]
            sched.assign(eid, slot_id, room_id)

        return sched

    def _generate_neighbors(
        self,
        current_schedule: Schedule,
        sample_size: int = 50,
        rng: Optional[random.Random] = None,
    ) -> List[Schedule]:
        """
        Generates candidate neighbor schedules by:
        1. Moving an exam to another valid slot and compatible room.
        2. Swapping slots and rooms between two exams.
        """
        if rng is None:
            rng = random.Random()

        neighbors: List[Schedule] = []
        exam_ids = list(current_schedule.assignments.keys())
        if not exam_ids:
            return neighbors

        all_slots = self.problem.time_slots_list

        for _ in range(sample_size):
            move_type = rng.choice(["reassign", "swap"])
            neighbor = current_schedule.copy()

            if move_type == "reassign" or len(exam_ids) < 2:
                # Reassign a random exam to a different slot and compatible room
                eid = rng.choice(exam_ids)
                compatible = self.problem.compatible_rooms.get(eid, list(self.problem.rooms.values()))
                if compatible:
                    new_room = rng.choice(compatible)
                    new_slot = rng.choice(all_slots)
                    neighbor.assign(eid, new_slot.id, new_room.id)
                    neighbors.append(neighbor)
            else:
                # Swap two exams
                e1, e2 = rng.sample(exam_ids, 2)
                a1 = current_schedule.assignments[e1]
                a2 = current_schedule.assignments[e2]

                r1 = self.problem.rooms.get(a1.room_id)
                r2 = self.problem.rooms.get(a2.room_id)
                exam1 = self.problem.exams.get(e1)
                exam2 = self.problem.exams.get(e2)

                # Check capacity compatibility for swap
                if (
                    r1 and r2 and exam1 and exam2
                    and r2.capacity >= exam1.student_count
                    and r1.capacity >= exam2.student_count
                ):
                    neighbor.assign(e1, a2.slot_id, a2.room_id)
                    neighbor.assign(e2, a1.slot_id, a1.room_id)
                    neighbors.append(neighbor)

        return neighbors

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        max_iterations: int = 500,
        max_restarts: int = 3,
        neighborhood_size: int = 40,
        random_seed: int = 42,
        **kwargs: Any,
    ) -> AlgorithmResult:
        start_time = time.time()
        self.explored_states = 0
        rng = random.Random(random_seed)

        best_overall_schedule: Optional[Schedule] = None
        best_overall_cost = float("inf")
        best_overall_hard = 999999

        cost_history: List[float] = []
        iteration_count = 0

        for restart in range(max_restarts):
            # For first run, use greedy constructive timetable; for subsequent restarts, randomize
            if restart == 0:
                current_schedule = self._generate_initial_schedule()
            else:
                current_schedule = self._generate_initial_schedule()
                # Perturb randomly
                all_eids = list(current_schedule.assignments.keys())
                for _ in range(len(all_eids) // 2):
                    eid = rng.choice(all_eids)
                    compat = self.problem.compatible_rooms.get(eid, list(self.problem.rooms.values()))
                    if compat:
                        current_schedule.assign(
                            eid,
                            rng.choice(self.problem.time_slots_list).id,
                            rng.choice(compat).id,
                        )

            current_cost, current_hard, _, _ = CostEvaluator.evaluate(current_schedule, self.problem)
            self.explored_states += 1

            if current_cost < best_overall_cost:
                best_overall_cost = current_cost
                best_overall_hard = current_hard
                best_overall_schedule = current_schedule.copy()

            for step in range(max_iterations // max_restarts):
                iteration_count += 1
                cost_history.append(current_cost)

                if progress_callback and iteration_count % 25 == 0:
                    prog = min(0.95, iteration_count / max_iterations)
                    progress_callback(
                        prog,
                        f"Hill Climbing (Iter {iteration_count}/{max_iterations}): Cost={current_cost:.1f}, HardViolations={current_hard}",
                    )

                # Generate neighborhood
                candidates = self._generate_neighbors(current_schedule, sample_size=neighborhood_size, rng=rng)
                best_candidate: Optional[Schedule] = None
                best_candidate_cost = current_cost
                best_candidate_hard = current_hard

                for cand in candidates:
                    self.explored_states += 1
                    c_cost, c_hard, _, _ = CostEvaluator.evaluate(cand, self.problem)
                    if c_cost < best_candidate_cost:
                        best_candidate_cost = c_cost
                        best_candidate_hard = c_hard
                        best_candidate = cand

                # Check if improvement was found
                if best_candidate and best_candidate_cost < current_cost:
                    current_schedule = best_candidate
                    current_cost = best_candidate_cost
                    current_hard = best_candidate_hard

                    if current_cost < best_overall_cost:
                        best_overall_cost = current_cost
                        best_overall_hard = current_hard
                        best_overall_schedule = current_schedule.copy()
                else:
                    # Reached local optimum for this restart
                    break

        elapsed = time.time() - start_time
        success = best_overall_hard == 0 and best_overall_schedule is not None

        return self._create_result(
            success=success,
            schedule=best_overall_schedule,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "total_iterations": iteration_count,
                "restarts": max_restarts,
                "final_cost": best_overall_cost,
                "hard_violations": best_overall_hard,
                "cost_history": cost_history[:: max(1, len(cost_history) // 30)],  # sampled for plotting
            },
            message=(
                f"Hill Climbing finished after {iteration_count} iterations. "
                f"Best Cost: {best_overall_cost:.1f} (Hard Violations: {best_overall_hard})."
            ),
        )
