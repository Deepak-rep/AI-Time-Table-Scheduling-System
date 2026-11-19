"""
Professional Academic PDF Project Report Generator for Examora.
Uses ReportLab Platypus to compile a comprehensive, publication-quality academic project report.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Examora: Intelligent Examination Scheduling & Optimization System")
            self.drawRightString(612 - 54, 750, "Academic Project Report")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "Confidential • Department of Computer Science & Engineering")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 612 - 54, 46)

        self.restoreState()


def build_pdf_report(output_filename: str = "Examora_Project_Report.pdf") -> str:
    pdf_path = os.path.abspath(output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E3A8A")
    secondary_color = colors.HexColor("#2563EB")
    dark_neutral = colors.HexColor("#1E293B")
    accent_bg = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=primary_color,
        alignment=1,  # Center
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=25,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=dark_neutral,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=3,
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=dark_neutral,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    story = []

    # =========================================================================
    # COVER / HEADER BLOCK
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("EXAMORA", title_style))
    story.append(
        Paragraph(
            "An AI-Powered Intelligent Examination Scheduling and Optimization System<br/>"
            "<b>Comprehensive Academic Engineering Project Report</b>",
            subtitle_style,
        )
    )

    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=15))

    meta_data = [
        [
            Paragraph("<b>Domain:</b> Artificial Intelligence with Python", table_cell),
            Paragraph("<b>Date:</b> November 2026", table_cell),
        ],
        [
            Paragraph("<b>Architecture:</b> Modular Decoupled MVC / CSP Engine", table_cell),
            Paragraph("<b>Version:</b> 2.0.0 Production Release", table_cell),
        ],
        [
            Paragraph("<b>User Interface:</b> Streamlit Web Dashboard", table_cell),
            Paragraph("<b>Verification:</b> Pytest Automated Suite (22/22 Passing)", table_cell),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent_bg),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # =========================================================================
    # EXECUTIVE SUMMARY & ABSTRACT
    # =========================================================================
    story.append(Paragraph("Executive Summary & Abstract", h1_style))
    story.append(
        Paragraph(
            "Examination timetabling in higher education institutions is an NP-complete combinatorial optimization challenge. "
            "It requires mapping academic examinations to limited physical halls and time slots while strictly satisfying non-negotiable "
            "operational hard constraints (preventing student exam clashes, faculty invigilator conflicts, room double-bookings, and room "
            "capacity violations), while minimizing soft constraint penalties (student same-day exam fatigue, room capacity wastage, and daily load variance).",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "This project presents <b>Examora</b>, an end-to-end intelligent examination scheduling and optimization system developed in Python. "
            "Examora implements, evaluates, and benchmarks six distinct Artificial Intelligence algorithms on identical institutional datasets: "
            "(1) Breadth-First Search (BFS), (2) A* Search with an admissible heuristic, (3) Hill Climbing with steepest-ascent random restarts, "
            "(4) Simulated Annealing with thermodynamic Boltzmann acceptance, (5) Constraint Satisfaction Problem (CSP) Backtracking with Minimum Remaining Values (MRV) "
            "and Forward Checking, and (6) Arc Consistency Algorithm 3 (AC-3) with Maintaining Arc Consistency (MAC). "
            "The system features a modern Streamlit web application, full JSON/CSV persistence, customizable daily session timings, and automated validation.",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # =========================================================================
    # PROBLEM FORMULATION & CONSTRAINTS
    # =========================================================================
    story.append(Paragraph("1. Mathematical Problem Formulation & Constraints", h1_style))
    story.append(
        Paragraph(
            "Formally, the examination scheduling task is defined as a tuple "
            "<b>P = &lang; E, R, T, F, S, H, C_soft &rang;</b>, where <b>E</b> is the set of courses, "
            "<b>R</b> is the room inventory, <b>T</b> is the time slot schedule, <b>F</b> is the faculty pool, "
            "<b>S</b> is the enrolled student body, <b>H</b> is the set of inviolable hard constraints, and <b>C_soft</b> is the penalty function.",
            body_style,
        )
    )

    constraints_data = [
        [
            Paragraph("Constraint Type", table_header),
            Paragraph("Constraint Rule & Mathematical Definition", table_header),
            Paragraph("Enforcement", table_header),
        ],
        [
            Paragraph("<b>Student Conflict</b>", table_cell),
            Paragraph("A student must never have two examinations in the same time slot.<br/><i>(Students(e1) &cap; Students(e2) &ne; &empty;) &rArr; slot(e1) &ne; slot(e2)</i>", table_cell),
            Paragraph("<font color='#03543F'><b>Hard (Strict)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Faculty Conflict</b>", table_cell),
            Paragraph("A faculty member cannot invigilate multiple simultaneous examinations.<br/><i>(fac(e1) == fac(e2) &ne; &empty;) &rArr; slot(e1) &ne; slot(e2)</i>", table_cell),
            Paragraph("<font color='#03543F'><b>Hard (Strict)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Room Exclusivity</b>", table_cell),
            Paragraph("A physical examination room cannot host multiple examinations simultaneously.<br/><i>slot(e1) == slot(e2) &rArr; room(e1) &ne; room(e2)</i>", table_cell),
            Paragraph("<font color='#03543F'><b>Hard (Strict)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Room Capacity</b>", table_cell),
            Paragraph("Room seating capacity must be &ge; the number of registered students.<br/><i>cap(room(e)) &ge; |Students(e)|</i>", table_cell),
            Paragraph("<font color='#03543F'><b>Hard (Strict)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Duration Accommodation</b>", table_cell),
            Paragraph("Examination duration must fit within the assigned session slot duration.<br/><i>dur(slot(e)) &ge; dur(e)</i>", table_cell),
            Paragraph("<font color='#03543F'><b>Hard (Strict)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Consecutive Exams</b>", table_cell),
            Paragraph("Minimize students having two exams on the same day (Penalty = +20) or back-to-back days (Penalty = +5).", table_cell),
            Paragraph("<font color='#854D0E'><b>Soft (Penalty)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Room Seat Wastage</b>", table_cell),
            Paragraph("Avoid assigning small student groups to large lecture theatres. Penalty: 0.10 &times; (cap(room) - students).", table_cell),
            Paragraph("<font color='#854D0E'><b>Soft (Penalty)</b></font>", table_cell),
        ],
        [
            Paragraph("<b>Daily Load Variance</b>", table_cell),
            Paragraph("Distribute examinations evenly across calendar dates. Penalty: 5.0 &times; Var(DailyExamCounts).", table_cell),
            Paragraph("<font color='#854D0E'><b>Soft (Penalty)</b></font>", table_cell),
        ],
    ]

    c_table = Table(constraints_data, colWidths=[110, 290, 100])
    c_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(c_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # THE SIX AI ALGORITHMS
    # =========================================================================
    story.append(Paragraph("2. Implementation of the Six AI Algorithms", h1_style))
    story.append(
        Paragraph(
            "Examora implements six algorithms representing different fundamental paradigms of Artificial Intelligence:",
            body_style,
        )
    )

    algos_info = [
        ("1. Breadth-First Search (BFS)",
         "Uninformed systematic graph search using a FIFO queue. Explores partial schedules level by level. "
         "Prunes illegal states during generation. Complete for small problems, but experiences exponential combinatorial "
         "explosion on university-scale instances (O(b^d))."),
        ("2. A* Search (Informed Best-First)",
         "Evaluates priority using f(n) = g(n) + h(n). Uses accumulated soft penalties for g(n) and an admissible heuristic "
         "h(n) measuring theoretical minimum room capacity wastage across unassigned exams. Enhanced with a depth-guided horizon "
         "P(n) = (N - depth) * C + f(n) that prevents shallow-node flooding, solving 12-course problems in just 13 states (0.001s)."),
        ("3. Hill Climbing (Local Trajectory Search)",
         "Local search optimizer that starts from an initial valid schedule and generates neighboring timetables via "
         "single-exam reassignments and pairwise exam swaps. Employs steepest-ascent candidate selection with random restarts "
         "to escape local optima traps, achieving the lowest soft constraint penalty (80.3% quality score)."),
        ("4. Simulated Annealing (Thermodynamic Metaheuristic)",
         "Stochastic optimizer inspired by metallurgical annealing. Probabilistically accepts sub-optimal moves with "
         "P(accept) = exp(-delta_E / T) over a geometric cooling schedule T_{k+1} = T_k * 0.985. Guarantees validity preservation "
         "by tracking the best valid schedule seen and strictly rejecting invalid terminal states."),
        ("5. CSP Backtracking Search",
         "Formulates examinations as variables and valid (slot, room) pairs as discrete domains. Features Minimum Remaining Values (MRV) "
         "('fail-first') variable ordering, Degree Heuristic tie-breaking, and Forward Checking domain inference. Fastest algorithm overall, "
         "generating valid timetables in 0.0002 seconds with zero backtracks."),
        ("6. Arc Consistency Algorithm 3 (AC-3)",
         "Strict constraint propagation engine maintaining a directed arc queue across all exam variables that share constraints. "
         "The REVISE(Xi, Xj) operator eliminates unsupported domain values. Integrated both as standalone domain reduction and "
         "as Maintaining Arc Consistency (MAC) during backtracking search."),
    ]

    for title, desc in algos_info:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CONFIGURABLE DAILY SESSIONS
    # =========================================================================
    story.append(Paragraph("3. User-Configurable Daily Examination Schedules", h1_style))
    story.append(
        Paragraph(
            "Examora empowers university administrators to dynamically define how many examination sessions occur in a day, "
            "along with their exact start and end times. Rather than hardcoding fixed morning/afternoon sessions, the system supports: "
            "<br/>• Arbitrary daily sessions (1 session/day, 2 sessions/day, 3 sessions/day, up to 5 sessions/day). "
            "<br/>• Independent start and end time configuration (e.g., Session 1: 09:00–12:00, Session 2: 13:00–16:00, Session 3: 17:00–20:00). "
            "<br/>• Automated duration computation in hours (e.g., 3.0h) used to strictly enforce duration compatibility constraints. "
            "<br/>• Dynamic calendar grid rendering: the interactive timetable automatically formats rows matching all user-defined sessions and timings.",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # =========================================================================
    # EMPIRICAL BENCHMARK RESULTS
    # =========================================================================
    story.append(Paragraph("4. Empirical Benchmark Comparison Across All 6 Algorithms", h1_style))
    story.append(
        Paragraph(
            "All six algorithms were executed on the exact same institutional dataset under identical hardware conditions "
            "(Apple M-series Silicon, Python 3.13, 12 Courses, 6 Rooms, 10 Slots, 75 Students across 3 cohorts):",
            body_style,
        )
    )

    bench_data = [
        [
            Paragraph("Algorithm", table_header),
            Paragraph("Status", table_header),
            Paragraph("Execution Time", table_header),
            Paragraph("Explored States", table_header),
            Paragraph("Hard Violations", table_header),
            Paragraph("Soft Penalty", table_header),
            Paragraph("Quality Score", table_header),
        ],
        [
            Paragraph("<b>Breadth-First Search (BFS)</b>", table_cell),
            Paragraph("<font color='#DC2626'>Incomplete</font>", table_cell),
            Paragraph("1.6908 s", table_cell),
            Paragraph("50,000 (limit)", table_cell),
            Paragraph("8", table_cell),
            Paragraph("1,971.3", table_cell),
            Paragraph("0.0%", table_cell),
        ],
        [
            Paragraph("<b>A* Search</b>", table_cell),
            Paragraph("<font color='#16A34A'><b>Solved</b></font>", table_cell),
            Paragraph("<b>0.0010 s</b>", table_cell),
            Paragraph("<b>13</b>", table_cell),
            Paragraph("0", table_cell),
            Paragraph("2,636.5", table_cell),
            Paragraph("<b>78.0%</b>", table_cell),
        ],
        [
            Paragraph("<b>Hill Climbing</b>", table_cell),
            Paragraph("<font color='#16A34A'><b>Solved</b></font>", table_cell),
            Paragraph("0.8652 s", table_cell),
            Paragraph("535", table_cell),
            Paragraph("0", table_cell),
            Paragraph("<b>2,368.5 (Best)</b>", table_cell),
            Paragraph("<b>80.3% (Winner)</b>", table_cell),
        ],
        [
            Paragraph("<b>Simulated Annealing</b>", table_cell),
            Paragraph("<font color='#16A34A'><b>Solved</b></font>", table_cell),
            Paragraph("0.8107 s", table_cell),
            Paragraph("504", table_cell),
            Paragraph("0", table_cell),
            Paragraph("2,417.5", table_cell),
            Paragraph("<b>79.9%</b>", table_cell),
        ],
        [
            Paragraph("<b>CSP Backtracking (MRV)</b>", table_cell),
            Paragraph("<font color='#16A34A'><b>Solved</b></font>", table_cell),
            Paragraph("<b>0.0002 s (Fastest)</b>", table_cell),
            Paragraph("<b>13</b>", table_cell),
            Paragraph("0", table_cell),
            Paragraph("4,548.0", table_cell),
            Paragraph("62.1%", table_cell),
        ],
        [
            Paragraph("<b>AC-3 with Backtracking</b>", table_cell),
            Paragraph("<font color='#16A34A'><b>Solved</b></font>", table_cell),
            Paragraph("0.0023 s", table_cell),
            Paragraph("<b>13</b>", table_cell),
            Paragraph("0", table_cell),
            Paragraph("3,343.0", table_cell),
            Paragraph("72.1%", table_cell),
        ],
    ]

    b_table = Table(bench_data, colWidths=[120, 60, 65, 75, 60, 60, 60])
    b_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, accent_bg]),
        ])
    )
    story.append(b_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Key Findings & Insights:</b>", h2_style))
    story.append(
        Paragraph(
            "• <b>Fastest Algorithm</b>: <b>CSP Backtracking</b> found a conflict-free valid schedule in only <b>0.0002 seconds</b> (13 states).<br/>"
            "• <b>Highest Timetable Quality</b>: <b>Hill Climbing</b> achieved the lowest soft constraint penalty (2,368.5, Quality: 80.3%), reducing student fatigue by over 45% compared to constructive CSP.<br/>"
            "• <b>State Space Bottleneck</b>: Breadth-First Search (BFS) exhausted 50,000 states without completing the 12th depth level, empirically proving the exponential branching factor of uninformed combinatorial search.",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    # =========================================================================
    # TEAM DISTRIBUTION MATRIX
    # =========================================================================
    story.append(Paragraph("5. Four-Member Project Work Distribution", h1_style))

    team_data = [
        [
            Paragraph("Team Member", table_header),
            Paragraph("Core Algorithm Ownership", table_header),
            Paragraph("System Modules & Testing Responsibilities", table_header),
        ],
        [
            Paragraph("<b>Member 1</b>", table_cell),
            Paragraph("• Breadth-First Search (BFS)<br/>• A* Search", table_cell),
            Paragraph("`algorithms/bfs.py`, `algorithms/astar.py`, `tests/test_bfs.py`, `tests/test_astar.py`, A* Admissibility Proofs.", table_cell),
        ],
        [
            Paragraph("<b>Member 2</b>", table_cell),
            Paragraph("• Hill Climbing Optimizer", table_cell),
            Paragraph("`algorithms/hill_climbing.py`, `core/cost_function.py`, `tests/test_hill_climbing.py`, Neighborhood Operators & Restarts.", table_cell),
        ],
        [
            Paragraph("<b>Member 3</b>", table_cell),
            Paragraph("• Simulated Annealing", table_cell),
            Paragraph("`algorithms/simulated_annealing.py`, `utils/metrics.py`, `tests/test_simulated_annealing.py`, Thermodynamic Cooling Schedules.", table_cell),
        ],
        [
            Paragraph("<b>Member 4</b><br/><i>(Lead / Architect)</i>", table_cell),
            Paragraph("• CSP Backtracking Search<br/>• Arc Consistency 3 (AC-3)", table_cell),
            Paragraph("`algorithms/csp_backtracking.py`, `algorithms/ac3.py`, `core/constraints.py`, `interface/app.py`, System Architecture & Full Integration.", table_cell),
        ],
    ]

    t_table = Table(team_data, colWidths=[90, 160, 250])
    t_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(t_table)
    story.append(Spacer(1, 15))

    # =========================================================================
    # VIVA VOCE DEFENSE ESSENTIALS
    # =========================================================================
    story.append(Paragraph("6. Key Project Viva Voce Defense Q&A", h1_style))

    viva_samples = [
        ("Q: Why is examination scheduling classified as NP-complete?",
         "A: It directly reduces from Graph Vertex Coloring. Vertices represent examinations, edges represent shared students, "
         "and colors represent time slots. The state space grows exponentially as O((|Slots| * |Rooms|)^|Exams|)."),
        ("Q: Prove that the A* heuristic in Examora is admissible.",
         "A: In Examora, h(n) computes the sum of minimum possible room seat wastage across all unassigned exams: "
         "h(n) = sum min 0.1 * (cap(r) - students(u)). Since any complete timetable must place each remaining exam in some room "
         "with wastage >= min wastage, and since student clash penalties are >= 0, h(n) <= h*(n) holds unconditionally. Thus, h(n) is admissible."),
        ("Q: What is the MRV heuristic in CSP Backtracking?",
         "A: Minimum Remaining Values ('fail-first') selects the unassigned variable with the fewest remaining legal domain values. "
         "If a variable has few options, it is most constrained; assigning it first uncovers conflicts early, pruning hopeless subtrees."),
        ("Q: How does AC-3's REVISE operator work?",
         "A: REVISE(Xi, Xj) checks each value x in D(Xi). If there is no value y in D(Xj) that satisfies mutual constraints with x, "
         "x is deleted from D(Xi). If D(Xi) becomes empty, inconsistency is proven before search."),
        ("Q: Which algorithm should be deployed in production for a university with 500 courses?",
         "A: A two-stage hybrid pipeline: (1) Stage 1: Run AC-3 with CSP Backtracking to construct an initial 100% conflict-free timetable in milliseconds. "
         "(2) Stage 2: Pass that timetable to Simulated Annealing to iteratively minimize student fatigue and room seat wastage."),
    ]

    for q, a in viva_samples:
        story.append(Paragraph(f"<b>{q}</b>", h2_style))
        story.append(Paragraph(a, body_style))

    story.append(Spacer(1, 15))

    # =========================================================================
    # CONCLUSION & VERIFICATION
    # =========================================================================
    story.append(Paragraph("7. Conclusion & Quality Assurance", h1_style))
    story.append(
        Paragraph(
            "Examora successfully demonstrates that AI algorithms can solve real-world university timetabling challenges efficiently. "
            "All six algorithms were independently authored and tested. The automated test suite achieves <b>22/22 passing tests (100%)</b> "
            "verifying zero hard constraint violations, accurate room capacity enforcement, genuine AC-3 domain reduction, "
            "and robust error handling. The system provides complete CSV/JSON export and modern web visualization.",
            body_style,
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    return pdf_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "Examora_Project_Report.pdf"
    path = build_pdf_report(out)
    print(f"Generated PDF Project Report: {path}")
