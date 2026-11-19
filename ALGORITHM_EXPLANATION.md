# Comprehensive Algorithmic Explanation – Examora

**System Title**: Examora – An AI-Powered Intelligent Examination Scheduling and Optimization System  
**Academic Domain**: Artificial Intelligence & Optimization with Python  

This document provides a rigorous mathematical and algorithmic breakdown of the six Artificial Intelligence algorithms implemented in **Examora**.

---

## 1. Mathematical Formulation of Examination Timetabling

An examination timetabling problem is formally specified as a tuple:

$$\mathcal{P} = \langle \mathcal{E}, \mathcal{R}, \mathcal{T}, \mathcal{F}, \mathcal{S}, \mathcal{H}, \mathcal{C}_{soft} \rangle$$

Where:
- $\mathcal{E} = \{e_1, e_2, \dots, e_N\}$ is the set of examinations (courses).
- $\mathcal{R} = \{r_1, r_2, \dots, r_M\}$ is the set of available examination rooms, each with seating capacity $cap(r)$.
- $\mathcal{T} = \{t_1, t_2, \dots, t_K\}$ is the set of available time slots (date + session, e.g. Day 1 Morning, Day 1 Afternoon), each with duration $dur(t)$.
- $\mathcal{F} = \{f_1, f_2, \dots, f_P\}$ is the faculty invigilator pool.
- $\mathcal{S} = \{s_1, s_2, \dots, s_Q\}$ is the enrolled student body.
- $\mathcal{H}$ is the set of inviolable Hard Constraints.
- $\mathcal{C}_{soft}$ is the soft constraint penalty function to be minimized.

A complete assignment is a mapping $\sigma: \mathcal{E} \to \mathcal{T} \times \mathcal{R}$ such that:
$$\sigma(e) = (slot(e), room(e))$$

### Inviolable Hard Constraints ($\mathcal{H}$)
1. **Student Conflict-Free**:
   $$\forall e_i, e_j \in \mathcal{E}, \quad (\text{Students}(e_i) \cap \text{Students}(e_j) \neq \emptyset) \implies slot(e_i) \neq slot(e_j)$$
2. **Faculty Conflict-Free**:
   $$\forall e_i, e_j \in \mathcal{E}, \quad (fac(e_i) = fac(e_j) \neq \emptyset) \implies slot(e_i) \neq slot(e_j)$$
3. **Room Exclusivity**:
   $$\forall e_i, e_j \in \mathcal{E}, \quad (slot(e_i) = slot(e_j)) \implies room(e_i) \neq room(e_j)$$
4. **Room Capacity Sufficiency**:
   $$\forall e \in \mathcal{E}, \quad cap(room(e)) \ge |\text{Students}(e)|$$
5. **Temporal Duration Compatibility**:
   $$\forall e \in \mathcal{E}, \quad dur(slot(e)) \ge dur(e)$$
6. **Total Assignment Completeness**:
   $$\forall e \in \mathcal{E}, \quad \sigma(e) \neq \text{None}$$

### Objective / Cost Function ($f(S)$)
$$f(S) = W_{hard} \cdot \sum_{h \in \mathcal{H}} \text{Violations}(h) + \mathcal{C}_{soft}(S)$$
where $W_{hard} = 10,000.0$. In any accepted valid schedule, $\sum \text{Violations}(h) = 0$, reducing $f(S)$ to $\mathcal{C}_{soft}(S)$.

$$\mathcal{C}_{soft}(S) = \omega_1 \cdot \text{Wastage} + \omega_2 \cdot \text{SameDayConsecutive} + \omega_3 \cdot \text{NextDayConsecutive} + \omega_4 \cdot \text{DayVariance}$$

---

## 2. Algorithm 1: Breadth-First Search (BFS)

### A. Theoretical Foundation
Breadth-First Search is an uninformed graph search strategy that expands the search tree level by level. In Examora:
- **Level $k$**: Exactly $k$ examinations have been assigned.
- **Node**: A partial schedule represented by an immutable tuple of triples:
  $$\text{State} = ((e_1, t_1, r_1), (e_2, t_2, r_2), \dots, (e_k, t_k, r_k))$$
