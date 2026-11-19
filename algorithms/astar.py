"""
A* Search Examination Scheduling Algorithm.
Utilizes an admissible heuristic function, accumulated path costs, and priority queue search.
"""
from __future__ import annotations

import heapq
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from algorithms.base import BaseScheduler
from core.models import (
    AlgorithmResult,
    ExamAssignment,
    Schedule,
    SchedulingProblem,
)
from core.constraints import ConstraintChecker


class AStarNode:
    """
    Search node for A* priority queue.
    """
    __slots__ = ("priority", "f_cost", "g_cost", "h_cost", "exam_idx", "assignments", "node_id")

    def __init__(
        self,
        priority: float,
        f_cost: float,
        g_cost: float,
        h_cost: float,
        exam_idx: int,
        assignments: Tuple[Tuple[str, str, str], ...],
        node_id: int,
    ):
        self.priority = priority
        self.f_cost = f_cost
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.exam_idx = exam_idx
        self.assignments = assignments
        self.node_id = node_id

    def __lt__(self, other: AStarNode) -> bool:
        if abs(self.priority - other.priority) > 1e-5:
            return self.priority < other.priority
        if abs(self.f_cost - other.f_cost) > 1e-5:
            return self.f_cost < other.f_cost
        if self.exam_idx != other.exam_idx:
            return self.exam_idx > other.exam_idx
        return self.node_id < other.node_id


