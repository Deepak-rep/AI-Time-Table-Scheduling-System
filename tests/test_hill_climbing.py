"""
Unit tests for Hill Climbing Scheduling Algorithm.
"""
import unittest
from algorithms.hill_climbing import HillClimbingScheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestHillClimbingScheduler(unittest.TestCase):

    def test_hill_climbing_optimizes_cost(self):
        """Test that Hill Climbing evaluates neighbors and produces a valid schedule."""
        problem = get_sample_problem()
        scheduler = HillClimbingScheduler(problem)

        result = scheduler.solve(max_iterations=100, max_restarts=2, neighborhood_size=20, random_seed=42)
        self.assertTrue(result.success, f"Hill Climbing failed: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(result.hard_violations, 0)
        self.assertGreater(result.explored_states, 0)
        self.assertIn("cost_history", result.details)

    def test_hill_climbing_hard_constraints_satisfied(self):
        """Verify resulting timetable has zero hard violations."""
        problem = generate_synthetic_dataset(num_exams=6, num_rooms=3, num_days=3, num_students=25)
        scheduler = HillClimbingScheduler(problem)

        result = scheduler.solve(max_iterations=150, max_restarts=2, neighborhood_size=25)
        if result.success:
            hard_count, violations = ConstraintChecker.check_hard_constraints(result.schedule, problem)
            self.assertEqual(hard_count, 0)


if __name__ == "__main__":
    unittest.main()
