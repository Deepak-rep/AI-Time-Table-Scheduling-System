"""
UI components, visualizers, styles, and chart generators for Examora.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.models import Schedule, SchedulingProblem, TimeSlot, Exam


def get_custom_css() -> str:
    """Returns custom modern CSS for the Examora dashboard."""
    return """
    <style>
    /* Global branding & styles */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .kpi-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748B;
        letter-spacing: 0.05em;
    }
    .badge-success {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-warning {
        background-color: #FEF08A;
        color: #854D0E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-danger {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .timetable-cell {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 6px;
        font-size: 0.85rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .exam-badge {
        background-color: #EEF2FF;
        color: #3730A3;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .room-badge {
        background-color: #F0FDF4;
        color: #166534;
        font-size: 0.75rem;
        padding: 2px 5px;
        border-radius: 4px;
    }
    .fac-badge {
        background-color: #FFFBEB;
        color: #92400E;
        font-size: 0.75rem;
        padding: 2px 5px;
        border-radius: 4px;
    }
    </style>
    """


def render_kpi_metrics(
    total_exams: int,
    total_students: int,
    total_rooms: int,
    total_slots: int,
    scheduled_status: str,
) -> str:
    """Generates HTML for top summary KPI cards."""
    status_badge = (
        '<span class="badge-success">SCHEDULED</span>'
        if scheduled_status == "Scheduled"
        else '<span class="badge-warning">NOT SCHEDULED</span>'
    )

    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
        <div class="kpi-card">
            <div class="kpi-value">{total_exams}</div>
            <div class="kpi-label">Examinations</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{total_students}</div>
            <div class="kpi-label">Registered Students</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{total_rooms}</div>
            <div class="kpi-label">Exam Rooms</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{total_slots}</div>
            <div class="kpi-label">Time Slots</div>
        </div>
        <div class="kpi-card">
            <div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">{status_badge}</div>
            <div class="kpi-label">Timetable Status</div>
        </div>
    </div>
    """


def generate_timetable_grid_html(schedule: Schedule, problem: SchedulingProblem) -> str:
    """
    Renders an HTML calendar grid for the examination timetable:
    Columns = Examination Dates
    Rows = Examination Sessions (dynamically discovered with start/end times)
    Cells = List of scheduled examinations with subject name, room, and faculty invigilator.
    """
    dates = sorted(list(set(slot.date_str for slot in problem.time_slots_list)))
    
    # Dynamically extract sessions and timings from problem time slots
    session_timings: Dict[str, str] = {}
    session_start_times: Dict[str, str] = {}
    for slot in problem.time_slots_list:
        if slot.session not in session_timings:
            session_timings[slot.session] = f"{slot.start_time} - {slot.end_time}"
            session_start_times[slot.session] = slot.start_time

    sessions = sorted(
        list(session_timings.keys()),
        key=lambda sess: session_start_times.get(sess, "00:00")
    )

    # Group assignments by (date, session)
    grid_data: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for (d, s) in [(d, s) for d in dates for s in sessions]:
        grid_data[(d, s)] = []

    for eid, assign in schedule.assignments.items():
        slot = problem.get_time_slot(assign.slot_id)
        room = problem.get_room(assign.room_id)
        exam = problem.get_exam(eid)
        if not slot or not exam:
            continue

        fac = problem.faculty.get(exam.assigned_faculty_id)
        fac_name = fac.name if fac else "Unassigned"

        grid_data[(slot.date_str, slot.session)].append({
            "exam_id": eid,
            "exam_name": exam.name,
            "room_name": room.name if room else assign.room_id,
            "room_cap": room.capacity if room else 0,
            "students": exam.student_count,
            "faculty": fac_name,
            "start": slot.start_time,
            "end": slot.end_time,
        })

    html = ['<div style="overflow-x: auto; margin-top: 1rem;">']
    html.append('<table style="width: 100%; border-collapse: collapse; font-family: sans-serif;">')
    html.append('<thead><tr style="background-color: #1E3A8A; color: white;">')
    html.append('<th style="padding: 12px; border: 1px solid #CBD5E1; text-align: center; width: 140px;">Session / Timing</th>')
    for d in dates:
        html.append(f'<th style="padding: 12px; border: 1px solid #CBD5E1; text-align: center;">{d}</th>')
    html.append('</tr></thead><tbody>')

    for sess in sessions:
        html.append('<tr>')
        sess_time = session_timings.get(sess, "")
        html.append(
            f'<td style="padding: 10px; border: 1px solid #CBD5E1; background: #F1F5F9; font-weight: 700; text-align: center;">'
            f'{sess}<br><span style="font-size: 0.75rem; color: #64748B; font-weight: normal;">{sess_time}</span></td>'
        )

        for d in dates:
            items = grid_data.get((d, sess), [])
            html.append('<td style="padding: 8px; border: 1px solid #CBD5E1; vertical-align: top; min-width: 170px; background: #FAFAFA;">')
            if not items:
                html.append('<div style="color: #94A3B8; font-size: 0.8rem; font-style: italic; text-align: center; padding: 12px;">No exams</div>')
            else:
                for it in items:
                    html.append(f"""
                    <div class="timetable-cell">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span class="exam-badge">{it['exam_id']}</span>
                            <span class="room-badge">📍 {it['room_name']}</span>
                        </div>
                        <div style="font-weight: 600; color: #1E293B; margin-bottom: 4px;">{it['exam_name']}</div>
                        <div style="font-size: 0.75rem; color: #475569;">
                            👥 Students: <b>{it['students']}</b> / {it['room_cap']}
                        </div>
                        <div style="font-size: 0.75rem; color: #92400E; margin-top: 2px;">
                            👨‍🏫 {it['faculty']}
                        </div>
                    </div>
                    """)
            html.append('</td>')
        html.append('</tr>')

    html.append('</tbody></table></div>')
    return "".join(html)


def build_comparison_charts(rows: List[Dict[str, Any]]):
    """
    Constructs Plotly charts for comparing execution time, explored states, and quality scores.
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        algos = [r["Algorithm"] for r in rows]
        times = [r["Execution Time (s)"] for r in rows]
        states = [r["Explored States"] for r in rows]
        costs = [r["Total Cost"] for r in rows]
        qualities = [r["Quality Score (%)"] for r in rows]

        # Figure 1: Execution Time & Explored States
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Execution Time (seconds) - Lower is Faster", "Explored States - Lower is More Efficient"),
        )

        fig.add_trace(
            go.Bar(
                x=algos, y=times, name="Time (s)",
                marker_color="#3B82F6",
                text=[f"{t:.3f}s" for t in times], textposition="auto",
            ),
            row=1, col=1,
        )

        fig.add_trace(
            go.Bar(
                x=algos, y=states, name="States",
                marker_color="#10B981",
                text=states, textposition="auto",
            ),
            row=1, col=2,
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=40, r=40, t=50, b=80),
        )

        # Figure 2: Quality Score
        fig_quality = go.Figure()
        fig_quality.add_trace(
            go.Bar(
                x=algos, y=qualities, name="Quality Score (%)",
                marker_color="#8B5CF6",
                text=[f"{q:.1f}%" for q in qualities], textposition="auto",
            )
        )
        fig_quality.update_layout(
            title="Timetable Quality Score (%) - Higher is Better",
            yaxis=dict(range=[0, 105]),
            height=350,
            margin=dict(l=40, r=40, t=50, b=80),
        )

        return fig, fig_quality
    except Exception as e:
        return None, None