- **Frontier / Open List**: A First-In-First-Out (FIFO) queue (`collections.deque`).

### B. Pruning & Constraint Validation
To prevent exponential divergence into illegal spaces, BFS validates hard constraints during state generation:
$$\text{is\_valid}(e_{k+1}, t, r, \text{partial\_schedule})$$
Only valid triples are enqueued into the frontier. Visited states are cached to prevent duplicate expansions.

### C. Complexity & Properties
- **Time Complexity**: $O(b^d)$, where $b = |\mathcal{T}| \times |\mathcal{R}_{compatible}|$ and $d = |\mathcal{E}|$.
- **Space Complexity**: $O(b^d)$, as all frontier nodes must be maintained in memory.
- **Completeness**: Complete. If a valid schedule exists, BFS is guaranteed to find one.
- **Optimality**: Finds the shallowest solution (all complete schedules have identical depth $N$). However, because it does not evaluate soft penalties, it does not guarantee soft-constraint optimality.
- **Practical Observation**: For small instances ($N \le 6$), BFS finds solutions quickly. For large university datasets ($N \ge 12$), the branching factor ($b \approx 60$) causes state explosion ($60^{12} \approx 2.1 \times 10^{21}$ combinations), leading to exhaustion of memory or state limits.

---

## 3. Algorithm 2: A* Search

### A. Theoretical Foundation
A* is an informed best-first search algorithm that directs its exploration toward the goal using an evaluation function:
$$f(n) = g(n) + h(n)$$

Where:
- $g(n)$: The accumulated cost incurred by the partial schedule so far (actual soft penalties: room capacity wastage + student spacing penalties).
- $h(n)$: The estimated remaining cost from node $n$ to the complete schedule.

### B. Admissible Heuristic Formulation
The heuristic $h(n)$ estimates the unavoidable room seat wastage across all currently unassigned examinations:
$$h(n) = \sum_{u \in \text{Unassigned}(n)} \min_{r \in \mathcal{R}_{compat}(u)} \left[ 0.1 \cdot (cap(r) - |\text{Students}(u)|) \right]$$

### C. Mathematical Proof of Admissibility
**Theorem**: $h(n)$ is admissible ($h(n) \le h^*(n)$ for all states $n$).

**Proof**:
1. For any unassigned exam $u$, it must eventually be allocated to some room $r^* \in \mathcal{R}_{compat}(u)$ in any valid complete timetable.
2. The true remaining soft cost $h^*(n)$ includes:
   $$h^*(n) = \sum_{u} \text{wastage}(u, r^*) + \text{ConsecutiveClashes}(n^*) + \text{DayLoadVariance}(n^*)$$
3. Since seat wastage penalty is non-negative and $\min_r \text{wastage}(u, r) \le \text{wastage}(u, r^*)$ by definition of the minimum, and since student clash penalties and day variances are $\ge 0$:
   $$h(n) = \sum_{u} \min_{r} \text{wastage}(u, r) \le \sum_{u} \text{wastage}(u, r^*) \le h^*(n)$$
4. Therefore, $h(n)$ never overestimates the true remaining cost. $\blacksquare$

### D. Priority Queue & Combinatorial Horizon
In tree search with fixed depth $N$, shallower states naturally have smaller accumulated path costs than deeper states ($g(d) \le g(d+1)$). To prevent shallow node flooding across the enormous combinatorial branching factor, Examora evaluates node priority as:
$$P(n) = (N - \text{depth}(n)) \cdot C + f(n)$$
Within each depth horizon, nodes are strictly ordered by $f(n) = g(n) + h(n)$, yielding orders-of-magnitude faster solution discovery (solving 12-exam problems in 13 states).

---

## 4. Algorithm 3: Hill Climbing

### A. Theoretical Foundation
Hill Climbing is a local search optimization algorithm that operates on complete candidate solutions. It begins with an initial valid schedule $S_0$ and iteratively transitions to neighboring schedules $S' \in \mathcal{N}(S)$ that improve the objective function $f(S)$.

