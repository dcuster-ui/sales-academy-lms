"""Cohort Analytics — Unified team overview, performance, and certification tracking."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from auth.auth import require_auth, require_role, get_current_user_id, is_admin, is_manager
from components.sidebar import render_sidebar
from components.metrics_cards import metric_row
from models.cohorts import get_all_cohorts, get_cohort_reps, get_cohort_for_user
from models.certifications import get_cohort_cert_heatmap, get_cohort_pass_rates
from models.users import get_reps_for_manager
from models.performance import (
    upsert_metric, get_cohort_metric_summary,
    get_weekly_metrics_by_rep, get_rep_weekly_totals,
)
from utils.date_helpers import current_training_week
from utils.constants import CERTIFICATION_SHORT_NAMES, COLOR_PASS, COLOR_FAIL, COLOR_WARNING

st.set_page_config(page_title="Cohort Analytics | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
require_role(["manager", "admin"])
render_sidebar()

user_id = get_current_user_id()

st.markdown("### Cohort Analytics")

# ── Cohort selection ───────────────────────────────────────────────────────────
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
week = current_training_week(selected_cohort["start_date"])

# ── Build tabs ─────────────────────────────────────────────────────────────────
if is_admin():
    tab_overview, tab_wow, tab_funnel, tab_entry = st.tabs([
        "Overview", "Week over Week", "Sales Funnel", "Data Entry",
    ])
else:
    tab_overview, tab_wow, tab_funnel = st.tabs([
        "Overview", "Week over Week", "Sales Funnel",
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW — Cert heatmap, pass rates, leaderboard
# ═══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    heatmap_data = get_cohort_cert_heatmap(cohort_id)
    total_reps = len(heatmap_data)

    if total_reps == 0:
        st.info("No reps enrolled in this cohort.")
    else:
        avg_passed = sum(v["passed_count"] for v in heatmap_data.values()) / total_reps
        completion_rate = round(avg_passed / 10 * 100, 1)
        behind_count = sum(1 for v in heatmap_data.values() if v["passed_count"] < 10)

        metric_row([
            ("Total Reps", str(total_reps), None),
            ("Avg Certs Passed", f"{avg_passed:.1f} / 10", None),
            ("Completion Rate", f"{completion_rate}%", None),
            ("Current Week", f"Week {week}", None),
        ])

        # --- Certification Heatmap ---
        st.markdown("#### Certification Status")
        names, z_data, text_data = [], [], []
        for uid, data in sorted(heatmap_data.items(), key=lambda x: x[1]["name"]):
            names.append(data["name"])
            row, text_row = [], []
            for cert_name in data["certs"]:
                status = data["certs"][cert_name]
                row.append(1 if status == "pass" else (-1 if status == "fail" else 0))
                text_row.append("Pass" if status == "pass" else ("Fail" if status == "fail" else "—"))
            z_data.append(row)
            text_data.append(text_row)

        cert_labels = CERTIFICATION_SHORT_NAMES[:len(z_data[0])] if z_data else []
        fig = go.Figure(data=go.Heatmap(
            z=z_data, x=cert_labels, y=names, text=text_data,
            texttemplate="%{text}", textfont={"size": 11},
            colorscale=[[0, "#dc3545"], [0.5, "#e9ecef"], [1, "#28a745"]],
            zmin=-1, zmax=1, showscale=False,
        ))
        fig.update_layout(
            height=max(250, len(names) * 40 + 80),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(side="top"), yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # --- Leaderboard + Pass Rates side by side ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Leaderboard")
            leaderboard = sorted(heatmap_data.values(), key=lambda x: x["passed_count"], reverse=True)
            for i, rep in enumerate(leaderboard, 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                st.markdown(f"{medal} **{rep['name']}** — {rep['passed_count']}/10")
                st.progress(rep["passed_count"] / 10)

        with col2:
            st.markdown("#### Certification Pass Rates")
            pass_rates = get_cohort_pass_rates(cohort_id)
            if pass_rates:
                fig2 = go.Figure(data=go.Bar(
                    x=[pr["rate"] for pr in pass_rates],
                    y=[pr["cert_name"] for pr in pass_rates],
                    orientation="h",
                    marker_color=[COLOR_PASS if pr["rate"] >= 80 else COLOR_WARNING if pr["rate"] >= 50 else COLOR_FAIL for pr in pass_rates],
                    text=[f"{pr['rate']}% ({pr['passed']}/{pr['total']})" for pr in pass_rates],
                    textposition="auto",
                ))
                fig2.update_layout(
                    height=400, margin=dict(l=0, r=20, t=10, b=0),
                    xaxis=dict(title="Pass Rate (%)", range=[0, 105]),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # --- Reps behind schedule ---
        behind = [(v["name"], v["passed_count"]) for v in heatmap_data.values() if v["passed_count"] < 10]
        if behind:
            st.markdown("#### Reps Behind Schedule")
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
            file_name=f"cohort-overview-{selected_cohort['name'].lower().replace(' ', '-')}.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: WEEK OVER WEEK — Deals, GP, Dials by rep by week
# ═══════════════════════════════════════════════════════════════════════════════
with tab_wow:
    weekly_data = get_weekly_metrics_by_rep(cohort_id)

    if not weekly_data:
        st.info("No performance data yet." + (" Use the Data Entry tab to add metrics." if is_admin() else ""))
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

        colors = px.colors.qualitative.Set2
        fig_deals = go.Figure()
        for i, wk in enumerate(week_cols):
            fig_deals.add_trace(go.Bar(
                name=wk, x=deals_pivot.index, y=deals_pivot[wk],
                marker_color=colors[i % len(colors)],
                text=deals_pivot[wk], textposition="auto",
            ))
        fig_deals.update_layout(
            barmode="group", height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Rep", yaxis_title="Deals Closed",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_deals, use_container_width=True)
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
        for i, wk in enumerate([c for c in gp_pivot.columns if c != "Total"]):
            fig_gp.add_trace(go.Bar(
                name=wk, x=gp_pivot.index, y=gp_pivot[wk],
                marker_color=colors[i % len(colors)],
                text=[f"${v:,.0f}" for v in gp_pivot[wk]], textposition="auto",
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

        # --- Dials by Rep by Week ---
        st.markdown("#### Dials — Week over Week")
        dials_pivot = df.pivot_table(
            index="rep_name", columns="week_label", values="dials",
            aggfunc="sum", fill_value=0,
        )
        dials_pivot = dials_pivot[week_cols]
        dials_pivot["Total"] = dials_pivot.sum(axis=1)
        dials_pivot = dials_pivot.sort_values("Total", ascending=False)

        fig_dials = go.Figure()
        for i, wk in enumerate(week_cols):
            fig_dials.add_trace(go.Bar(
                name=wk, x=dials_pivot.index, y=dials_pivot[wk],
                marker_color=colors[i % len(colors)],
                text=dials_pivot[wk], textposition="auto",
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

        # --- Trend Lines ---
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


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: SALES FUNNEL — Cohort funnel + per-rep comparison
# ═══════════════════════════════════════════════════════════════════════════════
with tab_funnel:
    weekly_data = get_weekly_metrics_by_rep(cohort_id)

    if not weekly_data:
        st.info("No performance data yet.")
    else:
        summary = get_cohort_metric_summary(cohort_id)

        st.markdown("#### Sales Process Funnel — Cohort Total")
        funnel_stages = ["Dials", "Connected", "DM Connect", "Appts Set", "Needs Assessment", "Presentations", "Close Won"]
        funnel_values = [
            summary["total_dials"] or 0, summary["total_connected"] or 0,
            summary["total_dm_connect"] or 0, summary["total_appointments"] or 0,
            summary["total_needs_assessment"] or 0, summary["total_presentations"] or 0,
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

        # Per-rep productivity table
        st.markdown("#### Per-Rep Productivity")
        rep_totals = get_rep_weekly_totals(cohort_id)
        if rep_totals:
            rep_df = pd.DataFrame(rep_totals)
            rep_df.columns = [
                "Rep", "Dials", "Solid Calls", "Connected", "DM Connect",
                "Appointments", "Needs Assessment", "Presentations", "Deals", "GP",
            ]
            rep_df["GP"] = rep_df["GP"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(rep_df, use_container_width=True, hide_index=True)

        # Stacked bar
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
                    name=label, x=rep_totals_df["rep_name"], y=rep_totals_df[col],
                    marker_color=color,
                ))
            fig_stack.update_layout(
                barmode="stack", height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="Rep", yaxis_title="Count",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_stack, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: DATA ENTRY — Admin only
# ═══════════════════════════════════════════════════════════════════════════════
if is_admin():
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
                        user_id=sel_rep["id"], cohort_id=cohort_id,
                        report_week=report_week.isoformat(),
                        dials=dials, solid_calls=solid_calls, connected=connected,
                        dm_connect=dm_connect, appointments_set=appointments,
                        needs_assessment=needs_assess, presentations=presentations,
                        close_won=close_won, um_closed=um_closed, um_launched=um_launched,
                        gp_amount=gp_amount, notes=notes if notes else None,
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
                                user_id=user["id"], cohort_id=cohort_id,
                                report_week=str(row["report_week"]),
                                dials=int(row.get("dials", 0)), solid_calls=int(row.get("solid_calls", 0)),
                                connected=int(row.get("connected", 0)), dm_connect=int(row.get("dm_connect", 0)),
                                appointments_set=int(row.get("appointments_set", 0)),
                                needs_assessment=int(row.get("needs_assessment", 0)),
                                presentations=int(row.get("presentations", 0)),
                                close_won=int(row.get("close_won", 0)),
                                um_closed=int(row.get("um_closed", 0)), um_launched=int(row.get("um_launched", 0)),
                                gp_amount=float(row.get("gp_amount", 0)),
                                entered_by=get_current_user_id(),
                            )
                            imported += 1
                    st.success(f"Imported {imported} rows.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
