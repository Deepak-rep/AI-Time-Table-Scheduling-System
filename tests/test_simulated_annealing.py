"""
Unit tests for Simulated Annealing Scheduling Algorithm.
"""
import unittest
from algorithms.simulated_annealing import SimulatedAnnealingScheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestSimulatedAnnealingScheduler(unittest.TestCase):

    def test_simulated_annealing_execution(self):
        """Test that Simulated Annealing runs and produces a valid timetable."""
        problem = get_sample_problem()
        scheduler = SimulatedAnnealingScheduler(problem)

        result = scheduler.solve(
            initial_temperature=50.0,
            cooling_rate=0.95,
            min_temperature=0.1,
            max_iterations=200,
            random_seed=42,
        )
        self.assertTrue(result.success, f"Simulated Annealing failed: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(result.hard_violations, 0)
        self.assertIn("acceptance_rate_percent", result.details)
        self.assertIn("temp_history", result.details)

    def test_simulated_annealing_never_accepts_invalid_final_schedule(self):
        """Verify that hard constraints are strictly 0 in final result."""
        problem = generate_synthetic_dataset(num_exams=7, num_rooms=4, num_days=3, num_students=30)
        scheduler = SimulatedAnnealingScheduler(problem)

        result = scheduler.solve(max_iterations=300, random_seed=123)
        if result.success:
            hard_count, violations = ConstraintChecker.check_hard_constraints(result.schedule, problem)
            self.assertEqual(hard_count, 0)
            self.assertEqual(result.hard_violations, 0)


if __name__ == "__main__":
    unittest.main()
