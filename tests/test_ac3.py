"""
Unit tests for Arc Consistency Algorithm 3 (AC-3).
"""
import unittest
from algorithms.ac3 import AC3Scheduler
from data.sample_data import get_sample_problem, generate_synthetic_dataset
from core.constraints import ConstraintChecker


class TestAC3Scheduler(unittest.TestCase):

    def test_ac3_domain_reduction(self):
        """Test that AC-3 performs actual arc consistency checks and domain reduction."""
        problem = get_sample_problem()
        scheduler = AC3Scheduler(problem)

        domains = scheduler.initialize_domains()
        neighbors = scheduler.build_neighbors()

        initial_total_values = sum(len(dom) for dom in domains.values())
        is_consistent, stats = scheduler.run_ac3(domains, neighbors)

        self.assertTrue(is_consistent)
        self.assertGreater(stats["arcs_processed"], 0)
        final_total_values = sum(len(dom) for dom in domains.values())

        # Final domain size must be <= initial domain size
        self.assertLessEqual(final_total_values, initial_total_values)

    def test_ac3_detects_empty_domain_inconsistency(self):
        """Test that AC-3 identifies an empty domain when constraints are mathematically unsatisfiable."""
        problem = generate_synthetic_dataset(num_exams=2, num_rooms=1, num_days=1, num_students=10)
        # Only 1 slot and 1 room exists
        problem.time_slots_list = [problem.time_slots_list[0]]
        # Force both exams to share the same student and faculty
        e1, e2 = list(problem.exams.keys())[:2]
        problem.exams[e1].assigned_faculty_id = "FAC01"
        problem.exams[e2].assigned_faculty_id = "FAC01"
        problem.exams[e1].enrolled_student_ids = ["STU01"]
        problem.exams[e2].enrolled_student_ids = ["STU01"]
        problem._precompute_conflicts()

        scheduler = AC3Scheduler(problem)
        domains = scheduler.initialize_domains()
        neighbors = scheduler.build_neighbors()

        # Artificially constrain e1 to have only the single slot/room
        domains[e1] = {(problem.time_slots_list[0].id, list(problem.rooms.keys())[0])}
        domains[e2] = {(problem.time_slots_list[0].id, list(problem.rooms.keys())[0])}

        # REVISE between e2 and e1 must prune the conflicting value from e2, leaving it empty!
        revised, pruned = scheduler.revise(e2, e1, domains)
        self.assertTrue(revised)
        self.assertEqual(len(domains[e2]), 0)

    def test_ac3_solver_on_sample_problem(self):
        """Test that AC-3 with Backtracking / MAC solves the university sample problem."""
        problem = get_sample_problem()
        scheduler = AC3Scheduler(problem)

        result = scheduler.solve(use_mac=True, timeout_seconds=20.0)
        self.assertTrue(result.success, f"AC-3 solver failed: {result.message}")
        self.assertIsNotNone(result.schedule)
        self.assertEqual(len(result.schedule.assignments), len(problem.exams))
        self.assertEqual(result.hard_violations, 0)
        self.assertIn("arcs_processed", result.details)


if __name__ == "__main__":
    unittest.main()
