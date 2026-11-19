"""
Arc Consistency Algorithm 3 (AC-3) Implementation.
Provides genuine domain reduction, constraint propagation, arc revision,
and seamless integration with CSP Backtracking (Maintaining Arc Consistency - MAC).
"""
from __future__ import annotations

import copy
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


class AC3Scheduler(BaseScheduler):
    """
    Arc Consistency Algorithm 3 (AC-3).
    
    Operates on binary constraints between examination variables:
    - Student Clash: If exams Xi and Xj share students, slot(Xi) != slot(Xj).
    - Faculty Clash: If exams Xi and Xj share faculty, slot(Xi) != slot(Xj).
    - Room Clash: If slot(Xi) == slot(Xj), then room(Xi) != room(Xj).
    
    Capabilities:
    1. Standalone AC-3 Domain Reduction: Enforces arc consistency, prunes unsupported values,
       and detects unsolvable states before search.
    2. Integrated Solver: Uses AC-3 as preprocessing and MAC (Maintaining Arc Consistency)
       during backtracking search to guarantee constraint satisfaction.
    """

    def __init__(self, problem: SchedulingProblem):
        super().__init__(problem, "AC-3 with Backtracking")

    def initialize_domains(self) -> Dict[str, Set[Tuple[str, str]]]:
        """
        Initializes domains as sets of (slot_id, room_id) with unary constraints applied:
        - Room capacity >= exam.student_count
        - Slot duration >= exam.duration_hours
        """
        domains: Dict[str, Set[Tuple[str, str]]] = {}
        for eid, exam in self.problem.exams.items():
            compat_rooms = self.problem.compatible_rooms.get(eid, [])
            valid_set: Set[Tuple[str, str]] = set()

            for slot in self.problem.time_slots_list:
                if exam.duration_hours <= slot.duration_hours:
                    for room in compat_rooms:
                        valid_set.add((slot.id, room.id))

            domains[eid] = valid_set
        return domains

    def build_neighbors(self) -> Dict[str, Set[str]]:
        """
        Identifies all neighbor variables that share constraints with each variable:
        - Share students
        - Share faculty
        - Share potential rooms/slots
        """
        neighbors: Dict[str, Set[str]] = {eid: set() for eid in self.problem.exams.keys()}
        exam_ids = list(self.problem.exams.keys())

        for i in range(len(exam_ids)):
            e1 = exam_ids[i]
            for j in range(i + 1, len(exam_ids)):
                e2 = exam_ids[j]
                # Any two exams have at least a mutual room-exclusion constraint if placed in same slot
                # But student and faculty conflicts make the constraint strictly tighter.
                neighbors[e1].add(e2)
                neighbors[e2].add(e1)

        return neighbors

    def satisfies_constraint(
        self,
        var1: str,
        val1: Tuple[str, str],
        var2: str,
        val2: Tuple[str, str],
    ) -> bool:
        """
        Binary constraint satisfaction predicate between var1=val1 and var2=val2.
        Returns True if the assignment pair is mutually legal.
        """
        slot1, room1 = val1
        slot2, room2 = val2

        if slot1 == slot2:
            # Cannot share the same room at the same time
            if room1 == room2:
                return False

            # Cannot share students at the same time
            if self.problem.has_student_conflict(var1, var2):
                return False

            # Cannot share faculty at the same time
            if self.problem.has_faculty_conflict(var1, var2):
                return False

        return True

    def revise(
        self,
        xi: str,
        xj: str,
        domains: Dict[str, Set[Tuple[str, str]]],
    ) -> Tuple[bool, int]:
        """
        The REVISE operation of AC-3.
        Removes any value x in Domain(xi) that has NO supporting value y in Domain(xj)
        satisfying the binary constraint between xi and xj.
        
        Returns:
            (revised_flag, number_of_pruned_values)
        """
        revised = False
        to_remove: Set[Tuple[str, str]] = set()

        for val_i in domains[xi]:
            # Look for at least one support in xj's domain
            has_support = False
            for val_j in domains[xj]:
                if self.satisfies_constraint(xi, val_i, xj, val_j):
                    has_support = True
                    break

            if not has_support:
                to_remove.add(val_i)
                revised = True

        if revised:
            domains[xi] -= to_remove

        return revised, len(to_remove)

    def run_ac3(
        self,
        domains: Dict[str, Set[Tuple[str, str]]],
        neighbors: Dict[str, Set[str]],
        arc_queue: Optional[deque[Tuple[str, str]]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes standard AC-3 algorithm on given domains.
        Returns:
            (is_consistent, stats_dict)
        """
        if arc_queue is None:
            # Initialize with all directed arcs (Xi, Xj)
            arc_queue = deque()
            for xi in self.problem.exams.keys():
                for xj in neighbors.get(xi, set()):
                    arc_queue.append((xi, xj))

        arcs_processed = 0
        arcs_revised = 0
        total_pruned_values = 0

        while arc_queue:
            xi, xj = arc_queue.popleft()
            arcs_processed += 1

            revised, pruned_count = self.revise(xi, xj, domains)
            if revised:
                arcs_revised += 1
                total_pruned_values += pruned_count

                # If domain is wiped out, inconsistency is proven
                if len(domains[xi]) == 0:
                    return False, {
                        "arcs_processed": arcs_processed,
                        "arcs_revised": arcs_revised,
                        "pruned_values": total_pruned_values,
                        "failed_variable": xi,
                    }

                # Add (Xk, Xi) for all neighbors of Xi except Xj
                for xk in neighbors.get(xi, set()):
                    if xk != xj:
                        arc_queue.append((xk, xi))

        return True, {
            "arcs_processed": arcs_processed,
            "arcs_revised": arcs_revised,
            "pruned_values": total_pruned_values,
        }

    def solve(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        use_mac: bool = True,
        timeout_seconds: float = 30.0,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """
        Solves the examination scheduling problem using AC-3 domain reduction
        combined with Backtracking and MAC (Maintaining Arc Consistency).
        """
        start_time = time.time()
        self.explored_states = 0
        backtracks = 0

        domains = self.initialize_domains()
        neighbors = self.build_neighbors()

        # Step 1: Run AC-3 Preprocessing
        initial_domain_sizes = {eid: len(dom) for eid, dom in domains.items()}
        ac3_consistent, ac3_stats = self.run_ac3(domains, neighbors)

        reduced_domain_sizes = {eid: len(dom) for eid, dom in domains.items()}
        total_pruned = ac3_stats["pruned_values"]

        if not ac3_consistent:
            elapsed = time.time() - start_time
            return self._create_result(
                success=False,
                schedule=None,
                execution_time=elapsed,
                details={
                    "ac3_preprocessing": ac3_stats,
                    "initial_domain_sizes": initial_domain_sizes,
                    "reduced_domain_sizes": reduced_domain_sizes,
                    "inconsistency_detected": True,
                },
                message=f"AC-3 detected insoluble constraints during preprocessing: domain of {ac3_stats.get('failed_variable')} was wiped out.",
            )

        # Step 2: Backtracking with MAC
        total_exams = len(self.problem.exams)
        assigned: Dict[str, Tuple[str, str]] = {}

        def select_mrv() -> str:
            unassigned = [e for e in self.problem.exams.keys() if e not in assigned]
            return min(unassigned, key=lambda e: (len(domains[e]), -len(neighbors.get(e, set()))))

        def mac_backtrack() -> Optional[Dict[str, Tuple[str, str]]]:
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
                    f"AC-3 MAC Search (Assigned {len(assigned)}/{total_exams}, States={self.explored_states}, Pruned={total_pruned})...",
                )

            var = select_mrv()
            var_domain = list(domains[var])

            for val in var_domain:
                # Check consistency with currently assigned variables
                consistent = True
                for other_var, other_val in assigned.items():
                    if not self.satisfies_constraint(var, val, other_var, other_val):
                        consistent = False
                        break

                if consistent:
                    assigned[var] = val
                    saved_domains = {e: set(domains[e]) for e in domains.keys()}

                    if use_mac:
                        # Set domain of assigned var to singleton
                        domains[var] = {val}
                        # Queue arcs (Xk, var) for all unassigned neighbors
                        mac_queue = deque((xk, var) for xk in neighbors[var] if xk not in assigned)
                        mac_ok, _ = self.run_ac3(domains, neighbors, mac_queue)

                        if mac_ok:
                            result = mac_backtrack()
                            if result is not None:
                                return result
                    else:
                        result = mac_backtrack()
                        if result is not None:
                            return result

                    # Restore on failure
                    domains.update(saved_domains)
                    assigned.pop(var, None)
                    backtracks += 1

            return None

        final_assigned = mac_backtrack()
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
                    "ac3_preprocessing": ac3_stats,
                    "initial_domain_sizes": initial_domain_sizes,
                    "reduced_domain_sizes": reduced_domain_sizes,
                    "values_pruned": total_pruned,
                    "arcs_processed": ac3_stats["arcs_processed"],
                    "arcs_revised": ac3_stats["arcs_revised"],
                    "mac_enabled": use_mac,
                },
                message=(
                    f"AC-3 with Backtracking found a valid timetable in {elapsed:.3f}s. "
                    f"Pruned {total_pruned} values across domains ({ac3_stats['arcs_processed']} arcs checked)."
                ),
            )

        return self._create_result(
            success=False,
            schedule=None,
            execution_time=elapsed,
            details={
                "explored_states": self.explored_states,
                "backtracks": backtracks,
                "ac3_preprocessing": ac3_stats,
                "initial_domain_sizes": initial_domain_sizes,
                "reduced_domain_sizes": reduced_domain_sizes,
            },
            message=f"AC-3 search failed after {self.explored_states} states and {backtracks} backtracks.",
        )
