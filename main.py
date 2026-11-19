"""
Main entry point for Examora: An AI-Powered Intelligent Examination Scheduling and Optimization System.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from core.scheduler import ExamScheduler
from data.data_manager import DataManager
from utils.metrics import BenchmarkAnalyzer


def run_benchmark_cli():
    print("=" * 70)
    print("EXAMORA: ACADEMIC BENCHMARK EVALUATION (ALL 6 AI ALGORITHMS)")
    print("=" * 70)
    dm = DataManager()
    problem = dm.problem
    print(f"Problem: {len(problem.exams)} exams, {len(problem.rooms)} rooms, "
          f"{len(problem.time_slots_list)} slots, {len(problem.students)} students.")
    print("-" * 70)

    scheduler = ExamScheduler(problem)
    results = scheduler.compare_all()

    rows = BenchmarkAnalyzer.create_comparison_rows(results, total_exams=len(problem.exams))
    
    # Print formatted table
    headers = ["Algorithm", "Status", "Time (s)", "States", "Hard", "Soft", "Cost", "Quality"]
    print(f"{headers[0]:<28} | {headers[1]:<10} | {headers[2]:<8} | {headers[3]:<7} | {headers[4]:<4} | {headers[5]:<6} | {headers[6]:<7} | {headers[7]:<7}")
    print("-" * 95)
    for r in rows:
        print(f"{r['Algorithm']:<28} | {r['Status']:<10} | {r['Execution Time (s)']:<8.4f} | {r['Explored States']:<7} | {r['Hard Violations']:<4} | {r['Soft Penalty']:<6.1f} | {r['Total Cost']:<7.1f} | {r['Quality Score (%)']:<6.1f}%")
    print("-" * 95)

    rankings = BenchmarkAnalyzer.get_rankings(rows)
    print(f"\n🏆 Fastest Algorithm:         {rankings['fastest']}")
    print(f"🧠 Most Memory-Efficient:      {rankings['most_efficient']}")
    print(f"🎯 Highest Solution Quality:   {rankings['best_quality']}")
    print("=" * 70)


def run_single_algorithm_cli(algo_name: str):
    print(f"Running algorithm: {algo_name}...")
    dm = DataManager()
    problem = dm.problem
    scheduler = ExamScheduler(problem)
    result = scheduler.run_algorithm(algo_name)

    print("-" * 60)
    print(f"Algorithm:       {result.algorithm_name}")
    print(f"Success:         {result.success}")
    print(f"Execution Time:  {result.execution_time:.4f} seconds")
    print(f"Explored States: {result.explored_states}")
    print(f"Hard Violations: {result.hard_violations}")
    print(f"Soft Penalty:    {result.soft_penalty:.2f}")
    print(f"Total Cost:      {result.total_cost:.2f}")
    print(f"Message:         {result.message}")
    print("-" * 60)


def launch_web_ui():
    app_path = os.path.join(os.path.dirname(__file__), "interface", "app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print(f"Launching Examora Web Application: {' '.join(cmd)}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nExamora server stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Examora: AI-Powered Examination Scheduling System"
    )
    parser.add_argument(
        "--web", action="store_true", help="Launch Streamlit web interface (default if no flags)"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Execute CLI benchmark across all 6 algorithms"
    )
    parser.add_argument(
        "--algo", type=str, help="Execute specific algorithm via CLI (e.g., 'CSP Backtracking', 'A* Search', 'AC-3', etc.)"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run automated test suite"
    )

    args = parser.parse_args()

    if args.benchmark:
        run_benchmark_cli()
    elif args.algo:
        run_single_algorithm_cli(args.algo)
    elif args.test:
        import unittest
        suite = unittest.defaultTestLoader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        launch_web_ui()


if __name__ == "__main__":
    main()
