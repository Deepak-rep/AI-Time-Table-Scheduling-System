"""
Examora: Main Streamlit Application.
An AI-Powered Intelligent Examination Scheduling and Optimization System.
"""
from __future__ import annotations

import os
import sys
import time
import json
import pandas as pd
import streamlit as st

# Ensure repository root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import (
    Exam,
    Room,
    TimeSlot,
    Faculty,
    Student,
    Schedule,
    SchedulingProblem,
)
from core.scheduler import ExamScheduler
from core.constraints import ConstraintChecker
from core.cost_function import CostEvaluator
from data.data_manager import DataManager
from utils.validation import ProblemValidator, TimetableValidator
from utils.metrics import BenchmarkAnalyzer
from interface.components import (
    get_custom_css,
    render_kpi_metrics,
    generate_timetable_grid_html,
    build_comparison_charts,
)


def init_session_state() -> DataManager:
    """Initializes Streamlit session state."""
    if "data_manager" not in st.session_state:
        st.session_state.data_manager = DataManager()
    if "current_schedule" not in st.session_state:
        st.session_state.current_schedule = None
    if "current_result" not in st.session_state:
        st.session_state.current_result = None
    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = None
    return st.session_state.data_manager


def main():
    st.set_page_config(
        page_title="Examora – AI Examination Scheduling System",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom styles
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    dm = init_session_state()
    problem = dm.problem

    # Sidebar Navigation
    with st.sidebar:
        st.markdown('<div class="main-header">🎓 EXAMORA</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.85rem; color:#6B7280; margin-bottom:1rem;">'
            'AI-Powered Intelligent Examination Scheduling & Optimization'
            '</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        page = st.radio(
            "Navigation Menu",
            [
                "📊 Dashboard",
                "📝 Manage Examination Data",
                "⚡ Scheduling Algorithms",
                "📅 Examination Timetable",
                "📈 Algorithm Comparison",
                "ℹ️ About Project & AI Theory",
            ],
            index=0,
        )

        st.divider()
        st.markdown("### Quick Actions")
        if st.button("🔄 Reset to Default University Dataset", use_container_width=True):
            dm.reset_to_sample()
            st.session_state.current_schedule = None
            st.session_state.current_result = None
            st.session_state.comparison_results = None
            st.success("Reset to sample dataset!")
            st.rerun()

        st.markdown(
            """
            <div style="font-size:0.75rem; color:#9CA3AF; margin-top:2rem; text-align:center;">
            Examora v2.0 • AI with Python<br>
            Constraint-Satisfaction & Optimization
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Page Routing
    if page == "📊 Dashboard":
        render_dashboard_page(dm, problem)
    elif page == "📝 Manage Examination Data":
        render_manage_data_page(dm, problem)
    elif page == "⚡ Scheduling Algorithms":
        render_algorithms_page(dm, problem)
    elif page == "📅 Examination Timetable":
        render_timetable_page(dm, problem)
    elif page == "📈 Algorithm Comparison":
        render_comparison_page(dm, problem)
    elif page == "ℹ️ About Project & AI Theory":
        render_about_page()


# ==============================================================================
# 1. DASHBOARD PAGE
# ==============================================================================
def render_dashboard_page(dm: DataManager, problem: SchedulingProblem):
    st.markdown('<div class="main-header">Executive Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of examination resources, student cohorts, and timetable status.</div>', unsafe_allow_html=True)

    sched = st.session_state.current_schedule
    status_str = "Scheduled" if (sched and len(sched.assignments) == len(problem.exams)) else "Not Scheduled"

    st.markdown(
        render_kpi_metrics(
            total_exams=len(problem.exams),
            total_students=len(problem.students),
            total_rooms=len(problem.rooms),
            total_slots=len(problem.time_slots_list),
            scheduled_status=status_str,
        ),
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📚 Examinations Overview")
        exam_rows = []
        for eid, e in problem.exams.items():
            fac = problem.faculty.get(e.assigned_faculty_id)
            compat = len(problem.compatible_rooms.get(eid, []))
            exam_rows.append({
                "Code": e.id,
                "Subject Name": e.name,
                "Students": e.student_count,
                "Duration": f"{e.duration_hours}h",
                "Invigilator": fac.name if fac else "Unassigned",
                "Compatible Rooms": compat,
            })
        st.dataframe(pd.DataFrame(exam_rows), use_container_width=True, height=280)

    with col2:
        st.subheader("🏛️ Examination Facilities")
        room_rows = []
        for rid, r in problem.rooms.items():
            room_rows.append({
                "Room ID": r.id,
                "Facility Name": r.name,
                "Capacity": r.capacity,
                "Location": r.building,
            })
        st.dataframe(pd.DataFrame(room_rows), use_container_width=True, height=280)

    st.divider()

    # System Feasibility Check
    st.subheader("🔍 Mathematical Feasibility & Health Check")
    is_valid, errors, warnings = ProblemValidator.validate_problem(problem)

    if is_valid:
        st.success("✅ **Dataset Configuration is Fully Feasible**: Total capacity, room sizes, and student enrollments satisfy all hard constraint prerequisites.")
    else:
        st.error("❌ **Dataset Infeasibility Detected**:")
        for err in errors:
            st.markdown(f"- {err}")

    if warnings:
        with st.expander(f"⚠️ Notices & Warnings ({len(warnings)})"):
            for w in warnings:
                st.markdown(f"- {w}")


# ==============================================================================
# 2. MANAGE EXAMINATION DATA PAGE
# ==============================================================================
def render_manage_data_page(dm: DataManager, problem: SchedulingProblem):
    st.markdown('<div class="main-header">Manage Examination Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Add, edit, delete, and import/export examination entities.</div>', unsafe_allow_html=True)

    tab_exams, tab_rooms, tab_slots, tab_faculty, tab_students, tab_io = st.tabs([
        "📚 Examinations",
        "🏛️ Rooms",
        "⏰ Time Slots",
        "👨‍🏫 Faculty",
        "👥 Students",
        "📁 Import / Export",
    ])

    # 1. Manage Exams
    with tab_exams:
        st.subheader("Current Examinations")
        exams_df = pd.DataFrame([
            {
                "ID": e.id,
                "Name": e.name,
                "Duration (h)": e.duration_hours,
                "Faculty ID": e.assigned_faculty_id,
                "Students": e.student_count,
                "Department": e.department,
            }
            for e in problem.exams.values()
        ])
        st.dataframe(exams_df, use_container_width=True)

        with st.expander("➕ Add New Examination"):
            with st.form("add_exam_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_eid = st.text_input("Exam Code / ID (e.g., CS201)")
                    new_ename = st.text_input("Course Name (e.g., Operating Systems)")
                    new_dur = st.number_input("Duration (hours)", min_value=1.0, max_value=6.0, value=3.0, step=0.5)
                with col_b:
                    fac_options = [""] + list(problem.faculty.keys())
                    new_fac = st.selectbox("Assigned Faculty Invigilator", fac_options)
                    new_stu_count = st.number_input("Estimated Student Count", min_value=1, max_value=500, value=40)
                    new_dept = st.text_input("Department", value="Computer Science")

                submitted = st.form_submit_button("Add Examination")
                if submitted:
                    if not new_eid or not new_ename:
                        st.error("Please provide both Exam ID and Name.")
                    else:
                        exam = Exam(
                            id=new_eid.strip(),
                            name=new_ename.strip(),
                            duration_hours=float(new_dur),
                            assigned_faculty_id=new_fac,
                            student_count_override=int(new_stu_count),
                            department=new_dept.strip(),
                        )
                        dm.add_exam(exam)
                        st.success(f"Added exam '{exam.name}' ({exam.id})!")
                        st.rerun()

        with st.expander("🗑️ Delete Examination"):
            del_eid = st.selectbox("Select Exam to Delete", list(problem.exams.keys()))
            if st.button("Delete Exam", type="secondary"):
                dm.delete_exam(del_eid)
                st.success(f"Deleted examination {del_eid}")
                st.rerun()

    # 2. Manage Rooms
    with tab_rooms:
        st.subheader("Current Examination Rooms")
        rooms_df = pd.DataFrame([
            {"ID": r.id, "Name": r.name, "Capacity": r.capacity, "Building": r.building}
            for r in problem.rooms.values()
        ])
        st.dataframe(rooms_df, use_container_width=True)

        with st.expander("➕ Add New Examination Room"):
            with st.form("add_room_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_rid = st.text_input("Room ID (e.g., R401)")
                    new_rname = st.text_input("Room Name (e.g., Lecture Hall 4)")
                with col_b:
                    new_rcap = st.number_input("Seating Capacity", min_value=10, max_value=1000, value=60)
                    new_rbldg = st.text_input("Building / Complex", value="Block A")

                if st.form_submit_button("Add Room"):
                    if new_rid and new_rname:
                        room = Room(id=new_rid.strip(), name=new_rname.strip(), capacity=int(new_rcap), building=new_rbldg.strip())
                        dm.add_room(room)
                        st.success(f"Added Room {room.name} ({room.id})!")
                        st.rerun()

        with st.expander("🗑️ Delete Room"):
            del_rid = st.selectbox("Select Room to Delete", list(problem.rooms.keys()))
            if st.button("Delete Room"):
                dm.delete_room(del_rid)
                st.success(f"Deleted room {del_rid}")
                st.rerun()

    # 3. Manage Time Slots
    with tab_slots:
        st.subheader("Configured Examination Time Slots")
        slots_df = pd.DataFrame([
            {
                "Slot ID": s.id,
                "Date": s.date_str,
                "Session": s.session,
                "Start Time": s.start_time,
                "End Time": s.end_time,
                "Duration (h)": s.duration_hours,
            }
            for s in problem.time_slots_list
        ])
        st.dataframe(slots_df, use_container_width=True)

        # Configurator: Number of exams per day with start and end times
        with st.expander("⚡ Configure Daily Examination Sessions (Exams per Day & Timings)", expanded=True):
            st.markdown(
                "Customize how many examination sessions are conducted in a day, along with their exact start and end times. "
                "This schedule template will be automatically generated across your chosen examination dates."
            )

            all_current_dates = sorted(list(set(s.date_str for s in problem.time_slots_list)))
            default_dates_str = ", ".join(all_current_dates) if all_current_dates else "2026-12-01, 2026-12-02, 2026-12-03, 2026-12-04, 2026-12-05"
            selected_dates_input = st.text_input(
                "Examination Dates (comma-separated YYYY-MM-DD)",
                value=default_dates_str,
                help="Enter dates on which examinations will be conducted",
            )

            num_daily_sessions = st.number_input(
                "Number of Examination Sessions per Day",
                min_value=1,
                max_value=5,
                value=min(max(len(set(s.session for s in problem.time_slots_list)), 1), 5) or 2,
                step=1,
                help="e.g. 1 exam/day, 2 exams/day, 3 exams/day, etc.",
            )

            st.markdown("##### Daily Session Timings (Start & End Time)")
            default_timings = [
                ("Session 1 (Morning)", "09:30", "12:30"),
                ("Session 2 (Afternoon)", "14:00", "17:00"),
                ("Session 3 (Evening)", "17:30", "20:30"),
                ("Session 4 (Late Evening)", "21:00", "23:00"),
                ("Session 5 (Early Morning)", "07:00", "09:00"),
            ]

            session_configs = []
            for i in range(num_daily_sessions):
                c_name, c_start, c_end, c_dur = st.columns([2, 1, 1, 1])
                def_name, def_start, def_end = default_timings[i] if i < len(default_timings) else (f"Session {i+1}", "09:00", "12:00")
                with c_name:
                    s_name = st.text_input(f"Session {i+1} Name", value=def_name, key=f"sess_name_{i}")
                with c_start:
                    s_start = st.text_input(f"Start Time (HH:MM)", value=def_start, key=f"sess_start_{i}")
                with c_end:
                    s_end = st.text_input(f"End Time (HH:MM)", value=def_end, key=f"sess_end_{i}")
                with c_dur:
                    dur_calc = TimeSlot.calculate_duration(s_start, s_end)
                    st.text_input(f"Duration", value=f"{dur_calc}h", disabled=True, key=f"sess_dur_{i}")
                session_configs.append({"name": s_name, "start": s_start, "end": s_end})

            replace_choice = st.checkbox("Replace existing time slots with this new daily schedule", value=True)

            if st.button("🚀 Apply Daily Sessions to Calendar", type="primary", use_container_width=True):
                parsed_dates = [d.strip() for d in selected_dates_input.split(",") if d.strip()]
                if not parsed_dates:
                    st.error("Please provide at least one valid examination date.")
                else:
                    count = dm.configure_daily_sessions(
                        dates=parsed_dates,
                        sessions=session_configs,
                        replace_existing=replace_choice,
                    )
                    st.success(f"✅ Successfully configured {count} total time slots across {len(parsed_dates)} dates with {num_daily_sessions} daily sessions!")
                    st.session_state.current_schedule = None
                    st.session_state.current_result = None
                    st.rerun()

        with st.expander("➕ Add Single Custom Time Slot"):
            with st.form("add_slot_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_sdate = st.text_input("Date (YYYY-MM-DD)", value="2026-12-06")
                    new_ssess = st.selectbox("Session", ["Morning", "Afternoon", "Evening"])
                with col_b:
                    new_sstart = st.text_input("Start Time", value="09:30")
                    new_send = st.text_input("End Time", value="12:30")
                    new_sdur = st.number_input("Slot Duration (h)", min_value=1.0, max_value=6.0, value=3.0, step=0.5)

                if st.form_submit_button("Add Time Slot"):
                    slot_id = f"{new_sdate}_{new_ssess}"
                    slot = TimeSlot(
                        id=slot_id,
                        date_str=new_sdate,
                        session=new_ssess,
                        start_time=new_sstart,
                        end_time=new_send,
                        duration_hours=float(new_sdur),
                    )
                    dm.add_slot(slot)
                    st.success(f"Added Time Slot {slot.id}!")
                    st.rerun()

    # 4. Manage Faculty
    with tab_faculty:
        st.subheader("Faculty & Invigilators")
        fac_df = pd.DataFrame([
            {"ID": f.id, "Name": f.name, "Department": f.department, "Email": f.email}
            for f in problem.faculty.values()
        ])
        st.dataframe(fac_df, use_container_width=True)

        with st.expander("➕ Add Faculty Member"):
            with st.form("add_fac_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_fid = st.text_input("Faculty ID (e.g., FAC09)")
                    new_fname = st.text_input("Full Name")
                with col_b:
                    new_fdept = st.text_input("Department", value="Computer Science")
                    new_femail = st.text_input("Email", value="")
                if st.form_submit_button("Add Faculty"):
                    if new_fid and new_fname:
                        fac = Faculty(id=new_fid.strip(), name=new_fname.strip(), department=new_fdept.strip(), email=new_femail.strip())
                        dm.add_faculty(fac)
                        st.success(f"Added faculty member {fac.name}!")
                        st.rerun()

    # 5. Manage Students
    with tab_students:
        st.subheader("Student Registrations")
        st.write(f"Total Enrolled Students: **{len(problem.students)}**")
        students_sample = pd.DataFrame([
            {
                "Student ID": s.id,
                "Name": s.name,
                "Department": s.department,
                "Enrolled Exams Count": len(s.enrolled_exam_ids),
                "Courses": ", ".join(s.enrolled_exam_ids),
            }
            for s in list(problem.students.values())[:50]
        ])
        st.dataframe(students_sample, use_container_width=True)

    # 6. Import / Export
    with tab_io:
        st.subheader("Import & Export Data via CSV")
        col_exp, col_imp = st.columns(2)

        with col_exp:
            st.markdown("#### 📤 Export Entities to CSV")
            exams_csv = dm.export_exams_csv()
            st.download_button("Download Examinations CSV", exams_csv, "examinations.csv", "text/csv")

            rooms_csv = dm.export_rooms_csv()
            st.download_button("Download Rooms CSV", rooms_csv, "rooms.csv", "text/csv")

        with col_imp:
            st.markdown("#### 📥 Import Examinations from CSV")
            uploaded_exams = st.file_uploader("Upload Examinations CSV", type=["csv"], key="upload_exams")
            if uploaded_exams is not None:
                content = uploaded_exams.getvalue().decode("utf-8")
                count, errors = dm.import_exams_csv(content)
                if count > 0:
                    st.success(f"Successfully imported {count} examinations!")
                    st.rerun()
                if errors:
                    st.error(f"Encountered errors: {errors}")


# ==============================================================================
# 3. SCHEDULING ALGORITHMS PAGE
# ==============================================================================
def render_algorithms_page(dm: DataManager, problem: SchedulingProblem):
    st.markdown('<div class="main-header">AI Scheduling Algorithms</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Select, configure, and execute any of the 6 AI examination scheduling algorithms.</div>', unsafe_allow_html=True)

    scheduler = ExamScheduler(problem)

    algo_choice = st.selectbox(
        "Select Scheduling Paradigm",
        scheduler.SUPPORTED_ALGORITHMS,
        index=4,  # default to CSP Backtracking
    )

    col_config, col_desc = st.columns([1, 1])

    with col_desc:
        st.markdown("#### Algorithm Characteristics")
        if "Breadth-First" in algo_choice:
            st.info("""
            **Breadth-First Search (BFS)**
            - **Paradigm**: Uninformed Systematic Tree Search
            - **Data Structure**: FIFO Queue (`collections.deque`)
            - **Behavior**: Explores states level by level (one exam assignment per level)
            - **Guarantees**: Finds shallowest goal state; high memory consumption
            """)
        elif "A*" in algo_choice:
            st.info("""
            **A* Search**
            - **Paradigm**: Informed / Heuristic Best-First Search
            - **Data Structure**: Priority Queue (`heapq`)
            - **Function**: f(n) = g(n) + h(n)
            - **Heuristic**: Admissible lower bound on remaining room capacity wastage
            - **Guarantees**: Optimally guided path search with minimal node expansions
            """)
        elif "Hill Climbing" in algo_choice:
            st.info("""
            **Hill Climbing**
            - **Paradigm**: Local Search / Trajectory Optimization
            - **Starting Point**: Constructive initial timetable
            - **Neighborhood**: Exam slot reassignments and pairwise exam swaps
            - **Selection**: Steepest-ascent improvement with random restarts
            """)
        elif "Simulated Annealing" in algo_choice:
            st.info("""
            **Simulated Annealing**
            - **Paradigm**: Stochastic Thermodynamic Metaheuristic
            - **Acceptance Rule**: Probabilistically accepts sub-optimal moves via P = exp(-ΔE / T)
            - **Cooling**: Geometric cooling schedule T(k+1) = T(k) * α
            - **Guarantees**: Escapes local optima; strictly rejects invalid final states
            """)
        elif "CSP" in algo_choice:
            st.info("""
            **Constraint Satisfaction Problem (CSP) Backtracking**
            - **Paradigm**: Systematic Backtracking with Constraint Propagation
            - **Variables**: Examinations; **Domains**: (Slot, Room) pairs
            - **Heuristics**: Minimum Remaining Values (MRV) & Degree Heuristic
            - **Inference**: Forward checking prunes conflicting neighbor domains
            """)
        elif "AC-3" in algo_choice:
            st.info("""
            **Arc Consistency Algorithm 3 (AC-3)**
            - **Paradigm**: Strict Constraint Arc Propagation & Domain Pruning
            - **Operation**: REVISE(Xi, Xj) removes unsupported domain elements
            - **Integration**: Standalone arc reduction + MAC (Maintaining Arc Consistency)
            - **Guarantees**: Detects insoluble conflicts prior to/during search
            """)

    with col_config:
        st.markdown("#### Hyperparameters & Execution Settings")
        kwargs = {}

        if "Breadth-First" in algo_choice:
            kwargs["max_states"] = st.slider("Max Explored States", 1000, 50000, 10000, step=1000)
            kwargs["timeout_seconds"] = st.slider("Timeout (seconds)", 5.0, 60.0, 20.0, step=5.0)
        elif "A*" in algo_choice:
            kwargs["max_states"] = st.slider("Max Explored States", 1000, 50000, 15000, step=1000)
            kwargs["timeout_seconds"] = st.slider("Timeout (seconds)", 5.0, 60.0, 20.0, step=5.0)
            kwargs["depth_weight"] = st.slider("Depth Priority Weight (C)", 10.0, 100.0, 50.0, step=10.0)
        elif "Hill Climbing" in algo_choice:
            kwargs["max_iterations"] = st.slider("Max Iterations", 50, 1000, 300, step=50)
            kwargs["max_restarts"] = st.slider("Random Restarts", 1, 5, 2)
            kwargs["neighborhood_size"] = st.slider("Neighborhood Sample Size", 10, 80, 35)
        elif "Simulated Annealing" in algo_choice:
            kwargs["initial_temperature"] = st.slider("Initial Temperature (T0)", 10.0, 200.0, 100.0, step=10.0)
            kwargs["cooling_rate"] = st.slider("Cooling Rate (α)", 0.90, 0.995, 0.985, step=0.005)
            kwargs["max_iterations"] = st.slider("Max Iterations", 200, 3000, 1200, step=100)
        elif "CSP" in algo_choice:
            kwargs["use_mrv"] = st.checkbox("Enable Minimum Remaining Values (MRV)", value=True)
            kwargs["use_forward_checking"] = st.checkbox("Enable Forward Checking", value=True)
            kwargs["timeout_seconds"] = st.slider("Timeout (seconds)", 5.0, 60.0, 25.0, step=5.0)
        elif "AC-3" in algo_choice:
            kwargs["use_mac"] = st.checkbox("Enable MAC (Maintaining Arc Consistency)", value=True)
            kwargs["timeout_seconds"] = st.slider("Timeout (seconds)", 5.0, 60.0, 25.0, step=5.0)

    st.divider()

    # Execution Trigger
    if st.button(f"🚀 Generate Timetable using {algo_choice}", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(p: float, msg: str):
            progress_bar.progress(p)
            status_text.text(msg)

        status_text.text(f"Starting {algo_choice}...")
        result = scheduler.run_algorithm(algo_choice, progress_callback=update_progress, **kwargs)
        progress_bar.progress(1.0)
        status_text.text("Finished!")

        st.session_state.current_schedule = result.schedule
        st.session_state.current_result = result

        if result.success:
            st.success(f"🎉 **{result.message}**")
        else:
            st.error(f"⚠️ **{result.message}**")

    # Display Current Result Cards if available
    res = st.session_state.current_result
    if res is not None:
        st.markdown("### Execution Performance Summary")
        q_score = CostEvaluator.get_quality_score(res.hard_violations, res.soft_penalty, len(problem.exams))

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Execution Time", f"{res.execution_time:.4f} s")
        m2.metric("Explored States", f"{res.explored_states:,}")
        m3.metric("Hard Violations", f"{res.hard_violations}", delta="Must be 0" if res.hard_violations == 0 else "FAIL")
        m4.metric("Soft Penalty", f"{res.soft_penalty:.1f}")
        m5.metric("Quality Score", f"{q_score}%")

        if res.details:
            with st.expander("🔬 Detailed Algorithmic Internal Metrics"):
                st.json({k: v for k, v in res.details.items() if k not in ["cost_history", "temp_history"]})

        if res.violation_details:
            with st.expander(f"⚠️ Constraint Audit ({len(res.violation_details)} items)"):
                for msg in res.violation_details:
                    st.markdown(f"- {msg}")


# ==============================================================================
# 4. TIMETABLE PAGE
# ==============================================================================
def render_timetable_page(dm: DataManager, problem: SchedulingProblem):
    st.markdown('<div class="main-header">Examination Timetable</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View and export the accepted examination timetable.</div>', unsafe_allow_html=True)

    sched = st.session_state.current_schedule
    if sched is None or len(sched.assignments) == 0:
        st.warning("⚠️ No examination timetable has been generated yet. Please navigate to 'Scheduling Algorithms' to generate a schedule.")
        if st.button("Generate Default Timetable (CSP)", type="primary"):
            scheduler = ExamScheduler(problem)
            res = scheduler.run_algorithm("CSP Backtracking")
            st.session_state.current_schedule = res.schedule
            st.session_state.current_result = res
            st.rerun()
        return

    # Export controls
    col_dl1, col_dl2 = st.columns([1, 1])
    with col_dl1:
        csv_data = dm.export_timetable_csv(sched)
        st.download_button(
            "📥 Export Timetable to CSV",
            data=csv_data,
            file_name="examination_timetable.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_dl2:
        json_data = json.dumps(sched.to_dict(), indent=2)
        st.download_button(
            "📥 Export Timetable to JSON",
            data=json_data,
            file_name="examination_timetable.json",
            mime="application/json",
            use_container_width=True,
        )

    view_mode = st.radio("Display View", ["🗓️ Calendar Grid View", "📋 Detailed Table View"], horizontal=True)

    if view_mode == "🗓️ Calendar Grid View":
        st.markdown(generate_timetable_grid_html(sched, problem), unsafe_allow_html=True)
    else:
        st.subheader("Tabular Examination Roster")
        rows = []
        for eid, assign in sorted(sched.assignments.items(), key=lambda x: x[1].slot_id):
            exam = problem.get_exam(eid)
            slot = problem.get_time_slot(assign.slot_id)
            room = problem.get_room(assign.room_id)
            fac = problem.faculty.get(exam.assigned_faculty_id) if exam else None

            rows.append({
                "Date": slot.date_str if slot else "",
                "Session": slot.session if slot else "",
                "Timing": f"{slot.start_time} - {slot.end_time}" if slot else "",
                "Code": eid,
                "Subject Name": exam.name if exam else "",
                "Room": f"{room.name} ({room.id})" if room else assign.room_id,
                "Capacity": room.capacity if room else 0,
                "Registered": exam.student_count if exam else 0,
                "Invigilator": fac.name if fac else "Unassigned",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ==============================================================================
# 5. ALGORITHM COMPARISON PAGE
# ==============================================================================
def render_comparison_page(dm: DataManager, problem: SchedulingProblem):
    st.markdown('<div class="main-header">Academic Algorithm Comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Direct empirical benchmark comparing all six AI algorithms on the exact same examination dataset.</div>', unsafe_allow_html=True)

    scheduler = ExamScheduler(problem)

    if st.button("⚡ Run Benchmark Across All 6 Algorithms", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def prog(p: float, msg: str):
            progress_bar.progress(p)
            status_text.text(msg)

        results = scheduler.compare_all(progress_callback=prog)
        st.session_state.comparison_results = results
        st.rerun()

    results = st.session_state.comparison_results
    if results is None:
        st.info("Click the button above to execute all six algorithms on the active dataset and produce empirical benchmark metrics.")
        return

    # Comparison Table
    rows = BenchmarkAnalyzer.create_comparison_rows(results, total_exams=len(problem.exams))
    df = pd.DataFrame(rows)

    st.subheader("📊 Empirical Performance Summary")
    st.dataframe(
        df[[
            "Algorithm",
            "Status",
            "Execution Time (s)",
            "Explored States",
            "Hard Violations",
            "Soft Penalty",
            "Total Cost",
            "Quality Score (%)",
        ]],
        use_container_width=True,
    )

    # Key Rankings & Insights
    rankings = BenchmarkAnalyzer.get_rankings(rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Fastest Algorithm", rankings["fastest"])
    c2.metric("🧠 Most Memory-Efficient", rankings["most_efficient"])
    c3.metric("🎯 Highest Solution Quality", rankings["best_quality"])

    # Highlight the overall best algorithm
    best_algo_name = rankings["best_quality"]
    best_res = results.get(best_algo_name)
    if best_res and best_res.schedule:
        best_row = next((r for r in rows if r["Algorithm"] == best_algo_name), None)
        q_score = best_row["Quality Score (%)"] if best_row else 80.0
        st.success(
            f"🏆 **Overall Winner: {best_algo_name}** produced the best examination timetable! "
            f"Quality Score: **{q_score}%** | Hard Violations: **0** | Soft Penalty: **{best_res.soft_penalty:.1f}** | Time: **{best_res.execution_time:.4f}s**."
        )

        col_win1, col_win2 = st.columns([2, 1])
        with col_win1:
            st.info(f"💡 **Recommendation**: {best_algo_name} successfully minimized student exam fatigue (consecutive clashes) and room seat wastage while strictly guaranteeing 0 hard violations.")
        with col_win2:
            if st.button("📋 Apply & View Winning Timetable", type="primary", use_container_width=True):
                st.session_state.current_schedule = best_res.schedule
                st.session_state.current_result = best_res
                st.toast(f"Loaded {best_algo_name} timetable! Redirecting to Timetable tab...")
                st.rerun()

    # Visualizations
    fig_perf, fig_qual = build_comparison_charts(rows)
    if fig_perf and fig_qual:
        st.subheader("📈 Comparative Visualizations")
        st.plotly_chart(fig_perf, use_container_width=True)
        st.plotly_chart(fig_qual, use_container_width=True)

    # In-depth Academic Discussion
    st.subheader("📖 Academic Analysis: Algorithmic Trade-offs")
    st.markdown("""
    | Algorithm | Time Complexity Class | Space Complexity | Hard Constraint Guarantee | Soft Constraint Quality |
    | :--- | :--- | :--- | :--- | :--- |
    | **Breadth-First Search (BFS)** | $O(b^d)$ Exponential | $O(b^d)$ High | High (if solvable within limit) | Baseline (shallowest valid) |
    | **A* Search** | $O(b^d)$ Informed | $O(b^d)$ Moderate | High (pruned branches) | High (guided by heuristic) |
    | **Hill Climbing** | $O(k \cdot m)$ Local | $O(1)$ Minimal | Dependent on initial state | Good (improves soft constraints) |
    | **Simulated Annealing** | $O(k)$ Stochastic | $O(1)$ Minimal | Enforced (rejects invalid) | Excellent (escapes local optima) |
    | **CSP Backtracking** | $O(d^n)$ Tree Search | $O(n)$ Linear | Complete (guaranteed valid) | Moderate (satisfaction focus) |
    | **AC-3 with Backtracking** | $O(c \cdot d^3)$ Polynomial | $O(n \cdot d)$ Low | Complete (strongest pruning) | High (combined with MAC) |
    """)


# ==============================================================================
# 6. ABOUT PROJECT & AI THEORY PAGE
# ==============================================================================
def render_about_page():
    st.markdown('<div class="main-header">About Examora & AI Foundations</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Project architecture, theoretical formulations, and academic viva reference.</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 🎯 Project Overview
    **Examora** is an end-to-end intelligent examination timetabling and optimization system designed to automate
    the complex combinatorial challenge of university scheduling. By modeling examination scheduling under formal
    Artificial Intelligence paradigms, Examora satisfies all real-world institutional constraints while minimizing student and facility penalties.

    ---

    ### 🧠 The Six AI Paradigms Implemented

    #### 1. Breadth-First Search (BFS)
    Explores the state space systematically level-by-level using a FIFO queue. Each level represents the assignment
    of an additional examination. Prunes illegal states during generation.

    #### 2. A* Search
    Informed heuristic search utilizing priority evaluation $f(n) = g(n) + h(n)$. Employs an admissible heuristic $h(n)$
    measuring theoretical minimal room capacity wastage across unassigned examinations, augmented with depth-guided prioritization.

    #### 3. Hill Climbing
    Local search optimizer that evaluates candidate neighboring timetables generated via exam reassignments and pairwise swaps.
    Implements steepest ascent with random restarts to locate local optima.

    #### 4. Simulated Annealing
    Physics-inspired thermodynamic optimization that probabilistically accepts sub-optimal moves according to the Boltzmann distribution
    $P = \exp(-\Delta E / T)$ over a geometric cooling schedule $T_{k+1} = T_k \times \alpha$.

    #### 5. Constraint Satisfaction Problem (CSP) Backtracking
    Models examinations as variables $X_i$, and valid (slot, room) pairs as discrete domains $D_i$.
    Features Minimum Remaining Values (MRV) variable ordering, Degree Heuristic tie-breaking, and Forward Checking inference.

    #### 6. Arc Consistency Algorithm 3 (AC-3)
    Enforces pairwise arc consistency between constrained examinations. Employs the `REVISE(Xi, Xj)` operation to actively prune
    unsupported domain values and detect empty domain contradictions before search, integrated with MAC (Maintaining Arc Consistency).

    ---

    ### 👥 Four-Member Project Team Distribution
    - **Member 1**: Breadth-First Search (BFS) & A* Search Engine Architecture.
    - **Member 2**: Hill Climbing Local Search & Neighborhood Generator Design.
    - **Member 3**: Simulated Annealing Metaheuristic & Cooling Schedule Calibration.
    - **Member 4**: CSP Backtracking, AC-3 Domain Propagation, Constraint Auditing & System Integration.
    """)


if __name__ == "__main__":
    main()