class AStarScheduler(BaseScheduler):
    """
    A* Search Algorithm for Examination Timetabling.
    
    Formal Formulation:
    - State: Partial schedule assignment up to exam index k.
    - Path Cost g(n): Accumulated soft constraint penalties (consecutive exams, room wastage)
      of assigned examinations so far.
    - Heuristic Cost h(n): Admissible lower bound on remaining cost:
        h(n) = sum_{u in unassigned} min_{r in CompatibleRooms(u)} [ 0.1 * (capacity(r) - students(u)) ]
      
    Priority Queue Ranking:
    - To prevent shallow-node flooding in fixed-depth combinatorial scheduling trees,
      nodes are evaluated with priority P(n) = (TotalExams - depth) * C + f(n),
      where f(n) = g(n) + h(n).
    
    Admissibility and Optimality Justification:
    - The room wastage heuristic h(n) is strictly admissible (h(n) <= h*(n)).
    - With depth-guided priority, search reaches deep goal states rapidly while preserving
      local f(n) tie-breaking, trading asymptotic optimality for exponential speedup.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "A* Search")
        self._precompute_min_wastage()

    def _precompute_min_wastage(self) -> None:
        """Precomputes minimum unavoidable room wastage penalty for each exam."""
        self.min_wastage: Dict[str, float] = {}
        for eid, exam in self.problem.exams.items():
            compatible = self.problem.compatible_rooms.get(eid, [])
            if not compatible:
                self.min_wastage[eid] = 0.0
            else:
                min_excess = min(r.capacity - exam.student_count for r in compatible)
                self.min_wastage[eid] = max(0.0, min_excess * 0.1)

    def heuristic(self, remaining_exam_ids: List[str]) -> float:
        """Admissible heuristic function h(n) for remaining unassigned exams."""
        return sum(self.min_wastage.get(eid, 0.0) for eid in remaining_exam_ids)

    def calculate_step_cost(
        self,
        exam_id: str,
        slot_id: str,
        room_id: str,
        current_schedule: Schedule,
    ) -> float:
        """Calculates the incremental soft penalty added by assigning (exam_id, slot_id, room_id)."""
        exam = self.problem.exams[exam_id]
        room = self.problem.rooms[room_id]
        slot = self.problem.time_slots[slot_id]

        excess = max(0, room.capacity - exam.student_count)
        cost = excess * 0.1

        for other_eid, assign in current_schedule.assignments.items():
            if self.problem.has_student_conflict(exam_id, other_eid):
                other_slot = self.problem.time_slots.get(assign.slot_id)
                if other_slot:
                    days_diff = slot.days_between(other_slot)
                    if days_diff == 0:
                        cost += 20.0
                    elif days_diff == 1:
                        cost += 5.0

        return cost

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        max_states: int = 50000,
        timeout_seconds: float = 30.0,
        depth_weight: float = 50.0,
        **kwargs: Any,
    ) -> AlgorithmResult:
        start_time = time.time()
        self.explored_states = 0

        exam_ids = sorted(
            self.problem.exams.keys(),
            key=lambda eid: (
                len(self.problem.exams[eid].enrolled_student_ids),
                self.problem.exams[eid].student_count,
            ),
            reverse=True,
        )
        total_exams = len(exam_ids)

        if total_exams == 0:
            return self._create_result(True, Schedule(), 0.0, message="No exams to schedule.")

        initial_h = self.heuristic(exam_ids)
        root = AStarNode(
            priority=total_exams * depth_weight + initial_h,
            f_cost=initial_h,
            g_cost=0.0,
            h_cost=initial_h,
            exam_idx=0,
            assignments=(),
            node_id=0,
        )

        open_heap: List[AStarNode] = [root]
        cost_so_far: Dict[Tuple[Tuple[str, str, str], ...], float] = {(): 0.0}

        best_partial_schedule: Optional[Schedule] = None
        best_partial_depth = 0
        node_counter = 1

        while open_heap:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                return self._create_result(
                    success=False,
                    schedule=best_partial_schedule,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "depth_reached": best_partial_depth,
                        "admissible": True,
                        "reason": f"Timeout after {timeout_seconds}s.",
                    },
                    message=f"A* timed out after exploring {self.explored_states} states.",
                )

            if self.explored_states >= max_states:
                return self._create_result(
                    success=False,
                    schedule=best_partial_schedule,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "depth_reached": best_partial_depth,
                        "admissible": True,
                        "reason": f"Reached state limit ({max_states}).",
                    },
                    message=f"A* reached limit of {max_states} states at depth {best_partial_depth}/{total_exams}.",
                )

            current = heapq.heappop(open_heap)
            self.explored_states += 1

            if progress_callback and self.explored_states % 250 == 0:
                progress = min(0.95, current.exam_idx / total_exams)
                progress_callback(
                    progress,
                    f"A* searching depth {current.exam_idx}/{total_exams} (f={current.f_cost:.1f}, {self.explored_states} states)...",
                )

            # Reconstruct schedule
            sched = Schedule()
            for eid, sid, rid in current.assignments:
                sched.assign(eid, sid, rid)

            if current.exam_idx > best_partial_depth:
                best_partial_depth = current.exam_idx
                best_partial_schedule = sched.copy()

            # Goal test: All exams assigned
            if current.exam_idx == total_exams:
                elapsed = time.time() - start_time
                return self._create_result(
                    success=True,
                    schedule=sched,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "final_f_cost": round(current.f_cost, 2),
                        "final_g_cost": round(current.g_cost, 2),
                        "admissible": True,
                        "optimality_guarantee": "Heuristic h(n) strictly admissible lower bound; priority uses depth-guided horizon",
                        "depth_reached": total_exams,
                    },
                    message=f"A* found a valid schedule (g={current.g_cost:.1f}) in {elapsed:.3f}s with {self.explored_states} states explored.",
                )

            current_eid = exam_ids[current.exam_idx]
            exam_obj = self.problem.exams[current_eid]
            remaining_after = exam_ids[current.exam_idx + 1 :]
            h_next = self.heuristic(remaining_after)

            compat = sorted(
                self.problem.compatible_rooms.get(current_eid, []),
                key=lambda r: r.capacity - exam_obj.student_count,
            )

            # Generate candidate (slot, best_room) pairs
            candidates: List[Tuple[float, str, str]] = []
            for slot in self.problem.time_slots_list:
                for room in compat:
                    if ConstraintChecker.is_assignment_valid(
                        exam_id=current_eid,
                        slot_id=slot.id,
                        room_id=room.id,
                        schedule=sched,
                        problem=self.problem,
                    ):
                        step_cost = self.calculate_step_cost(current_eid, slot.id, room.id, sched)
                        candidates.append((step_cost, slot.id, room.id))
                        # Pick best-fitting compatible room for this slot
                        break

            # Sort candidates by lowest step cost first
            candidates.sort(key=lambda c: c[0])

            for step_cost, slot_id, room_id in candidates:
                new_g = current.g_cost + step_cost
                new_f = new_g + h_next
                new_depth = current.exam_idx + 1
                new_priority = (total_exams - new_depth) * depth_weight + new_f
                new_assignments = current.assignments + ((current_eid, slot_id, room_id),)

                if new_assignments not in cost_so_far or new_g < cost_so_far[new_assignments]:
                    cost_so_far[new_assignments] = new_g
                    node_counter += 1
                    child_node = AStarNode(
                        priority=new_priority,
                        f_cost=new_f,
                        g_cost=new_g,
                        h_cost=h_next,
                        exam_idx=new_depth,
                        assignments=new_assignments,
                        node_id=node_counter,
                    )
                    heapq.heappush(open_heap, child_node)

        elapsed = time.time() - start_time
        return self._create_result(
            success=False,
            schedule=best_partial_schedule,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "depth_reached": best_partial_depth,
                "admissible": True,
            },
            message="A* exhausted open list without finding a complete schedule.",
        )
