"""
Validation utilities for inputs, entities, and generated timetables in Examora.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
from core.models import (
    Exam,
    Room,
    TimeSlot,
    Faculty,
    Student,
    Schedule,
    SchedulingProblem,
)
from core.constraints import ConstraintChecker, HardConstraintViolation


class ProblemValidator:
    """
    Validates examination problem setup before running scheduling algorithms.
    Detects logically impossible scheduling requirements early.
    """

    @classmethod
    def validate_problem(cls, problem: SchedulingProblem) -> Tuple[bool, List[str], List[str]]:
        """
        Validates problem feasibility.
        Returns:
            (is_valid, error_list, warning_list)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Basic entity counts
        if not problem.exams:
            errors.append("No examinations defined in dataset.")
        if not problem.rooms:
            errors.append("No examination rooms defined in dataset.")
        if not problem.time_slots_list:
            errors.append("No time slots (dates/sessions) defined in dataset.")

        if errors:
            return False, errors, warnings

        # 2. Total capacity check (Pigeonhole principle)
        total_slots = len(problem.time_slots_list)
        total_rooms = len(problem.rooms)
        max_possible_exams = total_slots * total_rooms

        if len(problem.exams) > max_possible_exams:
            errors.append(
                f"Insufficient physical capacity: {len(problem.exams)} examinations cannot fit into "
                f"{total_slots} time slots with {total_rooms} rooms (maximum capacity = {max_possible_exams})."
            )

        # 3. Individual exam feasibility
        max_room_capacity = max(r.capacity for r in problem.rooms.values())
        max_slot_duration = max(s.duration_hours for s in problem.time_slots_list)

        for eid, exam in problem.exams.items():
            if exam.student_count > max_room_capacity:
                errors.append(
                    f"Exam '{exam.name}' ({eid}) has {exam.student_count} students, but the largest room "
                    f"has capacity {max_room_capacity}."
                )

            if exam.duration_hours > max_slot_duration:
                errors.append(
                    f"Exam '{exam.name}' ({eid}) requires {exam.duration_hours}h duration, "
                    f"which exceeds maximum slot duration ({max_slot_duration}h)."
                )

            compatible = problem.compatible_rooms.get(eid, [])
            if not compatible:
                errors.append(f"Exam '{exam.name}' ({eid}) has 0 compatible rooms.")

            # Faculty verification
            if exam.assigned_faculty_id and exam.assigned_faculty_id not in problem.faculty:
                warnings.append(
                    f"Exam '{exam.name}' references non-existent faculty ID '{exam.assigned_faculty_id}'."
                )

            if exam.student_count == 0:
                warnings.append(f"Exam '{exam.name}' ({eid}) currently has 0 registered students.")

        # 4. Dense student conflict warnings (e.g., student taking more exams than available slots)
        for sid, stu in problem.students.items():
            if len(stu.enrolled_exam_ids) > total_slots:
                errors.append(
                    f"Student '{stu.name}' ({sid}) is enrolled in {len(stu.enrolled_exam_ids)} exams, "
                    f"which exceeds total available time slots ({total_slots}). A clash is mathematically unavoidable."
                )

        is_valid = len(errors) == 0
        return is_valid, errors, warnings


class TimetableValidator:
    """
    Validates a generated schedule against all university examination regulations.
    """

    @classmethod
    def audit_schedule(
        cls, schedule: Schedule, problem: SchedulingProblem
    ) -> Dict[str, Any]:
        """
        Performs a full audit of the timetable and produces a detailed report.
        """
        hard_count, hard_violations = ConstraintChecker.check_hard_constraints(schedule, problem)
        soft_penalty, soft_violations = ConstraintChecker.evaluate_soft_constraints(schedule, problem)

        is_legal = hard_count == 0 and len(schedule.assignments) == len(problem.exams)

        return {
            "is_legal": is_legal,
            "scheduled_exams_count": len(schedule.assignments),
            "total_exams_count": len(problem.exams),
            "hard_violations_count": hard_count,
            "hard_violations": [
                {
                    "type": v.constraint_type,
                    "message": v.message,
                    "involved_exams": v.involved_exams,
                    "slot_id": v.slot_id,
                    "room_id": v.room_id,
                }
                for v in hard_violations
            ],
            "soft_penalty": soft_penalty,
            "soft_violations_count": len(soft_violations),
            "soft_violations_summary": [
                {"type": v.constraint_type, "message": v.message, "penalty": v.penalty}
                for v in soft_violations[:10]
            ],
        }
