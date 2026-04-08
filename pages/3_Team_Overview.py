"""Team Overview — Manager and Admin cohort view."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from auth.auth import require_auth, require_role, get_current_user_id, is_admin
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row
from models.cohorts import get_all_cohorts, get_cohort_reps, get_cohort_for_user
from models.certifications import get_cohort_cert_heatmap, get_certs_passed_count, get_cohort_pass_rates
from models.users import get_reps_for_manager
from utils.date_helpers import current_training_week
from utils.constants import CERTIFICATION_SHORT_NAMES

st.set_page_config(page_title="Team Overview | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
require_role(["manager", "admin"])
render_sidebar()

user_id = get_current_user_id()

st.markdown("### Team Overview")

# Cohort selection
if is_admin():
    cohorts = get_all_cohorts()
    selected_cohort = st.selectbox("Select Cohort", options=cohorts, format_func=lambda c: c["name"])
else:
    reps = get_reps_for_manager(user_id)
    if reps:
        selected_cohort = get_cohort_for_user(reps[0]["id"])
    else:
        st.warning("No reps assigned to you.")
        st.stop()

if not selected_cohort:
    st.info("No cohorts available.")
    st.stop()

cohort_id = selected_cohort["id"]
heatmap_data = get_cohort_cert_heatmap(cohort_id)
week = current_training_week(selected_cohort["start_date"])
total_reps = len(heatmap_data)

if total_reps == 0:
    st.info("No reps enrolled in this cohort.")
    st.stop()

avg_passed = sum(v["passed_count"] for v in heatmap_data.values()) / total_reps
completion_rate = round(avg_passed / 10 * 100, 1)
behind_count = sum(1 for v in heatmap_data.values() if v["passed_count"] < 10)

metric_row([
    ("Total Reps", str(total_reps), None),
    ("Avg Certs Passed", f"{avg_passed:.1f} / 10", None),
    ("Completion Rate", f"{completion_rate}%", None),
    ("Current Week", f"Week {week}", None),
])

# Heatmap
st.markdown("#### Certification Heatmap")
names = []
z_data = []
text_data = []

for uid, data in sorted(heatmap_data.items(), key=lambda x: x[1]["name"]):
    names.append(data["name"])
    row = []
    text_row = []
    for cert_name in data["certs"]:
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

cert_labels = CERTIFICATION_SHORT_NAMES[:len(z_data[0])] if z_data else []

fig = go.Figure(data=go.Heatmap(
    z=z_data,
    x=cert_labels,
    y=names,
    text=text_data,
    texttemplate="%{text}",
    textfont={"size": 11},
    colorscale=[[0, "#dc3545"], [0.5, "#e9ecef"], [1, "#28a745"]],
    zmin=-1, zmax=1,
    showscale=False,
))
fig.update_layout(
    height=max(250, len(names) * 40 + 80),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(side="top"),
    yaxis=dict(autorange="reversed"),
)
st.plotly_chart(fig, use_container_width=True)

# Leaderboard
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Leaderboard")
    leaderboard = sorted(heatmap_data.values(), key=lambda x: x["passed_count"], reverse=True)
    for i, rep in enumerate(leaderboard, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        bar_pct = rep["passed_count"] / 10
        st.markdown(f"{medal} **{rep['name']}** — {rep['passed_count']}/10")
        st.progress(bar_pct)

with col2:
    st.markdown("#### Certification Pass Rates")
    pass_rates = get_cohort_pass_rates(cohort_id)
    if pass_rates:
        fig2 = go.Figure(data=go.Bar(
            x=[pr["rate"] for pr in pass_rates],
            y=[pr["cert_name"] for pr in pass_rates],
            orientation="h",
            marker_color=["#28a745" if pr["rate"] >= 80 else "#ffc107" if pr["rate"] >= 50 else "#dc3545" for pr in pass_rates],
            text=[f"{pr['rate']}%" for pr in pass_rates],
            textposition="auto",
        ))
        fig2.update_layout(
            height=400,
            margin=dict(l=0, r=20, t=10, b=0),
            xaxis=dict(title="Pass Rate (%)", range=[0, 105]),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)

# Export
st.markdown("---")
export_rows = []
for uid, data in heatmap_data.items():
    row = {"Name": data["name"], "Certs Passed": data["passed_count"]}
    row.update(data["certs"])
    export_rows.append(row)
df_export = pd.DataFrame(export_rows)
st.download_button(
    "Download Team Data (CSV)",
    data=df_export.to_csv(index=False),
    file_name=f"team-overview-{selected_cohort['name'].lower().replace(' ', '-')}.csv",
    mime="text/csv",
)
