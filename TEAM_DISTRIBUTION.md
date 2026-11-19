# Examora – Four-Member Project Team Work Distribution

**Project Title**: Examora – An AI-Powered Intelligent Examination Scheduling and Optimization System  
**Academic Domain**: Artificial Intelligence with Python  
**Institution**: School of Computer Science & Engineering  

---

## 👥 Executive Work Allocation Matrix

| Team Member | Core Algorithm Responsibilities | System Modules Owned | Testing & Quality Assurance | Documentation & Reporting |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1** | **Breadth-First Search (BFS)**<br>**A* Search** | `algorithms/bfs.py`<br>`algorithms/astar.py` | `tests/test_bfs.py`<br>`tests/test_astar.py` | A* Admissibility Proofs & Heuristic Formulation |
| **Member 2** | **Hill Climbing** | `algorithms/hill_climbing.py`<br>`core/cost_function.py` | `tests/test_hill_climbing.py`<br>Local Search Quality Testing | Neighborhood Operators & Trajectory Analysis |
| **Member 3** | **Simulated Annealing** | `algorithms/simulated_annealing.py`<br>`utils/metrics.py` | `tests/test_simulated_annealing.py`<br>Cooling Curve Validation | Thermal Schedules & Stochastic Acceptance Model |
| **Member 4**<br>*(Lead / Architect)* | **CSP Backtracking**<br>**Arc Consistency 3 (AC-3)** | `algorithms/csp_backtracking.py`<br>`algorithms/ac3.py`<br>`core/constraints.py`<br>`interface/app.py` | `tests/test_csp.py`<br>`tests/test_ac3.py`<br>`tests/test_validation.py` | System Architecture, CSP Formulation, Integration & Report |

---

## 📋 Detailed Member Responsibilities

### Member 1: Tree & Heuristic Search Specialist
- **Core Algorithms**:
  - Implemented **Breadth-First Search (BFS)** using a FIFO queue (`collections.deque`), establishing systematic level-by-level state space exploration.
  - Implemented **A* Search** with priority queue (`heapq`), evaluating $f(n) = g(n) + h(n)$.
- **Key Contributions**:
  - Formulated the admissible heuristic $h(n)$ based on minimum theoretical room seat wastage across unassigned examinations.
  - Documented the mathematical proof of admissibility ($h(n) \le h^*(n)$) and analyzed the tree search path-cost divergence phenomenon.
  - Implemented automated test suites in `tests/test_bfs.py` and `tests/test_astar.py`.
  - Collaborated on benchmark comparisons between uninformed (BFS) and informed (A*) search.

### Member 2: Local Search & Trajectory Optimization Specialist
- **Core Algorithm**:
  - Implemented **Hill Climbing** local search optimizer with steepest ascent and random restarts.
- **Key Contributions**:
  - Designed the two primary neighborhood transformation operators:
    1. Single-exam reassignment to alternative time slots and compatible rooms.
    2. Pairwise swap between two examinations with capacity validation.
  - Contributed to `core/cost_function.py`, establishing penalty weights for student spacing and room wastage.
  - Analyzed local optima traps and plateau behaviors in discrete combinatorial scheduling landscapes.
  - Authored unit tests in `tests/test_hill_climbing.py`.

### Member 3: Stochastic Metaheuristics Specialist
- **Core Algorithm**:
  - Implemented **Simulated Annealing** metaheuristic based on the Boltzmann thermodynamic acceptance criterion.
- **Key Contributions**:
  - Calibrated the geometric cooling schedule $T_{k+1} = T_k \times \alpha$, initial temperature $T_0$, and minimum temperature $T_{min}$.
  - Formulated the validity preservation rule: guaranteed that invalid (hard-constraint-violating) states are never accepted as the final accepted schedule.
  - Authored performance metric extractors in `utils/metrics.py` (tracking thermal curves, acceptance rates, and cost histories).
  - Authored unit tests in `tests/test_simulated_annealing.py`.

### Member 4: Constraint Satisfaction, Architecture & Integration Lead
- **Core Algorithms & Architecture**:
  - Modeled the examination timetabling problem as a formal **Constraint Satisfaction Problem (CSP)** $\langle X, D, C \rangle$.
  - Implemented **CSP Backtracking Search** enhanced with **Minimum Remaining Values (MRV)**, Degree Heuristic tie-breaking, and **Forward Checking**.
  - Implemented the genuine **Arc Consistency Algorithm 3 (AC-3)** with queue-based directed arc propagation, the `REVISE(Xi, Xj)` operator, and **Maintaining Arc Consistency (MAC)** integration.
- **Key Contributions**:
  - Designed modular repository architecture and common domain models (`core/models.py`).
  - Implemented comprehensive constraint checker (`core/constraints.py`) and dataset validator (`utils/validation.py`).
  - Built the modern **Streamlit Web Application** (`interface/app.py` and `interface/components.py`).
  - Coordinated overall automated test suite execution and final system integration.

---

## 🤝 Shared Team Responsibilities
All four team members actively participated in:
1. **Realistic Dataset Design**: Co-developed the university benchmark dataset containing 12 subjects, 6 rooms, 10 slots, 8 professors, and 75 students with realistic cross-elective cohort clashes.
2. **Empirical Benchmarking**: Executed all 6 algorithms on the active dataset under identical hardware and constraint conditions, capturing real execution times and state counts.
3. **Academic Documentation**: Contributed to `PROJECT_REPORT.md`, `ALGORITHM_EXPLANATION.md`, and `VIVA_QUESTIONS.md`.
4. **Code Reviews & Quality Assurance**: Verified that zero hard constraints were violated across all generated timetables and ensured 100% test pass rate.
