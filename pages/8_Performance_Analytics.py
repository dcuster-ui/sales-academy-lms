"""My Performance — Rep personal week-over-week productivity view."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from auth.auth import require_auth, get_current_user_id, get_current_role, is_rep
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row
from models.cohorts import get_cohort_for_user
from models.performance import get_rep_weekly_metrics, get_rep_metric_summary

st.set_page_config(page_title="My Performance | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
render_sidebar()

role = get_current_role()
user_id = get_current_user_id()

# This page is for reps only — managers/admins use Cohort Analytics (page 3)
if not is_rep():
    st.info("Head over to **Cohort Analytics** for team performance data.")
    st.stop()

st.markdown("### My Performance")
st.caption("Your week-over-week productivity and sales metrics")

# Auto-detect cohort for rep
cohort = get_cohort_for_user(user_id)
if not cohort:
    st.info("You're not enrolled in an active cohort.")
    st.stop()
cohort_id = cohort["id"]
st.markdown(f"**Cohort:** {cohort['name']}")

weekly_data = get_rep_weekly_metrics(user_id, cohort_id)

if not weekly_data:
    st.info("No performance data recorded yet. Check back after your first week!")
    st.stop()

df = pd.DataFrame(weekly_data)
df["week_label"] = "Week " + df["week_num"].astype(str)

# Summary cards
summary = get_rep_metric_summary(user_id, cohort_id)
metric_row([
    ("Total Dials", f"{summary['total_dials'] or 0:,}", None),
    ("Total Solid Calls", f"{summary['total_solid_calls'] or 0:,}", None),
    ("Total Appointments", f"{summary['total_appointments'] or 0:,}", None),
    ("Deals Closed", f"{summary['total_deals'] or 0:,}", None),
    ("Total GP", f"${summary['total_gp'] or 0:,.0f}", None),
])

st.markdown("---")

# Weekly activity trend
st.markdown("#### Your Weekly Activity")
metrics_to_plot = {
    "dials": "Dials",
    "solid_calls": "Solid Calls",
    "connected": "Connected",
    "dm_connect": "DM Connect",
    "appointments_set": "Appointments",
}
fig_activity = go.Figure()
colors = ["#53A318", "#5DB82A", "#81D64E", "#A5EA72", "#C8E8A0"]
for i, (col, label) in enumerate(metrics_to_plot.items()):
    fig_activity.add_trace(go.Bar(
        name=label,
        x=df["week_label"],
        y=df[col],
        marker_color=colors[i],
        text=df[col],
        textposition="auto",
    ))
fig_activity.update_layout(
    barmode="group", height=400,
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis_title="Week", yaxis_title="Count",
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig_activity, use_container_width=True)

st.markdown("---")

# Deals & GP trend
st.markdown("#### Deals Closed & GP — Week over Week")
col1, col2 = st.columns(2)
with col1:
    fig_deals = go.Figure()
    fig_deals.add_trace(go.Bar(
        x=df["week_label"], y=df["close_won"],
        marker_color="#53A318",
        text=df["close_won"], textposition="auto",
        name="Deals Closed",
    ))
    fig_deals.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="Week", yaxis_title="Deals",
    )
    st.plotly_chart(fig_deals, use_container_width=True)

with col2:
    fig_gp = go.Figure()
    fig_gp.add_trace(go.Bar(
        x=df["week_label"], y=df["gp_amount"],
        marker_color="#5DB82A",
        text=[f"${v:,.0f}" for v in df["gp_amount"]], textposition="auto",
        name="GP",
    ))
    fig_gp.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="Week", yaxis_title="GP ($)",
    )
    st.plotly_chart(fig_gp, use_container_width=True)

# Weekly detail table
st.markdown("#### Weekly Detail")
detail_df = df[[
    "week_label", "dials", "solid_calls", "connected", "dm_connect",
    "appointments_set", "needs_assessment", "presentations",
    "close_won", "um_closed", "um_launched", "gp_amount",
]].copy()
detail_df.columns = [
    "Week", "Dials", "Solid Calls", "Connected", "DM Connect",
    "Appts", "Needs Assessment", "Presentations",
    "Deals", "UM Closed", "UM Launched", "GP",
]
detail_df["GP"] = detail_df["GP"].apply(lambda x: f"${x:,.0f}")
st.dataframe(detail_df, use_container_width=True, hide_index=True)

# Sales funnel
st.markdown("---")
st.markdown("#### Your Sales Funnel")
funnel_stages = ["Dials", "Connected", "DM Connect", "Appts Set", "Needs Assessment", "Presentations", "Close Won"]
funnel_values = [
    summary["total_dials"] or 0,
    summary["total_connected"] or 0,
    summary["total_dm_connect"] or 0,
    summary["total_appointments"] or 0,
    summary["total_needs_assessment"] or 0,
    summary["total_presentations"] or 0,
    summary["total_deals"] or 0,
]
fig_funnel = go.Figure(go.Funnel(
    y=funnel_stages, x=funnel_values,
    textinfo="value+percent initial",
    marker_color=["#53A318", "#5DB82A", "#6FCC3C", "#81D64E", "#93E060", "#A5EA72", "#C8E8A0"],
))
fig_funnel.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig_funnel, use_container_width=True)
