"""
Constraint Satisfaction Problem (CSP) with Backtracking Search, MRV Heuristic, and Forward Checking.
"""
from __future__ import annotations

import copy
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


class CSPVariable:
    """Represents a variable (Exam) in the CSP formulation."""
    def __init__(self, exam_id: str, domain: List[Tuple[str, str]]):
        self.exam_id = exam_id
        self.domain = list(domain)  # List of (slot_id, room_id)


class CSPBacktrackingScheduler(BaseScheduler):
    """
    Solves examination scheduling modeled as a formal Constraint Satisfaction Problem (CSP)
    using Backtracking Search enhanced with MRV (Minimum Remaining Values),
    Degree Heuristic tie-breaking, and Forward Checking.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "CSP Backtracking")

    def initialize_domains(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Initializes the domain of each examination variable with unary constraints applied:
        - Room capacity >= exam.student_count
        - Slot duration >= exam.duration_hours
        """
        domains: Dict[str, List[Tuple[str, str]]] = {}
        for eid, exam in self.problem.exams.items():
            compatible_rooms = self.problem.compatible_rooms.get(eid, [])
            valid_pairs: List[Tuple[str, str]] = []

            for slot in self.problem.time_slots_list:
                if exam.duration_hours <= slot.duration_hours:
                    for room in compatible_rooms:
                        valid_pairs.append((slot.id, room.id))

            domains[eid] = valid_pairs
        return domains

    def select_unassigned_variable_mrv(
        self,
        assigned: Dict[str, Tuple[str, str]],
        domains: Dict[str, List[Tuple[str, str]]],
    ) -> str:
        """
        Selects next unassigned variable using:
        1. Minimum Remaining Values (MRV): fewest legal values left.
        2. Tie-breaker: Degree Heuristic (most constraints with other unassigned variables).
        """
        unassigned = [eid for eid in self.problem.exams.keys() if eid not in assigned]

        def degree(eid: str) -> int:
            deg = 0
            for other_eid in unassigned:
                if other_eid != eid:
                    if self.problem.has_student_conflict(eid, other_eid) or self.problem.has_faculty_conflict(eid, other_eid):
                        deg += 1
            return deg

        # Primary key: domain size (ascending), Secondary key: -degree (descending)
        return min(unassigned, key=lambda eid: (len(domains[eid]), -degree(eid)))

    def is_consistent(
        self,
        var: str,
        value: Tuple[str, str],
        assigned: Dict[str, Tuple[str, str]],
    ) -> bool:
        """
        Checks binary constraints between `var = value` and all previously `assigned` variables.
        """
        slot_id, room_id = value
        exam = self.problem.exams[var]

        for other_var, (other_slot, other_room) in assigned.items():
            if slot_id != other_slot:
                continue

            # Room clash: cannot share room in same slot
            if room_id == other_room:
                return False

            # Student clash
            if self.problem.has_student_conflict(var, other_var):
                return False

            # Faculty clash
            if self.problem.has_faculty_conflict(var, other_var):
                return False

        return True

    def forward_check(
        self,
        var: str,
        value: Tuple[str, str],
        assigned: Dict[str, Tuple[str, str]],
        domains: Dict[str, List[Tuple[str, str]]],
    ) -> Tuple[bool, Dict[str, List[Tuple[str, str]]]]:
        """
        Prunes values from domains of unassigned neighbors that conflict with `var = value`.
        Returns (is_viable, pruned_items_dict) for backtrack restoration.
        """
        slot_id, room_id = value
        pruned: Dict[str, List[Tuple[str, str]]] = {}

        for other_var, other_domain in domains.items():
            if other_var in assigned or other_var == var:
                continue

            has_student_conf = self.problem.has_student_conflict(var, other_var)
            has_faculty_conf = self.problem.has_faculty_conflict(var, other_var)

            # Check each possible value in neighbor's domain
            to_remove = []
            for (n_slot, n_room) in other_domain:
                if n_slot == slot_id:
                    # Same room conflict
                    if n_room == room_id:
                        to_remove.append((n_slot, n_room))
                    # Student or faculty conflict
                    elif has_student_conf or has_faculty_conf:
                        to_remove.append((n_slot, n_room))

            if to_remove:
                pruned[other_var] = to_remove
                domains[other_var] = [val for val in other_domain if val not in to_remove]

                # If domain is wiped out, forward check fails immediately
                if len(domains[other_var]) == 0:
                    return False, pruned

        return True, pruned

    def restore_domains(
        self,
        domains: Dict[str, List[Tuple[str, str]]],
        pruned: Dict[str, List[Tuple[str, str]]],
    ) -> None:
        """Restores values pruned during forward checking."""
        for var, removed_values in pruned.items():
            domains[var].extend(removed_values)

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        use_mrv: bool = True,
        use_forward_checking: bool = True,
        timeout_seconds: float = 30.0,
        **kwargs: Any,
    ) -> AlgorithmResult:
        start_time = time.time()
        self.explored_states = 0
        backtracks = 0

        domains = self.initialize_domains()
        total_exams = len(self.problem.exams)

        # Check for initial empty domains (unsolvable due to room capacity/duration)
        for eid, dom in domains.items():
            if not dom:
                return self._create_result(
                    success=False,
                    schedule=None,
                    execution_time=time.time() - start_time,
                    details={"error": f"Initial domain for exam {eid} is empty. No room has adequate capacity."},
                    message=f"Exam {eid} cannot be scheduled: domain is empty.",
                )

        assigned: Dict[str, Tuple[str, str]] = {}

        def backtrack() -> Optional[Dict[str, Tuple[str, str]]]:
            nonlocal backtracks
            self.explored_states += 1

            if time.time() - start_time > timeout_seconds:
                return None

            if len(assigned) == total_exams:
                return assigned

            if progress_callback and self.explored_states % 250 == 0:
                prog = min(0.95, len(assigned) / total_exams)
                progress_callback(
                    prog,
                    f"CSP Backtracking (Assigned {len(assigned)}/{total_exams}, States={self.explored_states}, Backtracks={backtracks})...",
                )

            # Choose variable
            if use_mrv:
                var = self.select_unassigned_variable_mrv(assigned, domains)
            else:
                unassigned = [e for e in self.problem.exams.keys() if e not in assigned]
                var = unassigned[0]

            # Try values in domain
            for value in list(domains[var]):
                if self.is_consistent(var, value, assigned):
                    assigned[var] = value

                    if use_forward_checking:
                        viable, pruned = self.forward_check(var, value, assigned, domains)
                        if viable:
                            result = backtrack()
                            if result is not None:
                                return result
                        # Restore pruned values on failure
                        self.restore_domains(domains, pruned)
                    else:
                        result = backtrack()
                        if result is not None:
                            return result

                    # Backtrack step
                    assigned.pop(var, None)
                    backtracks += 1

            return None

        final_assigned = backtrack()
        elapsed = time.time() - start_time

        if final_assigned is not None:
            schedule = Schedule()
            for eid, (slot_id, room_id) in final_assigned.items():
                schedule.assign(eid, slot_id, room_id)

            return self._create_result(
                success=True,
                schedule=schedule,
                execution_time=elapsed,
                details={
                    "explored_states": self.explored_states,
                    "backtracks": backtracks,
                    "use_mrv": use_mrv,
                    "use_forward_checking": use_forward_checking,
                },
                message=f"CSP Backtracking found a valid timetable in {elapsed:.3f}s with {backtracks} backtracks.",
            )

        return self._create_result(
            success=False,
            schedule=None,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "backtracks": backtracks,
                "use_mrv": use_mrv,
                "use_forward_checking": use_forward_checking,
            },
            message=f"CSP Backtracking failed to find a valid solution after {self.explored_states} states ({backtracks} backtracks).",
        )
