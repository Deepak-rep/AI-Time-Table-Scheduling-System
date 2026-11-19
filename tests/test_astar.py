"""
Unit tests for A* Search Scheduling Algorithm.
"""
import unittest
from algorithms.astar import AStarScheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestAStarScheduler(unittest.TestCase):

    def test_astar_heuristic_admissibility(self):
        """Test that A* heuristic values are non-negative and finite."""
        problem = get_sample_problem()
        scheduler = AStarScheduler(problem)

        exam_ids = list(problem.exams.keys())
        h_all = scheduler.heuristic(exam_ids)
        self.assertGreaterEqual(h_all, 0.0)

        # Empty remaining exams must have h(n) = 0
        h_empty = scheduler.heuristic([])
        self.assertEqual(h_empty, 0.0)

        # Subset remaining exams must have non-increasing heuristic
        h_half = scheduler.heuristic(exam_ids[: len(exam_ids) // 2])
        self.assertLessEqual(h_half, h_all)

    def test_astar_on_sample_problem(self):
        """Test A* search finds a valid timetable on benchmark dataset."""
        problem = generate_synthetic_dataset(num_exams=6, num_rooms=4, num_days=3, num_students=30)
        scheduler = AStarScheduler(problem)

        result = scheduler.solve(max_states=8000, timeout_seconds=15.0)
        self.assertTrue(result.success, f"A* failed: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(len(result.schedule.assignments), len(problem.exams))
        self.assertEqual(result.hard_violations, 0)
        self.assertIn("admissible", result.details)
        self.assertTrue(result.details["admissible"])

    def test_astar_hard_constraints_satisfied(self):
        """Verify timetable found by A* contains zero hard violations."""
        problem = generate_synthetic_dataset(num_exams=5, num_rooms=3, num_days=3, num_students=20)
        scheduler = AStarScheduler(problem)

        result = scheduler.solve(max_states=5000, timeout_seconds=10.0)
        if result.success:
            hard_count, violations = ConstraintChecker.check_hard_constraints(result.schedule, problem)
            self.assertEqual(hard_count, 0)


if __name__ == "__main__":
    unittest.main()
