"""My Progress — Rep personal progress view (managers/admins can view any rep)."""

import streamlit as st
from auth.auth import require_auth, get_current_role, get_current_user_id, is_admin, is_manager
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row, status_badge
from models.cohorts import get_cohort_for_user, get_all_cohorts, get_cohort_reps
from models.certifications import get_cert_status_for_user, get_certs_passed_count
from models.materials import get_materials_with_progress, get_material_progress_count, get_total_materials
from models.users import get_reps_for_manager, get_user
from utils.date_helpers import current_training_week, days_in_program, format_date
import plotly.graph_objects as go

st.set_page_config(page_title="My Progress | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
render_sidebar()

role = get_current_role()
user_id = get_current_user_id()

# Allow managers/admins to select a rep
viewing_user_id = user_id
if is_manager():
    reps = get_reps_for_manager(user_id)
    if reps:
        selected = st.selectbox(
            "View progress for",
            options=reps,
            format_func=lambda r: r["full_name"],
        )
        if selected:
            viewing_user_id = selected["id"]
elif is_admin():
    cohorts = get_all_cohorts()
    if cohorts:
        sel_cohort = st.selectbox("Select cohort", options=cohorts, format_func=lambda c: c["name"])
        if sel_cohort:
            reps = get_cohort_reps(sel_cohort["id"])
            if reps:
                selected = st.selectbox("Select rep", options=reps, format_func=lambda r: r["full_name"])
                if selected:
                    viewing_user_id = selected["id"]

# Get data
user_info = get_user(viewing_user_id)
cohort = get_cohort_for_user(viewing_user_id)

if not cohort:
    st.warning("This user is not enrolled in any active cohort.")
    st.stop()

cert_statuses = get_cert_status_for_user(viewing_user_id, cohort["id"])
passed = sum(1 for c in cert_statuses if c["status"] == "pass")
week = current_training_week(cohort["start_date"])
days = days_in_program(cohort["start_date"])
materials_done = get_material_progress_count(viewing_user_id)
total_materials = get_total_materials()

# Header
st.markdown(f"### {user_info['full_name']}'s Progress")
st.caption(f"Cohort: **{cohort['name']}** | Hire Date: {format_date(cohort.get('hire_date', cohort['start_date']))} | Week {week}")

metric_row([
    ("Certs Passed", f"{passed} / 10", None),
    ("Materials Completed", f"{materials_done} / {total_materials}", None),
    ("Training Week", f"Week {week}", None),
    ("Days in Program", str(days), None),
])

# Progress donut chart
col_chart, col_detail = st.columns([1, 2])
with col_chart:
    fig = go.Figure(data=[go.Pie(
        values=[passed, 10 - passed],
        labels=["Passed", "Remaining"],
        hole=0.65,
        marker_colors=["#53A318", "#e9ecef"],
        textinfo="none",
    )])
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        annotations=[dict(text=f"<b>{passed}/10</b>", x=0.5, y=0.5, font_size=24, showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True)

with col_detail:
    st.markdown("#### Certification Details")

# Certification grid
st.markdown("---")
cols_per_row = 2
for i in range(0, len(cert_statuses), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(cert_statuses):
            break
        cs = cert_statuses[idx]
        with col:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{cs['cert_name']}**")
                    st.caption(f"Target: Week {cs['target_week']} | Attempts: {cs['attempts']}")
                    if cs["passed_date"]:
                        st.caption(f"Passed: {format_date(cs['passed_date'])}")
                with c2:
                    if cs["status"] == "pass":
                        st.markdown(
                            '<div style="text-align:center;padding:12px;"><span style="font-size:2rem;color:#28a745;">&#10003;</span><br><span style="color:#28a745;font-weight:600;">PASSED</span></div>',
                            unsafe_allow_html=True,
                        )
                    elif cs["status"] == "fail":
                        st.markdown(
                            '<div style="text-align:center;padding:12px;"><span style="font-size:2rem;color:#dc3545;">&#10007;</span><br><span style="color:#dc3545;font-weight:600;">FAILED</span></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div style="text-align:center;padding:12px;"><span style="font-size:2rem;color:#ccc;">&#8212;</span><br><span style="color:#999;">PENDING</span></div>',
                            unsafe_allow_html=True,
                        )

# Materials section
st.markdown("---")
st.markdown("#### Materials Progress")
materials = get_materials_with_progress(viewing_user_id)

if materials:
    # Group by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for m in materials:
        by_category[m["category_name"]].append(m)

    for cat_name in sorted(by_category.keys(), key=lambda x: by_category[x][0]["cat_order"]):
        items = by_category[cat_name]
        completed = sum(1 for m in items if m["progress_status"] == "completed")
        with st.expander(f"**{cat_name}** — {completed}/{len(items)} completed"):
            for m in items:
                c1, c2 = st.columns([4, 1])
                with c1:
                    icon = {"deck": "📊", "video": "🎬", "document": "📄", "link": "🔗"}.get(m["material_type"], "📁")
                    st.markdown(f"{icon} {m['title']}")
                with c2:
                    if m["progress_status"] == "completed":
                        st.markdown("&#10003; Done", unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="color:#ccc;">Not done</span>', unsafe_allow_html=True)
