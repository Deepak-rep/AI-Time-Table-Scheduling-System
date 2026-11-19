"""
Tests for constraints and validation logic.
"""
import unittest
from core.models import (
    Exam,
    Room,
    TimeSlot,
    Faculty,
    Student,
    Schedule,
    SchedulingProblem,
)
from core.constraints import ConstraintChecker
from core.cost_function import CostEvaluator
from utils.validation import ProblemValidator, TimetableValidator
from data.sample_data import get_sample_problem


class TestValidationAndConstraints(unittest.TestCase):

    def setUp(self):
        self.problem = get_sample_problem()

    def test_sample_problem_validity(self):
        """Verify the default university sample problem passes feasibility validation."""
        is_valid, errors, warnings = ProblemValidator.validate_problem(self.problem)
        self.assertTrue(is_valid, f"Sample problem failed validation with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_hard_constraint_room_capacity(self):
        """Test that room capacity violation is detected when exam students exceed room size."""
        schedule = Schedule()
        # Find small room and large exam
        small_room = next(r for r in self.problem.rooms.values() if r.capacity < 40)
        large_exam = next(e for e in self.problem.exams.values() if e.student_count > 40)
        slot = self.problem.time_slots_list[0]

        # Assign large exam to small room
        schedule.assign(large_exam.id, slot.id, small_room.id)

        # Fill remaining with dummy valid or test check
        hard_count, violations = ConstraintChecker.check_hard_constraints(schedule, self.problem)
        capacity_violations = [v for v in violations if v.constraint_type == "RoomCapacityExceeded"]
        self.assertGreater(len(capacity_violations), 0)
        self.assertIn(large_exam.id, capacity_violations[0].involved_exams)

    def test_hard_constraint_student_clash(self):
        """Test that two exams sharing students scheduled in the same slot triggers student clash."""
        schedule = Schedule()
        # Find two exams that share students
        conflict_pair = list(self.problem.student_conflicts.keys())[0]
        e1, e2 = conflict_pair

        slot = self.problem.time_slots_list[0]
        rooms = list(self.problem.rooms.values())
        r1, r2 = rooms[0], rooms[1]

        # Assign both to the SAME slot in different rooms
        schedule.assign(e1, slot.id, r1.id)
        schedule.assign(e2, slot.id, r2.id)

        hard_count, violations = ConstraintChecker.check_hard_constraints(schedule, self.problem)
        student_clashes = [v for v in violations if v.constraint_type == "StudentClash"]
        self.assertGreater(len(student_clashes), 0)

    def test_hard_constraint_faculty_clash(self):
        """Test that two exams with same faculty in the same slot triggers faculty clash."""
        schedule = Schedule()
        # Find two exams sharing faculty
        conflict_pair = list(self.problem.faculty_conflicts.keys())[0]
        e1, e2 = conflict_pair

        slot = self.problem.time_slots_list[0]
        rooms = list(self.problem.rooms.values())
        r1, r2 = rooms[0], rooms[1]

        schedule.assign(e1, slot.id, r1.id)
        schedule.assign(e2, slot.id, r2.id)

        hard_count, violations = ConstraintChecker.check_hard_constraints(schedule, self.problem)
        faculty_clashes = [v for v in violations if v.constraint_type == "FacultyClash"]
        self.assertGreater(len(faculty_clashes), 0)

    def test_hard_constraint_room_clash(self):
        """Test that two exams allocated to the same room simultaneously triggers room clash."""
        schedule = Schedule()
        exam_ids = list(self.problem.exams.keys())
        e1, e2 = exam_ids[0], exam_ids[1]

        slot = self.problem.time_slots_list[0]
        room = self.problem.rooms_list[0] if hasattr(self.problem, 'rooms_list') else list(self.problem.rooms.values())[0]

        # Same slot, same room
        schedule.assign(e1, slot.id, room.id)
        schedule.assign(e2, slot.id, room.id)

        hard_count, violations = ConstraintChecker.check_hard_constraints(schedule, self.problem)
        room_clashes = [v for v in violations if v.constraint_type == "RoomClash"]
        self.assertGreater(len(room_clashes), 0)

    def test_impossible_problem_detection(self):
        """Test that ProblemValidator catches impossible setups (e.g. exams > total slots * rooms)."""
        # Create problem with 100 exams but only 1 room and 1 slot
        bad_problem = SchedulingProblem(
            exams={f"E{i}": Exam(id=f"E{i}", name=f"Exam {i}") for i in range(10)},
            rooms={"R1": Room(id="R1", name="R1", capacity=100)},
            time_slots=[TimeSlot(id="S1", date_str="2026-12-01", session="Morning", start_time="09:30", end_time="12:30")],
            faculty={},
            students={},
        )
        is_valid, errors, _ = ProblemValidator.validate_problem(bad_problem)
        self.assertFalse(is_valid)
        self.assertTrue(any("capacity" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
