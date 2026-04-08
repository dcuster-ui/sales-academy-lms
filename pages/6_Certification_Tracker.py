"""Certification Tracker — Core operational page for entering and viewing cert results."""

import streamlit as st
import pandas as pd
from auth.auth import require_auth, get_current_role, get_current_user_id, is_admin
from components.sidebar import render_sidebar
from components.metrics_cards import status_badge
from models.cohorts import get_all_cohorts, get_cohort_reps, get_cohort_for_user
from models.certifications import (
    get_all_certifications, get_cert_status_for_user, record_attempt,
    get_cert_attempts_history, get_cohort_cert_heatmap,
)
from models.users import get_reps_for_manager
from utils.date_helpers import format_date
from utils.constants import CERTIFICATION_SHORT_NAMES
from db.keboola_sync import is_keboola_configured, sync_certifications
import plotly.graph_objects as go

st.set_page_config(page_title="Certification Tracker | Sales Academy", page_icon="📋", layout="wide")
st.markdown(
    '<style>[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:12px 16px;}</style>',
    unsafe_allow_html=True,
)

require_auth()
render_sidebar()

role = get_current_role()
user_id = get_current_user_id()

st.markdown("### Certification Tracker")

if is_admin():
    # --- Sync from Google Sheet ---
    if is_keboola_configured():
        sync_col1, sync_col2 = st.columns([1, 4])
        with sync_col1:
            if st.button("Sync from Google Sheet", type="secondary", use_container_width=True):
                with st.spinner("Syncing certification data from Google Sheet..."):
                    try:
                        synced, skipped = sync_certifications()
                        if synced > 0:
                            st.success(f"Synced {synced} certification update(s).")
                        else:
                            st.info("All certifications already up to date.")
                        if skipped:
                            st.caption(f"Skipped (not enrolled): {', '.join(skipped[:10])}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
        with sync_col2:
            st.caption("Pull latest certification results from the Google Sheet tracker into the LMS.")
        st.markdown("---")

    # --- Admin View: Data Entry + History ---
    tab_entry, tab_batch, tab_history = st.tabs(["Quick Entry", "Batch Entry", "History"])

    cohorts = get_all_cohorts()
    certs = get_all_certifications()

    with tab_entry:
        st.markdown("#### Record Certification Attempt")
        with st.form("cert_entry"):
            col1, col2 = st.columns(2)
            with col1:
                sel_cohort = st.selectbox("Cohort", options=cohorts, format_func=lambda c: c["name"], key="qe_cohort")
            with col2:
                sel_cert = st.selectbox("Certification", options=certs, format_func=lambda c: c["name"], key="qe_cert")

            # Get reps for selected cohort
            reps = get_cohort_reps(sel_cohort["id"]) if sel_cohort else []

            col3, col4 = st.columns(2)
            with col3:
                sel_rep = st.selectbox("Rep", options=reps, format_func=lambda r: r["full_name"], key="qe_rep")
            with col4:
                result = st.radio("Result", options=["pass", "fail"], horizontal=True, key="qe_result")

            col5, col6 = st.columns(2)
            with col5:
                score = st.number_input("Score (optional)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="qe_score")
            with col6:
                notes = st.text_input("Notes (optional)", key="qe_notes")

            if st.form_submit_button("Record Attempt", type="primary"):
                if sel_rep and sel_cert:
                    record_attempt(
                        user_id=sel_rep["id"],
                        certification_id=sel_cert["id"],
                        cohort_id=sel_cohort["id"],
                        result=result,
                        score=score if score > 0 else None,
                        evaluated_by=user_id,
                        notes=notes if notes else None,
                    )
                    st.success(f"Recorded {result.upper()} for {sel_rep['full_name']} on {sel_cert['name']}")
                    st.rerun()

    with tab_batch:
        st.markdown("#### Batch Certification Entry")
        col1, col2 = st.columns(2)
        with col1:
            batch_cohort = st.selectbox("Cohort", options=cohorts, format_func=lambda c: c["name"], key="batch_cohort")
        with col2:
            batch_cert = st.selectbox("Certification", options=certs, format_func=lambda c: c["name"], key="batch_cert")

        if batch_cohort and batch_cert:
            batch_reps = get_cohort_reps(batch_cohort["id"])
            if batch_reps:
                st.markdown(f"**{batch_cert['name']}** — {batch_cohort['name']}")

                # Build editable data
                batch_data = []
                for r in batch_reps:
                    status = get_cert_status_for_user(r["id"], batch_cohort["id"])
                    cert_status = next((s for s in status if s["cert_id"] == batch_cert["id"]), None)
                    current = cert_status["status"] if cert_status else "not_attempted"
                    batch_data.append({
                        "Rep": r["full_name"],
                        "Current Status": current.replace("_", " ").title(),
                        "New Result": "skip",
                        "_user_id": r["id"],
                    })

                df = pd.DataFrame(batch_data)
                edited = st.data_editor(
                    df[["Rep", "Current Status", "New Result"]],
                    column_config={
                        "Rep": st.column_config.TextColumn(disabled=True),
                        "Current Status": st.column_config.TextColumn(disabled=True),
                        "New Result": st.column_config.SelectboxColumn(
                            options=["skip", "pass", "fail"],
                            default="skip",
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="batch_editor",
                )

                if st.button("Save Batch Results", type="primary"):
                    saved = 0
                    for i, row in edited.iterrows():
                        if row["New Result"] != "skip":
                            record_attempt(
                                user_id=batch_data[i]["_user_id"],
                                certification_id=batch_cert["id"],
                                cohort_id=batch_cohort["id"],
                                result=row["New Result"],
                                evaluated_by=user_id,
                            )
                            saved += 1
                    if saved > 0:
                        st.success(f"Saved {saved} certification result(s).")
                        st.rerun()
                    else:
                        st.info("No results to save (all set to 'skip').")

    with tab_history:
        st.markdown("#### Attempt History")
        col1, col2, col3 = st.columns(3)
        with col1:
            hist_cohort = st.selectbox("Filter by cohort", options=[None] + cohorts, format_func=lambda c: "All" if c is None else c["name"], key="hist_cohort")
        with col2:
            hist_cert = st.selectbox("Filter by cert", options=[None] + certs, format_func=lambda c: "All" if c is None else c["name"], key="hist_cert")
        with col3:
            hist_limit = st.number_input("Limit", min_value=10, max_value=500, value=50, key="hist_limit")

        history = get_cert_attempts_history(
            cohort_id=hist_cohort["id"] if hist_cohort else None,
            certification_id=hist_cert["id"] if hist_cert else None,
            limit=hist_limit,
        )

        if history:
            hist_df = pd.DataFrame([{
                "Date": format_date(h["attempt_date"]),
                "Rep": h["rep_name"],
                "Certification": h["cert_name"],
                "Attempt #": h["attempt_number"],
                "Result": h["result"].upper(),
                "Score": h["score"] if h["score"] else "—",
                "Evaluator": h["evaluator_name"] or "—",
                "Notes": h["notes"] or "—",
            } for h in history])
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

            st.download_button(
                "Export History (CSV)",
                data=hist_df.to_csv(index=False),
                file_name="cert-history.csv",
                mime="text/csv",
            )
        else:
            st.info("No certification attempts found.")

elif role == "manager":
    # Manager: Read-only team view
    reps = get_reps_for_manager(user_id)
    if not reps:
        st.warning("No reps assigned.")
        st.stop()

    cohort = get_cohort_for_user(reps[0]["id"])
    if cohort:
        heatmap_data = get_cohort_cert_heatmap(cohort["id"])
        st.markdown(f"**{cohort['name']}** — Team Certification Status")

        # Heatmap
        names = []
        z_data = []
        text_data = []
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

else:
    # Rep: Read-only personal view
    cohort = get_cohort_for_user(user_id)
    if not cohort:
        st.warning("Not enrolled in any active cohort.")
        st.stop()

    cert_statuses = get_cert_status_for_user(user_id, cohort["id"])
    passed = sum(1 for c in cert_statuses if c["status"] == "pass")

    st.progress(passed / 10, text=f"{passed}/10 certifications passed")

    for cs in cert_statuses:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{cs['cert_name']}**")
                st.caption(f"Target: Week {cs['target_week']}")
            with col2:
                st.markdown(f"Attempts: **{cs['attempts']}**")
            with col3:
                st.markdown(status_badge(cs["status"]), unsafe_allow_html=True)
