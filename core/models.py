"""
Data models for Examora Examination Scheduling System.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass(frozen=True)
class TimeSlot:
    """Represents a specific exam session on a specific date."""
    id: str  # e.g., "2026-12-01_Morning"
    date_str: str  # "YYYY-MM-DD"
    session: str  # "Morning", "Afternoon", etc.
    start_time: str  # "09:30"
    end_time: str  # "12:30"
    duration_hours: float = 3.0

    @property
    def parsed_date(self) -> date:
        try:
            return datetime.strptime(self.date_str, "%Y-%m-%d").date()
        except ValueError:
            return date(2026, 1, 1)

    def is_same_day(self, other: TimeSlot) -> bool:
        return self.date_str == other.date_str

    def days_between(self, other: TimeSlot) -> int:
        return abs((self.parsed_date - other.parsed_date).days)

    @staticmethod
    def calculate_duration(start_time: str, end_time: str) -> float:
        """Calculates duration in hours from 'HH:MM' start and end time strings."""
        try:
            parts1 = [int(p) for p in start_time.strip().split(":")]
            parts2 = [int(p) for p in end_time.strip().split(":")]
            m1 = parts1[0] * 60 + (parts1[1] if len(parts1) > 1 else 0)
            m2 = parts2[0] * 60 + (parts2[1] if len(parts2) > 1 else 0)
            diff_min = m2 - m1
            if diff_min <= 0:
                diff_min += 24 * 60  # overnight wrap if any
            return max(0.5, round(diff_min / 60.0, 2))
        except Exception:
            return 3.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date_str": self.date_str,
            "session": self.session,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_hours": self.duration_hours,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimeSlot:
        return cls(
            id=data["id"],
            date_str=data.get("date_str") or data.get("date", "2026-12-01"),
            session=data["session"],
            start_time=data.get("start_time", "09:30"),
            end_time=data.get("end_time", "12:30"),
            duration_hours=float(data.get("duration_hours", 3.0)),
        )


@dataclass
class Room:
    """Represents a physical room/hall where an exam can be conducted."""
    id: str
    name: str
    capacity: int
    building: str = "Main Campus"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "building": self.building,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Room:
        return cls(
            id=data["id"],
            name=data["name"],
            capacity=int(data["capacity"]),
            building=data.get("building", "Main Campus"),
        )


@dataclass
class Faculty:
    """Represents an instructor or invigilator assigned to examinations."""
    id: str
    name: str
    department: str = "General"
    email: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Faculty:
        return cls(
            id=data["id"],
            name=data["name"],
            department=data.get("department", "General"),
            email=data.get("email", ""),
        )


@dataclass
class Student:
    """Represents a student enrolled in one or more subjects."""
    id: str
    name: str
    enrolled_exam_ids: List[str] = field(default_factory=list)
    department: str = "General"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "enrolled_exam_ids": list(self.enrolled_exam_ids),
            "department": self.department,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Student:
        return cls(
            id=data["id"],
            name=data["name"],
            enrolled_exam_ids=list(data.get("enrolled_exam_ids", [])),
            department=data.get("department", "General"),
        )


@dataclass
class Exam:
    """Represents an examination subject."""
    id: str
    name: str
    duration_hours: float = 3.0
    assigned_faculty_id: str = ""
    enrolled_student_ids: List[str] = field(default_factory=list)
    student_count_override: Optional[int] = None
    department: str = "General"

    @property
    def student_count(self) -> int:
        if self.student_count_override is not None and self.student_count_override > 0:
            return self.student_count_override
        return len(self.enrolled_student_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "duration_hours": self.duration_hours,
            "assigned_faculty_id": self.assigned_faculty_id,
            "enrolled_student_ids": list(self.enrolled_student_ids),
            "student_count_override": self.student_count_override,
            "department": self.department,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Exam:
        return cls(
            id=data["id"],
            name=data["name"],
            duration_hours=float(data.get("duration_hours", 3.0)),
            assigned_faculty_id=data.get("assigned_faculty_id", ""),
            enrolled_student_ids=list(data.get("enrolled_student_ids", [])),
            student_count_override=data.get("student_count_override"),
            department=data.get("department", "General"),
        )


@dataclass(frozen=True)
class ExamAssignment:
    """Assignment of an exam to a specific time slot and room."""
    exam_id: str
    slot_id: str
    room_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "slot_id": self.slot_id,
            "room_id": self.room_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExamAssignment:
        return cls(
            exam_id=data["exam_id"],
            slot_id=data["slot_id"],
            room_id=data["room_id"],
        )


@dataclass
class Schedule:
    """Represents an exam timetable (partial or complete)."""
    assignments: Dict[str, ExamAssignment] = field(default_factory=dict)

    def assign(self, exam_id: str, slot_id: str, room_id: str) -> None:
        self.assignments[exam_id] = ExamAssignment(exam_id=exam_id, slot_id=slot_id, room_id=room_id)

    def unassign(self, exam_id: str) -> None:
        self.assignments.pop(exam_id, None)

    def get_assignment(self, exam_id: str) -> Optional[ExamAssignment]:
        return self.assignments.get(exam_id)

    def is_complete(self, total_exams: int) -> bool:
        return len(self.assignments) >= total_exams

    def copy(self) -> Schedule:
        return Schedule(assignments=dict(self.assignments))

    def to_dict(self) -> Dict[str, Any]:
        return {
            exam_id: assign.to_dict()
            for exam_id, assign in self.assignments.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Schedule:
        assignments = {
            exam_id: ExamAssignment.from_dict(val)
            for exam_id, val in data.items()
        }
        return cls(assignments=assignments)


class SchedulingProblem:
    """
    Encapsulates all entities, variables, domains, and precomputed conflicts
    for the examination scheduling task.
    """
    def __init__(
        self,
        exams: Dict[str, Exam],
        rooms: Dict[str, Room],
        time_slots: List[TimeSlot],
        faculty: Dict[str, Faculty],
        students: Dict[str, Student],
    ):
        self.exams = exams
        self.rooms = rooms
        self.time_slots = {slot.id: slot for slot in time_slots}
        self.time_slots_list = list(time_slots)
        self.faculty = faculty
        self.students = students

        # Synchronize student enrollments with exam enrolled_student_ids
        self._sync_student_enrollments()

        # Precompute conflicts for quick lookup
        self._precompute_conflicts()

    def _sync_student_enrollments(self) -> None:
        """Ensures bidirectional consistency between students and exams."""
        for student in self.students.values():
            for exam_id in student.enrolled_exam_ids:
                if exam_id in self.exams:
                    if student.id not in self.exams[exam_id].enrolled_student_ids:
                        self.exams[exam_id].enrolled_student_ids.append(student.id)

        for exam in self.exams.values():
            for s_id in exam.enrolled_student_ids:
                if s_id in self.students:
                    if exam.id not in self.students[s_id].enrolled_exam_ids:
                        self.students[s_id].enrolled_exam_ids.append(exam.id)

    def _precompute_conflicts(self) -> None:
        """
        Precompute:
        1. Student conflict graph: which pairs of exams share students
        2. Faculty conflict graph: which pairs of exams share faculty
        3. Valid rooms per exam (room capacity >= exam student count)
        """
        self.student_conflicts: Dict[Tuple[str, str], Set[str]] = {}
        self.faculty_conflicts: Dict[Tuple[str, str], str] = {}
        self.exam_student_sets: Dict[str, Set[str]] = {
            exam_id: set(exam.enrolled_student_ids)
            for exam_id, exam in self.exams.items()
        }

        exam_ids = list(self.exams.keys())
        for i in range(len(exam_ids)):
            e1 = exam_ids[i]
            for j in range(i + 1, len(exam_ids)):
                e2 = exam_ids[j]
                common_students = self.exam_student_sets[e1] & self.exam_student_sets[e2]
                if common_students:
                    self.student_conflicts[(e1, e2)] = common_students
                    self.student_conflicts[(e2, e1)] = common_students

                f1 = self.exams[e1].assigned_faculty_id
                f2 = self.exams[e2].assigned_faculty_id
                if f1 and f2 and f1 == f2:
                    self.faculty_conflicts[(e1, e2)] = f1
                    self.faculty_conflicts[(e2, e1)] = f1

        # Precompute compatible rooms based on capacity
        self.compatible_rooms: Dict[str, List[Room]] = {}
        for exam_id, exam in self.exams.items():
            valid_rooms = [
                r for r in self.rooms.values()
                if r.capacity >= exam.student_count
            ]
            self.compatible_rooms[exam_id] = valid_rooms

    def has_student_conflict(self, exam1_id: str, exam2_id: str) -> bool:
        return (exam1_id, exam2_id) in self.student_conflicts

    def get_common_students(self, exam1_id: str, exam2_id: str) -> Set[str]:
        return self.student_conflicts.get((exam1_id, exam2_id), set())

    def has_faculty_conflict(self, exam1_id: str, exam2_id: str) -> bool:
        return (exam1_id, exam2_id) in self.faculty_conflicts

    def get_time_slot(self, slot_id: str) -> Optional[TimeSlot]:
        return self.time_slots.get(slot_id)

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_exam(self, exam_id: str) -> Optional[Exam]:
        return self.exams.get(exam_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exams": {eid: exam.to_dict() for eid, exam in self.exams.items()},
            "rooms": {rid: room.to_dict() for rid, room in self.rooms.items()},
            "time_slots": [slot.to_dict() for slot in self.time_slots_list],
            "faculty": {fid: fac.to_dict() for fid, fac in self.faculty.items()},
            "students": {sid: stu.to_dict() for sid, stu in self.students.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SchedulingProblem:
        exams = {eid: Exam.from_dict(v) for eid, v in data.get("exams", {}).items()}
        rooms = {rid: Room.from_dict(v) for rid, v in data.get("rooms", {}).items()}
        slots = [TimeSlot.from_dict(v) for v in data.get("time_slots", [])]
        faculty = {fid: Faculty.from_dict(v) for fid, v in data.get("faculty", {}).items()}
        students = {sid: Student.from_dict(v) for sid, v in data.get("students", {}).items()}
        return cls(exams=exams, rooms=rooms, time_slots=slots, faculty=faculty, students=students)


@dataclass
class AlgorithmResult:
    """Results returned by any of the 6 scheduling algorithms."""
    algorithm_name: str
    success: bool
    schedule: Optional[Schedule]
    execution_time: float  # seconds
    explored_states: int
    hard_violations: int = 0
    soft_penalty: float = 0.0
    total_cost: float = 0.0
    violation_details: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_name": self.algorithm_name,
            "success": self.success,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "execution_time": round(self.execution_time, 4),
            "explored_states": self.explored_states,
            "hard_violations": self.hard_violations,
            "soft_penalty": round(self.soft_penalty, 2),
            "total_cost": round(self.total_cost, 2),
            "violation_details": self.violation_details,
            "details": self.details,
            "message": self.message,
        }
