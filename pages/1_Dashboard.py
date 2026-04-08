"""Dashboard — role-specific landing page."""

import streamlit as st
from auth.auth import require_auth, get_current_role, get_current_user_id, is_admin, is_manager
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row, cert_status_badges, status_badge
from models.cohorts import get_cohort_for_user, get_all_cohorts, get_cohort_reps, get_cohort_stats
from models.certifications import get_cert_status_for_user, get_certs_passed_count, get_cohort_cert_heatmap
from models.materials import get_material_progress_count, get_total_materials
from models.users import get_reps_for_manager
from utils.date_helpers import current_training_week, days_in_program, format_date
from utils.constants import CERTIFICATION_SHORT_NAMES
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Dashboard | Sales Academy", page_icon="📋", layout="wide")

st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
render_sidebar()

role = get_current_role()
user_id = get_current_user_id()


def render_rep_dashboard():
    cohort = get_cohort_for_user(user_id)
    if not cohort:
        st.warning("You are not enrolled in any active cohort.")
        return

    week = current_training_week(cohort["start_date"])
    days = days_in_program(cohort["start_date"])
    cert_statuses = get_cert_status_for_user(user_id, cohort["id"])
    passed = sum(1 for c in cert_statuses if c["status"] == "pass")
    materials_done = get_material_progress_count(user_id)
    total_materials = get_total_materials()

    st.markdown(f"### Welcome, {st.session_state['user_name']}")
    st.caption(f"Cohort: **{cohort['name']}** | Started: {format_date(cohort['start_date'])}")

    metric_row([
        ("Certs Completed", f"{passed} / 10", None),
        ("Materials Accessed", f"{materials_done} / {total_materials}", None),
        ("Current Week", f"Week {week}", None),
        ("Days in Program", str(days), None),
    ])

    st.markdown("#### Certification Status")
    cert_status_badges(cert_statuses)

    # Progress bar
    st.progress(passed / 10, text=f"{passed}/10 certifications passed")

    # Certs detail
    st.markdown("#### Certification Details")
    for cs in cert_statuses:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{cs['cert_name']}**")
        with col2:
            st.markdown(status_badge(cs["status"]), unsafe_allow_html=True)
        with col3:
            st.caption(f"{cs['attempts']} attempt(s)" if cs["attempts"] > 0 else "Not attempted")


def render_manager_dashboard():
    reps = get_reps_for_manager(user_id)
    if not reps:
        st.warning("No reps assigned to you.")
        return

    # Find cohort from first rep
    cohort = get_cohort_for_user(reps[0]["id"])
    if not cohort:
        st.warning("No active cohort found for your team.")
        return

    st.markdown(f"### Team Dashboard — {st.session_state['user_name']}")
    st.caption(f"Cohort: **{cohort['name']}**")

    # Stats
    heatmap_data = get_cohort_cert_heatmap(cohort["id"])
    total_reps = len(heatmap_data)
    avg_passed = sum(v["passed_count"] for v in heatmap_data.values()) / max(total_reps, 1)
    week = current_training_week(cohort["start_date"])
    behind_count = sum(1 for v in heatmap_data.values() if v["passed_count"] < 10)

    metric_row([
        ("Team Size", str(total_reps), None),
        ("Avg Certs Passed", f"{avg_passed:.1f} / 10", None),
        ("Current Week", f"Week {week}", None),
        ("Reps Behind", str(behind_count), None),
    ])

    # Heatmap
    st.markdown("#### Certification Heatmap")
    _render_heatmap(heatmap_data)

    # At-risk reps
    at_risk = [v for v in heatmap_data.values() if v["passed_count"] < 10]
    if at_risk:
        st.markdown("#### Reps Needing Attention")
        for rep in sorted(at_risk, key=lambda x: x["passed_count"]):
            st.markdown(f"- **{rep['name']}** — {rep['passed_count']}/10 certs passed")


def render_admin_dashboard():
    st.markdown("### Training Admin Dashboard")

    cohorts = get_all_cohorts()
    active_cohorts = [c for c in cohorts if c["status"] == "active"]

    # Overall stats
    total_reps = 0
    total_passed = 0
    total_possible = 0
    for cohort in active_cohorts:
        hm = get_cohort_cert_heatmap(cohort["id"])
        for v in hm.values():
            total_reps += 1
            total_passed += v["passed_count"]
            total_possible += v["total"]

    pass_rate = round(total_passed / max(total_possible, 1) * 100, 1)

    metric_row([
        ("Active Cohorts", str(len(active_cohorts)), None),
        ("Total Active Reps", str(total_reps), None),
        ("Overall Pass Rate", f"{pass_rate}%", None),
        ("Total Cohorts", str(len(cohorts)), None),
    ])

    # Cohort overview table
    st.markdown("#### Cohort Overview")
    if cohorts:
        rows = []
        for c in cohorts:
            stats = get_cohort_stats(c["id"])
            hm = get_cohort_cert_heatmap(c["id"])
            avg_pct = 0
            if hm:
                avg_pct = round(
                    sum(v["passed_count"] for v in hm.values()) / (len(hm) * 10) * 100, 1
                )
            rows.append({
                "Cohort": c["name"],
                "Status": c["status"].title(),
                "Start": format_date(c["start_date"]),
                "End": format_date(c["end_date"]),
                "Reps": stats["rep_count"],
                "Avg Completion": f"{avg_pct}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Per-cohort heatmap
    if active_cohorts:
        selected_cohort = st.selectbox(
            "View cohort heatmap",
            options=active_cohorts,
            format_func=lambda c: c["name"],
        )
        if selected_cohort:
            heatmap_data = get_cohort_cert_heatmap(selected_cohort["id"])
            _render_heatmap(heatmap_data)


def _render_heatmap(heatmap_data):
    """Render a certification heatmap using plotly."""
    if not heatmap_data:
        st.info("No data to display.")
        return

    from utils.constants import CERTIFICATION_SHORT_NAMES

    names = []
    z_data = []
    text_data = []

    for uid, data in sorted(heatmap_data.items(), key=lambda x: x[1]["name"]):
        names.append(data["name"])
        row = []
        text_row = []
        for cert_name in [c for c in data["certs"]]:
            status = data["certs"][cert_name]
            if status == "pass":
                row.append(1)
                text_row.append("Pass")
            elif status == "fail":
                row.append(-1)
                text_row.append("Fail")
            else:
                row.append(0)
                text_row.append("—")
        z_data.append(row)
        text_data.append(text_row)

    # Use short names for x-axis
    cert_labels = CERTIFICATION_SHORT_NAMES[:len(z_data[0])] if z_data else []

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=cert_labels,
        y=names,
        text=text_data,
        texttemplate="%{text}",
        textfont={"size": 11},
        colorscale=[[0, "#dc3545"], [0.5, "#e9ecef"], [1, "#28a745"]],
        zmin=-1,
        zmax=1,
        showscale=False,
    ))
    fig.update_layout(
        height=max(200, len(names) * 40 + 80),
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(side="top"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)


# Render based on role
if role == "rep":
    render_rep_dashboard()
elif role == "manager":
    render_manager_dashboard()
elif role == "admin":
    render_admin_dashboard()
