"""
Unit tests for Breadth-First Search (BFS) Scheduling Algorithm.
"""
import unittest
from algorithms.bfs import BFSScheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestBFSScheduler(unittest.TestCase):

    def test_bfs_on_small_instance(self):
        """Test BFS on a well-constrained small problem to verify exact level-by-level solution."""
        # 4 exams, 4 rooms, 2 slots
        problem = generate_synthetic_dataset(num_exams=4, num_rooms=3, num_days=2, num_students=20)
        scheduler = BFSScheduler(problem)

        result = scheduler.solve(max_states=5000, timeout_seconds=10.0)
        self.assertTrue(result.success, f"BFS failed to find solution: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(len(result.schedule.assignments), len(problem.exams))
        self.assertEqual(result.hard_violations, 0)
        self.assertGreater(result.explored_states, 0)
        self.assertGreater(result.execution_time, 0.0)

    def test_bfs_hard_constraints_enforced(self):
        """Verify that resulting schedule satisfies all hard constraints."""
        problem = generate_synthetic_dataset(num_exams=5, num_rooms=3, num_days=3, num_students=25)
        scheduler = BFSScheduler(problem)

        result = scheduler.solve(max_states=8000, timeout_seconds=15.0)
        if result.success:
            hard_count, violations = ConstraintChecker.check_hard_constraints(result.schedule, problem)
            self.assertEqual(hard_count, 0, f"Violations found: {[v.message for v in violations]}")

    def test_bfs_insoluble_case(self):
        """Verify BFS fails gracefully when no valid schedule is possible (0 compatible rooms)."""
        problem = generate_synthetic_dataset(num_exams=3, num_rooms=1, num_days=1, num_students=10)
        # Make room too small for all exams
        problem.rooms["R01"].capacity = 1
        for e in problem.exams.values():
            e.student_count_override = 50
        problem._precompute_conflicts()

        scheduler = BFSScheduler(problem)
        result = scheduler.solve(max_states=1000, timeout_seconds=5.0)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
