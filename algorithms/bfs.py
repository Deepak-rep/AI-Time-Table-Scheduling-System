"""
Breadth-First Search (BFS) Scheduling Algorithm.
Systematically explores the state space level-by-level using a FIFO queue.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from algorithms.base import BaseScheduler
from core.models import (
    AlgorithmResult,
    ExamAssignment,
    Schedule,
    SchedulingProblem,
)
from core.constraints import ConstraintChecker


class BFSScheduler(BaseScheduler):
    """
    Breadth-First Search (BFS) examination scheduler.
    Explores the assignment tree level-by-level using a FIFO queue.
    Guarantees finding a shallowest valid solution if one exists within state limits.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "Breadth-First Search (BFS)")

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        max_states: int = 50000,
        timeout_seconds: float = 30.0,
        **kwargs: Any,
    ) -> AlgorithmResult:
        start_time = time.time()
        self.explored_states = 0

        # Sort exams to prune earlier (most constrained first by student count & conflicts)
        exam_ids = sorted(
            self.problem.exams.keys(),
            key=lambda eid: (
                self.problem.exams[eid].student_count,
                len(self.problem.exams[eid].enrolled_student_ids),
            ),
            reverse=True,
        )
        total_exams = len(exam_ids)

        if total_exams == 0:
            return self._create_result(True, Schedule(), 0.0, message="No exams to schedule.")

        # Queue contains tuples of (exam_index, immutable_assignments)
        # immutable_assignments is a tuple of (exam_id, slot_id, room_id)
        queue: deque[Tuple[int, Tuple[Tuple[str, str, str], ...]]] = deque()
        queue.append((0, ()))

        visited: Set[Tuple[Tuple[str, str, str], ...]] = set()
        visited.add(())

        best_partial_schedule: Optional[Schedule] = None
        best_partial_depth = 0
        max_queue_size = 1

        while queue:
            # Check limits
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                return self._create_result(
                    success=False,
                    schedule=best_partial_schedule,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "max_queue_size": max_queue_size,
                        "depth_reached": best_partial_depth,
                        "total_exams": total_exams,
                        "reason": f"Timeout after {timeout_seconds}s.",
                    },
                    message=f"BFS timed out after exploring {self.explored_states} states.",
                )

            if self.explored_states >= max_states:
                return self._create_result(
                    success=False,
                    schedule=best_partial_schedule,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "max_queue_size": max_queue_size,
                        "depth_reached": best_partial_depth,
                        "total_exams": total_exams,
                        "reason": f"Reached max state limit ({max_states}).",
                    },
                    message=f"BFS reached state limit ({max_states}) at depth {best_partial_depth}/{total_exams}.",
                )

            max_queue_size = max(max_queue_size, len(queue))
            exam_idx, current_assignments = queue.popleft()
            self.explored_states += 1

            if progress_callback and self.explored_states % 500 == 0:
                progress = min(0.95, exam_idx / total_exams)
                progress_callback(
                    progress,
                    f"BFS exploring depth {exam_idx}/{total_exams} ({self.explored_states} states explored)...",
                )

            # Reconstruct Schedule object for constraint checks
            sched = Schedule()
            for eid, sid, rid in current_assignments:
                sched.assign(eid, sid, rid)

            if exam_idx > best_partial_depth:
                best_partial_depth = exam_idx
                best_partial_schedule = sched.copy()

            # Goal test: All exams assigned
            if exam_idx == total_exams:
                elapsed = time.time() - start_time
                return self._create_result(
                    success=True,
                    schedule=sched,
                    execution_time=elapsed,
                    details={
                        "explored_states": self.explored_states,
                        "max_queue_size": max_queue_size,
                        "depth_reached": total_exams,
                        "total_exams": total_exams,
                    },
                    message=f"BFS successfully found a complete valid timetable in {elapsed:.3f}s.",
                )

            # Expand current state for exam_ids[exam_idx]
            current_eid = exam_ids[exam_idx]
            exam_obj = self.problem.exams[current_eid]
            compatible_rooms = self.problem.compatible_rooms.get(current_eid, [])

            # Generate valid children
            for slot in self.problem.time_slots_list:
                for room in compatible_rooms:
                    # Check hard constraints
                    if ConstraintChecker.is_assignment_valid(
                        exam_id=current_eid,
                        slot_id=slot.id,
                        room_id=room.id,
                        schedule=sched,
                        problem=self.problem,
                    ):
                        new_assignment = current_assignments + ((current_eid, slot.id, room.id),)
                        if new_assignment not in visited:
                            visited.add(new_assignment)
                            queue.append((exam_idx + 1, new_assignment))

        elapsed = time.time() - start_time
        return self._create_result(
            success=False,
            schedule=best_partial_schedule,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "max_queue_size": max_queue_size,
                "depth_reached": best_partial_depth,
                "total_exams": total_exams,
                "reason": "Queue exhausted with no valid complete schedule found.",
            },
            message="BFS exhausted state space without finding a complete schedule.",
        )
