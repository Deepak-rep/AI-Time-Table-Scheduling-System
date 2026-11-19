"""
DataManager for Examora: Handles persistent storage, JSON serialization, CSV imports/exports,
and CRUD operations for exams, rooms, time slots, faculty, and students.
"""
from __future__ import annotations

import csv
import json
import os
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from core.models import (
    Exam,
    Room,
    TimeSlot,
    Faculty,
    Student,
    Schedule,
    SchedulingProblem,
)
from data.sample_data import get_sample_problem


class DataManager:
    """
    Manages persistent state of examination data, import/export operations,
    and updates to problem entities.
    """

    DEFAULT_DATA_FILE = os.path.join(os.path.dirname(__file__), "exam_data.json")

    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file or self.DEFAULT_DATA_FILE
        self._problem: Optional[SchedulingProblem] = None
        self.load_or_initialize()

    @property
    def problem(self) -> SchedulingProblem:
        if self._problem is None:
            self.load_or_initialize()
        return self._problem  # type: ignore

    def load_or_initialize(self) -> SchedulingProblem:
        """Loads data from persistent JSON file; if missing or invalid, initializes sample data."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._problem = SchedulingProblem.from_dict(data)
                return self._problem
            except Exception as e:
                print(f"Warning: Failed to load existing data ({e}). Falling back to sample data.")

        # Initialize with sample problem
        self._problem = get_sample_problem()
        self.save()
        return self._problem

    def save(self) -> None:
        """Persists the current problem to disk in JSON format."""
        if self._problem is not None:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self._problem.to_dict(), f, indent=2)

    def reset_to_sample(self) -> SchedulingProblem:
        """Resets the dataset to the default university benchmark dataset."""
        self._problem = get_sample_problem()
        self.save()
        return self._problem

    # ------------------ CRUD for Exams ------------------
    def add_exam(self, exam: Exam) -> None:
        self.problem.exams[exam.id] = exam
        self.problem._sync_student_enrollments()
        self.problem._precompute_conflicts()
        self.save()

    def update_exam(self, exam: Exam) -> None:
        self.add_exam(exam)

    def delete_exam(self, exam_id: str) -> None:
        self.problem.exams.pop(exam_id, None)
        # Remove from students' enrollments
        for s in self.problem.students.values():
            if exam_id in s.enrolled_exam_ids:
                s.enrolled_exam_ids.remove(exam_id)
        self.problem._precompute_conflicts()
        self.save()

    # ------------------ CRUD for Rooms ------------------
    def add_room(self, room: Room) -> None:
        self.problem.rooms[room.id] = room
        self.problem._precompute_conflicts()
        self.save()

    def update_room(self, room: Room) -> None:
        self.add_room(room)

    def delete_room(self, room_id: str) -> None:
        self.problem.rooms.pop(room_id, None)
        self.problem._precompute_conflicts()
        self.save()

    # ------------------ CRUD for Time Slots ------------------
    def add_slot(self, slot: TimeSlot) -> None:
        if slot.id not in self.problem.time_slots:
            self.problem.time_slots[slot.id] = slot
            self.problem.time_slots_list.append(slot)
            self.save()

    def delete_slot(self, slot_id: str) -> None:
        self.problem.time_slots.pop(slot_id, None)
        self.problem.time_slots_list = [s for s in self.problem.time_slots_list if s.id != slot_id]
        self.save()

    def configure_daily_sessions(
        self,
        dates: List[str],
        sessions: List[Dict[str, str]],
        replace_existing: bool = True,
    ) -> int:
        """
        Configures daily examination sessions across multiple examination dates.
        Each session in `sessions` has:
        - 'name': str, e.g. 'Session 1'
        - 'start': str, e.g. '09:00'
        - 'end': str, e.g. '12:00'
        """
        if replace_existing:
            self.problem.time_slots.clear()
            self.problem.time_slots_list.clear()

        count = 0
        for d in dates:
            for s in sessions:
                s_name = s.get("name") or s.get("session") or f"Session {count + 1}"
                s_start = s.get("start") or s.get("start_time") or "09:30"
                s_end = s.get("end") or s.get("end_time") or "12:30"
                dur = TimeSlot.calculate_duration(s_start, s_end)
                slot_id = f"{d}_{s_name.replace(' ', '_')}"

                slot = TimeSlot(
                    id=slot_id,
                    date_str=d,
                    session=s_name,
                    start_time=s_start,
                    end_time=s_end,
                    duration_hours=dur,
                )
                self.problem.time_slots[slot.id] = slot
                self.problem.time_slots_list.append(slot)
                count += 1

        self.problem._precompute_conflicts()
        self.save()
        return count

    # ------------------ CRUD for Faculty ------------------
    def add_faculty(self, fac: Faculty) -> None:
        self.problem.faculty[fac.id] = fac
        self.problem._precompute_conflicts()
        self.save()

    def delete_faculty(self, fac_id: str) -> None:
        self.problem.faculty.pop(fac_id, None)
        for e in self.problem.exams.values():
            if e.assigned_faculty_id == fac_id:
                e.assigned_faculty_id = ""
        self.problem._precompute_conflicts()
        self.save()

    # ------------------ CRUD for Students ------------------
    def add_student(self, student: Student) -> None:
        self.problem.students[student.id] = student
        self.problem._sync_student_enrollments()
        self.problem._precompute_conflicts()
        self.save()

    def delete_student(self, student_id: str) -> None:
        self.problem.students.pop(student_id, None)
        for e in self.problem.exams.values():
            if student_id in e.enrolled_student_ids:
                e.enrolled_student_ids.remove(student_id)
        self.problem._precompute_conflicts()
        self.save()

    # ------------------ CSV Exports ------------------
    def export_timetable_csv(self, schedule: Schedule) -> str:
        """Exports the generated timetable to a CSV formatted string."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Exam Code",
            "Exam Name",
            "Date",
            "Session",
            "Start Time",
            "End Time",
            "Room ID",
            "Room Name",
            "Room Capacity",
            "Registered Students",
            "Faculty ID",
            "Faculty Name",
            "Duration (Hours)",
        ])

        for eid, assign in sorted(schedule.assignments.items(), key=lambda x: x[1].slot_id):
            exam = self.problem.get_exam(eid)
            slot = self.problem.get_time_slot(assign.slot_id)
            room = self.problem.get_room(assign.room_id)
            fac = self.problem.faculty.get(exam.assigned_faculty_id) if exam else None

            writer.writerow([
                eid,
                exam.name if exam else "",
                slot.date_str if slot else "",
                slot.session if slot else "",
                slot.start_time if slot else "",
                slot.end_time if slot else "",
                room.id if room else "",
                room.name if room else "",
                room.capacity if room else 0,
                exam.student_count if exam else 0,
                fac.id if fac else "",
                fac.name if fac else "",
                exam.duration_hours if exam else 3.0,
            ])

        return output.getvalue()

    def export_exams_csv(self) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Duration_Hours", "Assigned_Faculty_ID", "Student_Count", "Department"])
        for e in self.problem.exams.values():
            writer.writerow([e.id, e.name, e.duration_hours, e.assigned_faculty_id, e.student_count, e.department])
        return output.getvalue()

    def export_rooms_csv(self) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Capacity", "Building"])
        for r in self.problem.rooms.values():
            writer.writerow([r.id, r.name, r.capacity, r.building])
        return output.getvalue()

    # ------------------ CSV Imports ------------------
    def import_exams_csv(self, csv_content: str) -> Tuple[int, List[str]]:
        """Imports examination subjects from CSV string."""
        errors: List[str] = []
        count = 0
        reader = csv.DictReader(StringIO(csv_content))
        for row in reader:
            try:
                eid = row.get("ID") or row.get("id") or row.get("Exam Code", "").strip()
                name = row.get("Name") or row.get("name") or row.get("Exam Name", "").strip()
                if not eid or not name:
                    continue
                dur = float(row.get("Duration_Hours", 3.0))
                fac = row.get("Assigned_Faculty_ID", "").strip()
                dept = row.get("Department", "General").strip()
                count_override = int(row["Student_Count"]) if "Student_Count" in row and row["Student_Count"] else None

                exam = Exam(
                    id=eid,
                    name=name,
                    duration_hours=dur,
                    assigned_faculty_id=fac,
                    student_count_override=count_override,
                    department=dept,
                )
                self.problem.exams[eid] = exam
                count += 1
            except Exception as e:
                errors.append(f"Row error: {e}")

        self.problem._precompute_conflicts()
        self.save()
        return count, errors

    def import_rooms_csv(self, csv_content: str) -> Tuple[int, List[str]]:
        """Imports rooms from CSV string."""
        errors: List[str] = []
        count = 0
        reader = csv.DictReader(StringIO(csv_content))
        for row in reader:
            try:
                rid = row.get("ID") or row.get("id") or row.get("Room ID", "").strip()
                name = row.get("Name") or row.get("name") or row.get("Room Name", "").strip()
                if not rid or not name:
                    continue
                cap = int(row.get("Capacity") or row.get("capacity", 50))
                bldg = row.get("Building", "Main Campus").strip()
                room = Room(id=rid, name=name, capacity=cap, building=bldg)
                self.problem.rooms[rid] = room
                count += 1
            except Exception as e:
                errors.append(f"Row error: {e}")

        self.problem._precompute_conflicts()
        self.save()
        return count, errors
