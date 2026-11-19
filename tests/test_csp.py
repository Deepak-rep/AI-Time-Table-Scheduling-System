"""
Unit tests for Constraint Satisfaction Problem (CSP) Backtracking Algorithm.
"""
import unittest
from algorithms.csp_backtracking import CSPBacktrackingScheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestCSPBacktrackingScheduler(unittest.TestCase):

    def test_csp_solves_sample_problem(self):
        """Test that CSP Backtracking with MRV and Forward Checking finds a valid schedule."""
        problem = get_sample_problem()
        scheduler = CSPBacktrackingScheduler(problem)

        result = scheduler.solve(use_mrv=True, use_forward_checking=True, timeout_seconds=20.0)
        self.assertTrue(result.success, f"CSP Backtracking failed: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(len(result.schedule.assignments), len(problem.exams))
        self.assertEqual(result.hard_violations, 0)
        self.assertIn("backtracks", result.details)

    def test_csp_without_mrv(self):
        """Test CSP Backtracking works without MRV on a small synthetic instance."""
        problem = generate_synthetic_dataset(num_exams=5, num_rooms=3, num_days=3, num_students=20)
        scheduler = CSPBacktrackingScheduler(problem)

        result = scheduler.solve(use_mrv=False, use_forward_checking=True, timeout_seconds=10.0)
        self.assertTrue(result.success)
        self.assertEqual(result.hard_violations, 0)

    def test_csp_unsolvable_case(self):
        """Test that CSP detects unsolvable problem and reports failure gracefully."""
        problem = generate_synthetic_dataset(num_exams=3, num_rooms=1, num_days=1, num_students=10)
        # Force all 3 exams to have same faculty and same students, but only 1 slot and 1 room exists
        problem.time_slots_list = [problem.time_slots_list[0]]
        for e in problem.exams.values():
            e.assigned_faculty_id = "FAC01"
            e.enrolled_student_ids = ["STU01"]
        problem._precompute_conflicts()

        scheduler = CSPBacktrackingScheduler(problem)
        result = scheduler.solve(timeout_seconds=5.0)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