### B. Neighborhood Generation Operators ($\mathcal{N}(S)$)
Examora implements two complementary mutation operators:
1. **Reassignment Mutation**:
   Select an exam $e \in \mathcal{E}$ uniformly at random. Move $e$ to a different time slot $t' \in \mathcal{T}$ and compatible room $r' \in \mathcal{R}_{compat}(e)$.
2. **Pairwise Swap Mutation**:
   Select two exams $e_1, e_2 \in \mathcal{E}$ such that $cap(room(e_2)) \ge |\text{Students}(e_1)|$ and $cap(room(e_1)) \ge |\text{Students}(e_2)|$. Swap their assigned slots and rooms:
   $$\sigma'(e_1) = (slot(e_2), room(e_2)), \quad \sigma'(e_2) = (slot(e_1), room(e_1))$$

### C. Steepest-Ascent & Random Restarts
At each step, a candidate neighborhood sample $\mathcal{N}_{sample}(S)$ of size $M$ (default 35-50) is evaluated:
$$S_{best} = \arg\min_{S' \in \mathcal{N}_{sample}(S)} f(S')$$
If $f(S_{best}) < f(S)$, the move is accepted ($S \leftarrow S_{best}$). If no candidate improves upon $S$, the algorithm has reached a local optimum. To escape local optima, Examora executes multiple random restarts ($k=3$), tracking the global best schedule across restarts.

---

## 5. Algorithm 4: Simulated Annealing

### A. Theoretical Foundation
Simulated Annealing is a stochastic metaheuristic inspired by the physical annealing process in metallurgy, where controlled cooling allows atoms to settle into a minimal-energy crystalline lattice.

