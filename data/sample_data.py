"""
Realistic sample university dataset for Examora.
Department of Computer Science & Engineering - End Semester Examination Schedule.
"""
from __future__ import annotations

from typing import Dict, List
from core.models import (
    Exam,
    Room,
    TimeSlot,
    Faculty,
    Student,
    SchedulingProblem,
)


def get_sample_problem() -> SchedulingProblem:
    """
    Constructs a realistic university examination problem:
    - 12 Academic Subjects / Examinations
    - 8 Distinguished Faculty Invigilators
    - 6 Examination Rooms with varied capacities (35 to 120 seats)
    - 5 Examination Days with 2 Sessions each (Morning and Afternoon = 10 Time Slots)
    - 75 Students organized across 3 academic cohorts with realistic cross-elective clashes
    """

    # 1. Faculty Members
    faculty_list = [
        Faculty(id="FAC01", name="Dr. Alan Turing", department="Computer Science", email="turing@university.edu"),
        Faculty(id="FAC02", name="Dr. Ada Lovelace", department="Computer Science", email="lovelace@university.edu"),
        Faculty(id="FAC03", name="Dr. John von Neumann", department="Systems Engineering", email="neumann@university.edu"),
        Faculty(id="FAC04", name="Dr. Grace Hopper", department="Software Engineering", email="hopper@university.edu"),
        Faculty(id="FAC05", name="Dr. Claude Shannon", department="Information Theory", email="shannon@university.edu"),
        Faculty(id="FAC06", name="Dr. Tim Berners-Lee", department="Web Technologies", email="lee@university.edu"),
        Faculty(id="FAC07", name="Dr. Geoffrey Hinton", department="Artificial Intelligence", email="hinton@university.edu"),
        Faculty(id="FAC08", name="Dr. Donald Knuth", department="Algorithms & Computing", email="knuth@university.edu"),
    ]
    faculty_dict = {f.id: f for f in faculty_list}

    # 2. Examination Rooms
    rooms_list = [
        Room(id="R101", name="Hall Alpha", capacity=60, building="Block A"),
        Room(id="R102", name="Hall Beta", capacity=60, building="Block A"),
        Room(id="R201", name="Lecture Theatre 1", capacity=80, building="Block B"),
        Room(id="R202", name="Lecture Theatre 2", capacity=45, building="Block B"),
        Room(id="R301", name="Seminar Room C", capacity=35, building="Block C"),
        Room(id="AUD01", name="Main Auditorium", capacity=120, building="Central Complex"),
    ]
    rooms_dict = {r.id: r for r in rooms_list}

    # 3. Time Slots (5 days x 2 sessions = 10 slots)
    dates = [
        "2026-12-01",
        "2026-12-02",
        "2026-12-03",
        "2026-12-04",
        "2026-12-05",
    ]
    slots_list: List[TimeSlot] = []
    for d in dates:
        slots_list.append(
            TimeSlot(
                id=f"{d}_Morning",
                date_str=d,
                session="Morning",
                start_time="09:30",
                end_time="12:30",
                duration_hours=3.0,
            )
        )
        slots_list.append(
            TimeSlot(
                id=f"{d}_Afternoon",
                date_str=d,
                session="Afternoon",
                start_time="14:00",
                end_time="17:00",
                duration_hours=3.0,
            )
        )

    # 4. Subjects / Examinations
    exams_list = [
        Exam(id="CS101", name="Data Structures & Algorithms", duration_hours=3.0, assigned_faculty_id="FAC08", department="Computer Science"),
        Exam(id="CS102", name="Database Management Systems", duration_hours=3.0, assigned_faculty_id="FAC04", department="Computer Science"),
        Exam(id="CS103", name="Computer Networks", duration_hours=3.0, assigned_faculty_id="FAC05", department="Computer Science"),
        Exam(id="CS104", name="Artificial Intelligence", duration_hours=3.0, assigned_faculty_id="FAC07", department="AI & DS"),
        Exam(id="CS105", name="Operating Systems", duration_hours=3.0, assigned_faculty_id="FAC03", department="Systems"),
        Exam(id="CS106", name="Software Engineering", duration_hours=3.0, assigned_faculty_id="FAC04", department="Software Engineering"),
        Exam(id="CS107", name="Theory of Computation", duration_hours=3.0, assigned_faculty_id="FAC01", department="Computer Science"),
        Exam(id="CS108", name="Machine Learning", duration_hours=3.0, assigned_faculty_id="FAC07", department="AI & DS"),
        Exam(id="CS109", name="Cloud Computing", duration_hours=3.0, assigned_faculty_id="FAC03", department="Systems"),
        Exam(id="CS110", name="Cyber Security", duration_hours=3.0, assigned_faculty_id="FAC05", department="Information Security"),
        Exam(id="CS111", name="Computer Architecture", duration_hours=3.0, assigned_faculty_id="FAC01", department="Hardware & Systems"),
        Exam(id="CS112", name="Web Technologies", duration_hours=3.0, assigned_faculty_id="FAC06", department="Web & Software"),
    ]
    exams_dict = {e.id: e for e in exams_list}

    # 5. Students & Enrollments (Cohort-based with realistic overlaps)
    # Cohort 1: Core Computer Science (Students S001 to S028) -> CS101, CS102, CS103, CS105, CS111
    # Cohort 2: Artificial Intelligence & Data Science (Students S029 to S054) -> CS101, CS102, CS104, CS108, CS109
    # Cohort 3: Cybersecurity & Software (Students S055 to S075) -> CS102, CS103, CS106, CS110, CS112
    # Additional electives:
    # S001 to S010 also enrolled in CS107 (Theory of Computation)
    # S020 to S035 also enrolled in CS106
    # S050 to S065 also enrolled in CS108

    students_dict: Dict[str, Student] = {}

    for i in range(1, 29):
        sid = f"S{i:03d}"
        enrolled = ["CS101", "CS102", "CS103", "CS105", "CS111"]
        if i <= 10:
            enrolled.append("CS107")
        if 20 <= i <= 28:
            enrolled.append("CS106")
        students_dict[sid] = Student(id=sid, name=f"Student {sid}", enrolled_exam_ids=enrolled, department="Computer Science")

    for i in range(29, 55):
        sid = f"S{i:03d}"
        enrolled = ["CS101", "CS102", "CS104", "CS108", "CS109"]
        if 29 <= i <= 35:
            enrolled.append("CS106")
        if i >= 50:
            enrolled.append("CS108")
        students_dict[sid] = Student(id=sid, name=f"Student {sid}", enrolled_exam_ids=enrolled, department="AI & DS")

    for i in range(55, 76):
        sid = f"S{i:03d}"
        enrolled = ["CS102", "CS103", "CS106", "CS110", "CS112"]
        if 55 <= i <= 65:
            enrolled.append("CS108")
        students_dict[sid] = Student(id=sid, name=f"Student {sid}", enrolled_exam_ids=enrolled, department="Cyber Security")

    problem = SchedulingProblem(
        exams=exams_dict,
        rooms=rooms_dict,
        time_slots=slots_list,
        faculty=faculty_dict,
        students=students_dict,
    )
    return problem


