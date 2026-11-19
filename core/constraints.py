"""
Constraint checking and violation tracking for Examora.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from core.models import (
    Exam,
    Room,
    TimeSlot,
    Schedule,
    SchedulingProblem,
    ExamAssignment,
)


@dataclass
class HardConstraintViolation:
    constraint_type: str
    message: str
    involved_exams: List[str]
    slot_id: Optional[str] = None
    room_id: Optional[str] = None


@dataclass
class SoftConstraintViolation:
    constraint_type: str
    message: str
    penalty: float
    involved_exams: List[str] = field(default_factory=list)


class ConstraintChecker:
    """
    Validates hard constraints and computes soft constraint penalties
    for complete or partial examination timetables.
    """

    @staticmethod
    def is_assignment_valid(
        exam_id: str,
        slot_id: str,
        room_id: str,
        schedule: Schedule,
        problem: SchedulingProblem,
    ) -> bool:
        """
        Fast incremental hard constraint check.
        Checks if assigning exam_id to (slot_id, room_id) violates any hard constraints
        given current schedule assignments.
        """
        exam = problem.get_exam(exam_id)
        if not exam:
            return False

        slot = problem.get_time_slot(slot_id)
        if not slot:
            return False

        room = problem.get_room(room_id)
        if not room:
            return False

        # 4. Room capacity must be sufficient
        if room.capacity < exam.student_count:
            return False

        # 6. Duration must be accommodated
        if exam.duration_hours > slot.duration_hours:
            return False

        exam_students = problem.exam_student_sets.get(exam_id, set())
        exam_faculty = exam.assigned_faculty_id

        for other_eid, other_assign in schedule.assignments.items():
            if other_eid == exam_id:
                continue

            # If not in the same slot, no simultaneous clashes can occur
            if other_assign.slot_id != slot_id:
                continue

            # 3. Room clash: A room must not be allocated to multiple examinations simultaneously
            if other_assign.room_id == room_id:
                return False

            # 2. Faculty clash: A faculty member must not be assigned to two exams simultaneously
            other_exam = problem.get_exam(other_eid)
            if other_exam and exam_faculty and other_exam.assigned_faculty_id == exam_faculty:
                return False

            # 1. Student clash: A student must not have two examinations at the same time
            if problem.has_student_conflict(exam_id, other_eid):
                return False

        return True

    @staticmethod
    def check_hard_constraints(
        schedule: Schedule,
        problem: SchedulingProblem,
    ) -> Tuple[int, List[HardConstraintViolation]]:
        """
        Audits the entire schedule for any hard constraint violations.
        Returns total violation count and structured violation objects.
        """
        violations: List[HardConstraintViolation] = []

        # Track usage per slot
        slot_rooms: Dict[Tuple[str, str], List[str]] = defaultdict(list)
        slot_faculty: Dict[Tuple[str, str], List[str]] = defaultdict(list)
        slot_students: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

        # 5. Check if all exams are assigned
        for eid, exam in problem.exams.items():
            assignment = schedule.get_assignment(eid)
            if not assignment:
                violations.append(
                    HardConstraintViolation(
                        constraint_type="UnassignedExam",
                        message=f"Examination '{exam.name}' ({eid}) has not been scheduled.",
                        involved_exams=[eid],
                    )
                )
                continue

            slot = problem.get_time_slot(assignment.slot_id)
            room = problem.get_room(assignment.room_id)

            if not slot or not room:
                violations.append(
                    HardConstraintViolation(
                        constraint_type="InvalidSlotOrRoom",
                        message=f"Exam '{exam.name}' ({eid}) assigned to invalid slot/room.",
                        involved_exams=[eid],
                        slot_id=assignment.slot_id,
                        room_id=assignment.room_id,
                    )
                )
                continue

            # 4. Room capacity
            if room.capacity < exam.student_count:
                violations.append(
                    HardConstraintViolation(
                        constraint_type="RoomCapacityExceeded",
                        message=(
                            f"Room '{room.name}' (capacity {room.capacity}) is too small "
                            f"for exam '{exam.name}' ({eid}) with {exam.student_count} students."
                        ),
                        involved_exams=[eid],
                        slot_id=slot.id,
                        room_id=room.id,
                    )
                )

            # 6. Duration
            if exam.duration_hours > slot.duration_hours:
                violations.append(
                    HardConstraintViolation(
                        constraint_type="DurationExceeded",
                        message=(
                            f"Exam '{exam.name}' duration ({exam.duration_hours}h) exceeds "
                            f"slot '{slot.id}' duration ({slot.duration_hours}h)."
                        ),
                        involved_exams=[eid],
                        slot_id=slot.id,
                    )
                )

            # Record for overlap detection
            slot_rooms[(assignment.slot_id, assignment.room_id)].append(eid)
            if exam.assigned_faculty_id:
                slot_faculty[(assignment.slot_id, exam.assigned_faculty_id)].append(eid)

            students = problem.exam_student_sets.get(eid, set())
            for sid in students:
                slot_students[assignment.slot_id][sid].append(eid)

        # 3. Room clash
        for (slot_id, room_id), eids in slot_rooms.items():
            if len(eids) > 1:
                violations.append(
                    HardConstraintViolation(
                        constraint_type="RoomClash",
                        message=(
                            f"Multiple examinations {eids} assigned to room '{room_id}' "
                            f"simultaneously at slot '{slot_id}'."
                        ),
                        involved_exams=eids,
                        slot_id=slot_id,
                        room_id=room_id,
                    )
                )

        # 2. Faculty clash
        for (slot_id, fac_id), eids in slot_faculty.items():
            if len(eids) > 1:
                fac = problem.faculty.get(fac_id)
                fac_name = fac.name if fac else fac_id
                violations.append(
                    HardConstraintViolation(
                        constraint_type="FacultyClash",
                        message=(
                            f"Faculty '{fac_name}' ({fac_id}) assigned to multiple simultaneous "
                            f"examinations {eids} at slot '{slot_id}'."
                        ),
                        involved_exams=eids,
                        slot_id=slot_id,
                    )
                )

        # 1. Student clash
        for slot_id, student_map in slot_students.items():
            for sid, eids in student_map.items():
                if len(eids) > 1:
                    student = problem.students.get(sid)
                    student_name = student.name if student else sid
                    violations.append(
                        HardConstraintViolation(
                            constraint_type="StudentClash",
                            message=(
                                f"Student '{student_name}' ({sid}) has {len(eids)} simultaneous "
                                f"examinations {eids} at slot '{slot_id}'."
                            ),
                            involved_exams=eids,
                            slot_id=slot_id,
                        )
                    )

        return len(violations), violations

    @staticmethod
    def evaluate_soft_constraints(
        schedule: Schedule,
        problem: SchedulingProblem,
    ) -> Tuple[float, List[SoftConstraintViolation]]:
        """
        Evaluates soft constraints and returns total penalty score plus details.
        
        Soft Constraints:
        1. Minimize consecutive examinations for students:
           - Same day consecutive sessions (Morning & Afternoon): penalty = 20.0 per occurrence
           - Consecutive days: penalty = 5.0 per occurrence
        2. Minimize long gaps between examinations (> 3 days between exams for a student):
           - penalty = 3.0 per excess day
        3. Distribute examinations reasonably across available days:
           - Day load variance penalty: standard deviation / spread penalty
        4. Avoid unnecessary room wastage:
           - Excess capacity penalty: 0.1 per unused seat above student count
        5. Balanced faculty distribution:
           - Faculty load variance penalty
        """
        violations: List[SoftConstraintViolation] = []
        total_penalty = 0.0

        # Pre-group assignments by student
        student_slots: Dict[str, List[Tuple[TimeSlot, str]]] = defaultdict(list)
        exams_per_day: Dict[str, int] = defaultdict(int)
        faculty_counts: Dict[str, int] = defaultdict(int)

        for eid, assignment in schedule.assignments.items():
            exam = problem.get_exam(eid)
            slot = problem.get_time_slot(assignment.slot_id)
            room = problem.get_room(assignment.room_id)

            if not exam or not slot or not room:
                continue

            exams_per_day[slot.date_str] += 1
            if exam.assigned_faculty_id:
                faculty_counts[exam.assigned_faculty_id] += 1

            # 4. Room wastage penalty
            wasted_seats = room.capacity - exam.student_count
            if wasted_seats > 0:
                penalty = wasted_seats * 0.1
                total_penalty += penalty
                if wasted_seats >= 25:  # log significant wastage
                    violations.append(
                        SoftConstraintViolation(
                            constraint_type="RoomWastage",
                            message=(
                                f"Exam '{exam.name}' ({exam.student_count} students) allocated to "
                                f"Room '{room.name}' ({room.capacity} capacity) wasting {wasted_seats} seats."
                            ),
                            penalty=penalty,
                            involved_exams=[eid],
                        )
                    )

            students = problem.exam_student_sets.get(eid, set())
            for sid in students:
                student_slots[sid].append((slot, eid))

        # 1 & 2. Student scheduling spacing (consecutive & gaps)
        for sid, slots_with_exams in student_slots.items():
            if len(slots_with_exams) <= 1:
                continue

            # Sort chronologically by date and session start time
            sorted_slots = sorted(
                slots_with_exams,
                key=lambda x: (x[0].parsed_date, x[0].start_time),
            )

            for i in range(len(sorted_slots) - 1):
                slot1, e1 = sorted_slots[i]
                slot2, e2 = sorted_slots[i + 1]

                day_diff = abs((slot2.parsed_date - slot1.parsed_date).days)

                # Same day consecutive exam
                if day_diff == 0:
                    penalty = 20.0
                    total_penalty += penalty
                    student_obj = problem.students.get(sid)
                    s_name = student_obj.name if student_obj else sid
                    violations.append(
                        SoftConstraintViolation(
                            constraint_type="SameDayConsecutive",
                            message=f"Student '{s_name}' has 2 exams on the same day ({slot1.date_str}) in {e1} and {e2}.",
                            penalty=penalty,
                            involved_exams=[e1, e2],
                        )
                    )
                # Next day consecutive exam
                elif day_diff == 1:
                    penalty = 5.0
                    total_penalty += penalty
                # Long gap (> 3 days)
                elif day_diff > 3:
                    excess = day_diff - 3
                    penalty = excess * 3.0
                    total_penalty += penalty

        # 3. Daily distribution balance
        all_dates = {s.date_str for s in problem.time_slots_list}
        if all_dates:
            day_counts = [exams_per_day[d] for d in all_dates]
            mean_exams = sum(day_counts) / len(all_dates)
            variance = sum((c - mean_exams) ** 2 for c in day_counts) / len(all_dates)
            distribution_penalty = variance * 5.0
            total_penalty += distribution_penalty
            if distribution_penalty > 10.0:
                violations.append(
                    SoftConstraintViolation(
                        constraint_type="UnevenDayDistribution",
                        message=f"Exam load is unevenly distributed across dates (daily counts: {dict(exams_per_day)}).",
                        penalty=distribution_penalty,
                    )
                )

        # 5. Faculty workload balance
        if problem.faculty:
            fac_counts = [faculty_counts[fid] for fid in problem.faculty.keys()]
            if fac_counts:
                mean_fac = sum(fac_counts) / len(fac_counts)
                fac_var = sum((c - mean_fac) ** 2 for c in fac_counts) / len(fac_counts)
                fac_penalty = fac_var * 4.0
                total_penalty += fac_penalty

        return round(total_penalty, 2), violations