### B. The Metropolis Acceptance Criterion
At iteration $k$ with current temperature $T_k$, a candidate neighbor $S'$ is sampled from $\mathcal{N}(S)$. The change in energy is:
$$\Delta E = f(S') - f(S)$$

The acceptance probability $P(\text{accept})$ is defined by the Boltzmann distribution:
$$P(\text{accept}) = \begin{cases} 1.0 & \text{if } \Delta E < 0 \quad (\text{improvement}) \\ \exp\left(-\frac{\Delta E}{T_k}\right) & \text{if } \Delta E \ge 0 \quad (\text{deterioration}) \end{cases}$$

At high temperatures ($T \gg 0$), the algorithm freely accepts sub-optimal moves to explore the landscape and escape local minima. As $T \to 0$, $P(\text{accept}) \to 0$, causing the algorithm to behave like greedy hill climbing.

### C. Geometric Cooling Schedule
$$T_{k+1} = T_k \cdot \alpha$$
Where initial temperature $T_0 = 100.0$ and cooling rate $\alpha = 0.985$.

### D. Inviolable Validity Preservation
Simulated Annealing maintains an independent reference:
$$S_{best\_valid} = \arg\min \{ f(S) \mid S \text{ visited and } \text{HardViolations}(S) = 0 \}$$
If the terminal state $S_{final}$ contains any hard constraint violation, the system automatically falls back to $S_{best\_valid}$. An invalid schedule is **never** returned to the user.

---

## 6. Algorithm 5: CSP with Backtracking Search

### A. Theoretical Foundation
Constraint Satisfaction Problems (CSPs) model the problem using:
- **Variables**: $X = \{e_1, e_2, \dots, e_N\}$
- **Domains**: $D(e) = \{ (t, r) \in \mathcal{T} \times \mathcal{R} \mid cap(r) \ge |\text{Students}(e)| \land dur(t) \ge dur(e) \}$
- **Constraints**: Binary relations prohibiting simultaneous room sharing, student clashes, or faculty clashes.

### B. Minimum Remaining Values (MRV) Heuristic
Also known as the "Most Constrained Variable" or "Fail-First" principle. At each decision point, Backtracking selects the unassigned variable with the smallest legal domain:
$$X^* = \arg\min_{X \in \text{Unassigned}} |D(X)|$$

### C. Degree Heuristic Tie-Breaker
When multiple variables share the minimum domain size, the Degree Heuristic selects the variable involved in the largest number of constraints with other unassigned variables:
$$\text{deg}(X) = |\{ Y \in \text{Unassigned} \mid Y \neq X \land \text{shares\_constraint}(X, Y) \}|$$

### D. Forward Checking Inference
When variable $X$ is assigned value $v = (t, r)$:
For every unassigned neighbor $Y \in \text{Neighbors}(X)$, prune all values $w = (t', r') \in D(Y)$ that conflict with $v$:
1. If $t' == t$ and $r' == r$ (room clash), remove $w$.
2. If $t' == t$ and ($X, Y$ share students or faculty), remove $w$.

If $D(Y)$ becomes empty for any neighbor, the forward check immediately flags a failure, triggering backtrack without exploring hopeless sub-trees.

---

## 7. Algorithm 6: Arc Consistency Algorithm 3 (AC-3)

### A. Theoretical Foundation
AC-3 enforces **pairwise arc consistency** across the constraint network prior to and during search.

**Definition**: A directed arc $(X_i, X_j)$ is arc consistent if and only if for every value $x \in D(X_i)$, there exists at least one supporting value $y \in D(X_j)$ such that $(x, y)$ satisfies all binary constraints between $X_i$ and $X_j$.

### B. The `REVISE(Xi, Xj)` Operator
```python
def REVISE(csp, Xi, Xj):
    revised = False
    for x in D(Xi):
        # Look for at least one support in D(Xj)
        if not any(satisfies_constraint(Xi, x, Xj, y) for y in D(Xj)):
            delete x from D(Xi)
            revised = True
    return revised
```

### C. Arc Propagation Queue Mechanics
1. Initialize queue $\mathcal{Q}$ with all directed arcs:
   $$\mathcal{Q} = \{ (X_i, X_j) \mid X_i \in \mathcal{E}, X_j \in \text{Neighbors}(X_i) \}$$
2. While $\mathcal{Q}$ is not empty:
   - Pop arc $(X_i, X_j)$.
   - If $\text{REVISE}(X_i, X_j)$ prunes values:
     - If $D(X_i) == \emptyset$, return **Failure** (contradiction detected!).
     - Enqueue $(X_k, X_i)$ for all $X_k \in \text{Neighbors}(X_i) \setminus \{X_j\}$.

### D. Integration: Maintaining Arc Consistency (MAC)
Examora integrates AC-3 in two modalities:
1. **Preprocessing**: AC-3 runs on initial domains, shrinking domain sizes and detecting insoluble setups in $O(c \cdot d^3)$ time before search begins.
2. **Backtracking with MAC**: After each variable assignment $X_i = v$, $D(X_i)$ is restricted to $\{v\}$, and AC-3 propagates constraints to all neighbor arcs. This prevents thrashing and guarantees minimal backtrack depth.

---

## 8. Summary Comparison of Algorithmic Trade-offs

| Criterion | BFS | A* Search | Hill Climbing | Simulated Annealing | CSP Backtracking | AC-3 with MAC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Strategy** | Uninformed FIFO | Heuristic Best-First | Local Greedy | Stochastic Thermal | Depth-First Pruning | Arc Consistency + MAC |
| **State Representation** | Partial Tree Node | Priority Tree Node | Complete Timetable | Complete Timetable | Variable Domains | Reduced Domains |
| **Memory Consumption** | High ($O(b^d)$) | Moderate ($O(b \cdot d)$) | Minimal ($O(1)$) | Minimal ($O(1)$) | Low ($O(n \cdot d)$) | Low ($O(n \cdot d)$) |
| **Speed on Sample Problem** | 1.70s (timed out) | ~0.001s | ~0.86s | ~0.81s | ~0.0002s | ~0.002s |
| **Primary Strength** | Completeness | Heuristic Guidance | Soft Optimization | Escapes Local Optima | Fast Satisfaction | Earliest Inconsistency Pruning |
| **Best Use Case** | Small instances ($N \le 6$) | Optimal small schedules | Timetable polishing | Large soft optimization | Standard timetable generation | Densely constrained timetables |