def generate_synthetic_dataset(
    num_exams: int = 10,
    num_rooms: int = 5,
    num_days: int = 4,
    num_students: int = 50,
) -> SchedulingProblem:
    """
    Generates a custom synthetic problem of specified scale for testing and benchmarking.
    """
    import random
    rng = random.Random(42)

    # Faculty
    faculty_dict = {
        f"FAC{i+1:02d}": Faculty(id=f"FAC{i+1:02d}", name=f"Prof. Faculty {i+1}", department="Engineering")
        for i in range(max(4, num_exams // 2))
    }
    fac_ids = list(faculty_dict.keys())

    # Rooms
    base_caps = [35, 45, 60, 75, 100, 120]
    rooms_dict = {
        f"R{i+1:02d}": Room(id=f"R{i+1:02d}", name=f"Room {i+1}", capacity=base_caps[i % len(base_caps)])
        for i in range(num_rooms)
    }

    # Time slots
    slots_list: List[TimeSlot] = []
    for day in range(1, num_days + 1):
        d_str = f"2026-12-{day:02d}"
        slots_list.append(TimeSlot(id=f"{d_str}_Morning", date_str=d_str, session="Morning", start_time="09:30", end_time="12:30"))
        slots_list.append(TimeSlot(id=f"{d_str}_Afternoon", date_str=d_str, session="Afternoon", start_time="14:00", end_time="17:00"))

    # Exams
    exams_dict: Dict[str, Exam] = {}
    for i in range(num_exams):
        eid = f"EXAM{i+1:02d}"
        exams_dict[eid] = Exam(
            id=eid,
            name=f"Subject {i+1}",
            duration_hours=3.0,
            assigned_faculty_id=rng.choice(fac_ids),
        )

    # Students & Enrollments
    students_dict: Dict[str, Student] = {}
    exam_ids = list(exams_dict.keys())
    for i in range(num_students):
        sid = f"STU{i+1:03d}"
        # Pick 3 to 5 exams for this student
        k = min(len(exam_ids), rng.randint(3, 5))
        chosen = rng.sample(exam_ids, k=k)
        students_dict[sid] = Student(id=sid, name=f"Student {i+1}", enrolled_exam_ids=chosen)

    return SchedulingProblem(
        exams=exams_dict,
        rooms=rooms_dict,
        time_slots=slots_list,
        faculty=faculty_dict,
        students=students_dict,
    )
