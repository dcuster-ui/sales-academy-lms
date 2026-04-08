"""Performance Analytics — Role-aware week-over-week cohort analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from auth.auth import require_auth, get_current_user_id, get_current_role, is_admin, is_manager, is_rep
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row
from models.cohorts import get_all_cohorts, get_cohort_reps, get_cohort_for_user
from models.certifications import get_cohort_pass_rates, get_cohort_cert_heatmap, get_all_certifications
from models.performance import (
    upsert_metric, get_metrics_for_cohort, get_cohort_metric_summary,
    get_weekly_metrics_by_rep, get_rep_weekly_totals,
    get_rep_weekly_metrics, get_rep_metric_summary,
)
from utils.date_helpers import format_date
from utils.constants import COLOR_PASS, COLOR_FAIL, COLOR_WARNING

st.set_page_config(page_title="Performance Analytics | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
render_sidebar()

role = get_current_role()
user_id = get_current_user_id()

# ── Role-based header and cohort resolution ──────────────────────────────────

if is_rep():
    st.markdown("### My Performance")
    st.caption("Your week-over-week productivity and sales metrics")

    # Auto-detect cohort for rep
    cohort = get_cohort_for_user(user_id)
    if not cohort:
        st.info("You're not enrolled in an active cohort.")
        st.stop()
    cohort_id = cohort["id"]
    st.markdown(f"**Cohort:** {cohort['name']}")

elif is_manager():
    st.markdown("### Team Performance")
    st.caption("Week-over-week productivity and sales metrics for your team")

    cohorts = get_all_cohorts()
    if not cohorts:
        st.info("No cohorts available.")
        st.stop()
    selected_cohort = st.selectbox("Select Cohort", options=cohorts, format_func=lambda c: c["name"])
    cohort_id = selected_cohort["id"]

else:  # admin
    st.markdown("### Performance Analytics")
    st.caption("Internal — Week-over-week productivity, deals, and GP by rep")

    cohorts = get_all_cohorts()
    if not cohorts:
        st.info("No cohorts available.")
        st.stop()
    selected_cohort = st.selectbox("Select Cohort", options=cohorts, format_func=lambda c: c["name"])
    cohort_id = selected_cohort["id"]


# ═══════════════════════════════════════════════════════════════════════════════
# REP VIEW — Personal metrics only
# ═══════════════════════════════════════════════════════════════════════════════
if is_rep():
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

    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGER & ADMIN VIEW — Full cohort analytics
# ═══════════════════════════════════════════════════════════════════════════════

# Build tabs — managers get WoW + Funnel, admins get all four
if is_admin():
    tab_wow, tab_productivity, tab_certs, tab_entry = st.tabs([
        "Week over Week", "Productivity Funnel", "Certification Analytics", "Data Entry",
    ])
else:
    tab_wow, tab_productivity = st.tabs([
        "Week over Week", "Productivity Funnel",
    ])


# --- Tab 1: Week over Week (Cohort Analysis style) ---
with tab_wow:
    weekly_data = get_weekly_metrics_by_rep(cohort_id)

    if not weekly_data:
        st.info("No performance data yet. Use the Data Entry tab to add metrics." if is_admin() else "No performance data yet for this cohort.")
    else:
        df = pd.DataFrame(weekly_data)
        df["week_label"] = "Week " + df["week_num"].astype(str)

        # Summary cards
        summary = get_cohort_metric_summary(cohort_id)
        metric_row([
            ("Total Dials", f"{summary['total_dials'] or 0:,}", None),
            ("Total Solid Calls", f"{summary['total_solid_calls'] or 0:,}", None),
            ("Total Appointments", f"{summary['total_appointments'] or 0:,}", None),
            ("Total Deals Closed", f"{summary['total_deals'] or 0:,}", None),
            ("Total GP", f"${summary['total_gp'] or 0:,.0f}", None),
        ])

        st.markdown("---")

        # --- Deals Closed by Rep by Week ---
        st.markdown("#### Deals Closed — Week over Week")
        deals_pivot = df.pivot_table(
            index="rep_name", columns="week_label", values="close_won",
            aggfunc="sum", fill_value=0,
        )
        week_cols = sorted(deals_pivot.columns, key=lambda x: int(x.split()[-1]))
        deals_pivot = deals_pivot[week_cols]
        deals_pivot["Total"] = deals_pivot.sum(axis=1)
        deals_pivot = deals_pivot.sort_values("Total", ascending=False)

        # Bar chart
        fig_deals = go.Figure()
        colors = px.colors.qualitative.Set2
        for i, week in enumerate(week_cols):
            fig_deals.add_trace(go.Bar(
                name=week,
                x=deals_pivot.index,
                y=deals_pivot[week],
                marker_color=colors[i % len(colors)],
                text=deals_pivot[week],
                textposition="auto",
            ))
        fig_deals.update_layout(
            barmode="group", height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Rep", yaxis_title="Deals Closed",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_deals, use_container_width=True)

        # Cohort analysis table
        st.dataframe(
            deals_pivot.style.format("{:.0f}").background_gradient(cmap="Greens", subset=week_cols),
            use_container_width=True,
        )

        st.markdown("---")

        # --- GP by Rep by Week ---
        st.markdown("#### Gross Profit (GP) — Week over Week")
        gp_pivot = df.pivot_table(
            index="rep_name", columns="week_label", values="gp_amount",
            aggfunc="sum", fill_value=0,
        )
        gp_pivot = gp_pivot[week_cols] if all(w in gp_pivot.columns for w in week_cols) else gp_pivot
        gp_pivot["Total"] = gp_pivot.sum(axis=1)
        gp_pivot = gp_pivot.sort_values("Total", ascending=False)

        fig_gp = go.Figure()
        for i, week in enumerate([c for c in gp_pivot.columns if c != "Total"]):
            fig_gp.add_trace(go.Bar(
                name=week,
                x=gp_pivot.index,
                y=gp_pivot[week],
                marker_color=colors[i % len(colors)],
                text=[f"${v:,.0f}" for v in gp_pivot[week]],
                textposition="auto",
            ))
        fig_gp.update_layout(
            barmode="group", height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Rep", yaxis_title="GP ($)",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_gp, use_container_width=True)

        st.dataframe(
            gp_pivot.style.format("${:,.0f}").background_gradient(cmap="Greens", subset=[c for c in gp_pivot.columns if c != "Total"]),
            use_container_width=True,
        )

        st.markdown("---")

        # --- Dials by Rep by Week (key productivity metric) ---
        st.markdown("#### Dials — Week over Week")
        dials_pivot = df.pivot_table(
            index="rep_name", columns="week_label", values="dials",
            aggfunc="sum", fill_value=0,
        )
        dials_pivot = dials_pivot[week_cols]
        dials_pivot["Total"] = dials_pivot.sum(axis=1)
        dials_pivot = dials_pivot.sort_values("Total", ascending=False)

        fig_dials = go.Figure()
        for i, week in enumerate(week_cols):
            fig_dials.add_trace(go.Bar(
                name=week,
                x=dials_pivot.index,
                y=dials_pivot[week],
                marker_color=colors[i % len(colors)],
                text=dials_pivot[week],
                textposition="auto",
            ))
        fig_dials.update_layout(
            barmode="group", height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Rep", yaxis_title="Dials",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_dials, use_container_width=True)

        st.dataframe(
            dials_pivot.style.format("{:,.0f}").background_gradient(cmap="Blues", subset=week_cols),
            use_container_width=True,
        )

        st.markdown("---")

        # --- Week-over-Week Trend Lines (all reps) ---
        st.markdown("#### Weekly Trend — Dials per Rep")
        fig_trend = px.line(
            df, x="week_label", y="dials", color="rep_name",
            markers=True, labels={"dials": "Dials", "week_label": "Week", "rep_name": "Rep"},
        )
        fig_trend.update_layout(
            height=400, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Export
        export_df = df[[
            "rep_name", "report_week", "week_label", "dials", "solid_calls",
            "connected", "dm_connect", "appointments_set", "needs_assessment",
            "presentations", "close_won", "um_closed", "um_launched", "gp_amount",
        ]]
        st.download_button(
            "Export Week-over-Week Data (CSV)",
            data=export_df.to_csv(index=False),
            file_name=f"wow-performance-{date.today().isoformat()}.csv",
            mime="text/csv",
        )


# --- Tab 2: Productivity Funnel ---
with tab_productivity:
    weekly_data = get_weekly_metrics_by_rep(cohort_id)

    if not weekly_data:
        st.info("No performance data yet.")
    else:
        df = pd.DataFrame(weekly_data)
        summary = get_cohort_metric_summary(cohort_id)

        # Sales funnel
        st.markdown("#### Sales Process Funnel — Cohort Total")
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

        st.markdown("---")

        # Per-rep funnel comparison
        st.markdown("#### Per-Rep Productivity Comparison")
        rep_totals = get_rep_weekly_totals(cohort_id)
        if rep_totals:
            rep_df = pd.DataFrame(rep_totals)
            rep_df.columns = [
                "Rep", "Dials", "Solid Calls", "Connected", "DM Connect",
                "Appointments", "Needs Assessment", "Presentations", "Deals", "GP",
            ]
            rep_df["GP"] = rep_df["GP"].apply(lambda x: f"${x:,.0f}")

            st.dataframe(rep_df, use_container_width=True, hide_index=True)

        # Stacked bar: funnel breakdown per rep
        st.markdown("#### Rep Funnel Breakdown")
        rep_totals_df = pd.DataFrame(get_rep_weekly_totals(cohort_id))
        if not rep_totals_df.empty:
            stages = [
                ("total_connected", "Connected", "#53A318"),
                ("total_dm_connect", "DM Connect", "#6FCC3C"),
                ("total_appointments", "Appts Set", "#81D64E"),
                ("total_needs_assessment", "Needs Assessment", "#A5EA72"),
                ("total_presentations", "Presentations", "#C8E8A0"),
            ]
            fig_stack = go.Figure()
            for col, label, color in stages:
                fig_stack.add_trace(go.Bar(
                    name=label,
                    x=rep_totals_df["rep_name"],
                    y=rep_totals_df[col],
                    marker_color=color,
                ))
            fig_stack.update_layout(
                barmode="stack", height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="Rep", yaxis_title="Count",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_stack, use_container_width=True)


# --- Tab 3: Certification Analytics (Admin only) ---
if is_admin():
    with tab_certs:
        st.markdown("#### Certification Pass Rates")
        pass_rates = get_cohort_pass_rates(cohort_id)

        if pass_rates:
            fig = go.Figure(data=go.Bar(
                x=[pr["rate"] for pr in pass_rates],
                y=[pr["cert_name"] for pr in pass_rates],
                orientation="h",
                marker_color=[
                    COLOR_PASS if pr["rate"] >= 80 else COLOR_WARNING if pr["rate"] >= 50 else COLOR_FAIL
                    for pr in pass_rates
                ],
                text=[f"{pr['rate']}% ({pr['passed']}/{pr['total']})" for pr in pass_rates],
                textposition="auto",
            ))
            fig.update_layout(
                height=400,
                margin=dict(l=0, r=20, t=10, b=0),
                xaxis=dict(title="Pass Rate (%)", range=[0, 105]),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            green_count = sum(1 for pr in pass_rates if pr["rate"] >= 80)
            yellow_count = sum(1 for pr in pass_rates if 50 <= pr["rate"] < 80)
            red_count = sum(1 for pr in pass_rates if pr["rate"] < 50)
            with col1:
                st.markdown(f'<div style="background:#d4edda;padding:12px;border-radius:8px;text-align:center;"><span style="font-size:1.5rem;">🟢</span><br><b>{green_count}</b> certs at 80%+ pass rate</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="background:#fff3cd;padding:12px;border-radius:8px;text-align:center;"><span style="font-size:1.5rem;">🟡</span><br><b>{yellow_count}</b> certs at 50-79% pass rate</div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="background:#f8d7da;padding:12px;border-radius:8px;text-align:center;"><span style="font-size:1.5rem;">🔴</span><br><b>{red_count}</b> certs below 50% pass rate</div>', unsafe_allow_html=True)

        # Reps behind schedule
        st.markdown("#### Reps Behind Schedule")
        heatmap_data = get_cohort_cert_heatmap(cohort_id)
        behind = [(v["name"], v["passed_count"]) for v in heatmap_data.values() if v["passed_count"] < 10]
        if behind:
            for name, count in sorted(behind, key=lambda x: x[1]):
                pct = count / 10
                status_color = COLOR_PASS if pct >= 0.8 else COLOR_WARNING if pct >= 0.5 else COLOR_FAIL
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
                    f'<span style="width:150px;font-weight:500;">{name}</span>'
                    f'<div style="flex:1;background:#e9ecef;border-radius:4px;height:20px;">'
                    f'<div style="width:{pct*100}%;background:{status_color};height:100%;border-radius:4px;'
                    f'text-align:center;color:#fff;font-size:0.75rem;line-height:20px;">{count}/10</div></div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("All reps have completed all certifications!")


    # --- Tab 4: Data Entry (Admin only) ---
    with tab_entry:
        st.markdown("#### Enter Weekly Performance Metrics")
        reps = get_cohort_reps(cohort_id)

        if not reps:
            st.warning("No reps in this cohort.")
        else:
            with st.form("perf_entry"):
                col1, col2 = st.columns(2)
                with col1:
                    sel_rep = st.selectbox("Rep", options=reps, format_func=lambda r: r["full_name"])
                with col2:
                    report_week = st.date_input("Week Starting", value=date.today())

                st.markdown("**Activity Metrics**")
                col3, col4, col5 = st.columns(3)
                with col3:
                    dials = st.number_input("Dials", min_value=0, value=0)
                    solid_calls = st.number_input("Solid Calls", min_value=0, value=0)
                    connected = st.number_input("Connected", min_value=0, value=0)
                with col4:
                    dm_connect = st.number_input("DM Connect", min_value=0, value=0)
                    appointments = st.number_input("Appointments Set", min_value=0, value=0)
                    needs_assess = st.number_input("Needs Assessment", min_value=0, value=0)
                with col5:
                    presentations = st.number_input("Presentations", min_value=0, value=0)
                    close_won = st.number_input("Deals Closed", min_value=0, value=0)

                st.markdown("**Revenue Metrics**")
                col6, col7, col8 = st.columns(3)
                with col6:
                    gp_amount = st.number_input("GP ($)", min_value=0.0, value=0.0, step=100.0)
                with col7:
                    um_closed = st.number_input("UM Closed", min_value=0, value=0)
                with col8:
                    um_launched = st.number_input("UM Launched", min_value=0, value=0)

                notes = st.text_input("Notes (optional)")

                if st.form_submit_button("Save Metrics", type="primary"):
                    upsert_metric(
                        user_id=sel_rep["id"],
                        cohort_id=cohort_id,
                        report_week=report_week.isoformat(),
                        dials=dials,
                        solid_calls=solid_calls,
                        connected=connected,
                        dm_connect=dm_connect,
                        appointments_set=appointments,
                        needs_assessment=needs_assess,
                        presentations=presentations,
                        close_won=close_won,
                        um_closed=um_closed,
                        um_launched=um_launched,
                        gp_amount=gp_amount,
                        notes=notes if notes else None,
                        entered_by=get_current_user_id(),
                    )
                    st.success(f"Saved metrics for {sel_rep['full_name']} — Week of {report_week}")
                    st.rerun()

        # Bulk CSV import
        st.markdown("---")
        st.markdown("#### Bulk Import (CSV)")
        st.caption("Upload a CSV with columns: email, report_week (YYYY-MM-DD), dials, solid_calls, connected, dm_connect, appointments_set, needs_assessment, presentations, close_won, um_closed, um_launched, gp_amount")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            try:
                import_df = pd.read_csv(uploaded)
                st.dataframe(import_df.head(), use_container_width=True)
                if st.button("Import Data"):
                    from db.database import query as db_query
                    imported = 0
                    for _, row in import_df.iterrows():
                        user = db_query("SELECT id FROM users WHERE email = ?", (row["email"],), one=True)
                        if user:
                            upsert_metric(
                                user_id=user["id"],
                                cohort_id=cohort_id,
                                report_week=str(row["report_week"]),
                                dials=int(row.get("dials", 0)),
                                solid_calls=int(row.get("solid_calls", 0)),
                                connected=int(row.get("connected", 0)),
                                dm_connect=int(row.get("dm_connect", 0)),
                                appointments_set=int(row.get("appointments_set", 0)),
                                needs_assessment=int(row.get("needs_assessment", 0)),
                                presentations=int(row.get("presentations", 0)),
                                close_won=int(row.get("close_won", 0)),
                                um_closed=int(row.get("um_closed", 0)),
                                um_launched=int(row.get("um_launched", 0)),
                                gp_amount=float(row.get("gp_amount", 0)),
                                entered_by=get_current_user_id(),
                            )
                            imported += 1
                    st.success(f"Imported {imported} rows.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
