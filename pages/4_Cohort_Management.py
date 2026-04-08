"""Cohort Management — Admin only."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from auth.auth import require_auth, require_role, get_current_user_id
from components.sidebar import render_sidebar
from components.metrics_cards import status_badge
from models.cohorts import get_all_cohorts, get_cohort, get_cohort_reps, create_cohort, enroll_rep, get_cohort_stats
from models.users import get_all_users, create_user, get_user, set_user_active
from db.database import execute, query
from utils.date_helpers import format_date

st.set_page_config(page_title="Cohort Management | Sales Academy", page_icon="📋", layout="wide")

require_auth()
require_role(["admin"])
render_sidebar()

st.markdown("### Cohort Management")

tab1, tab2, tab3 = st.tabs(["Cohorts", "Create Cohort", "Manage Users"])

# --- Tab 1: Cohort List ---
with tab1:
    cohorts = get_all_cohorts()
    if not cohorts:
        st.info("No cohorts yet. Create one in the next tab.")
    else:
        for cohort in cohorts:
            stats = get_cohort_stats(cohort["id"])
            with st.expander(f"**{cohort['name']}** — {cohort['status'].title()} ({stats['rep_count']} reps)"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"**Start:** {format_date(cohort['start_date'])}")
                with col2:
                    st.markdown(f"**End:** {format_date(cohort['end_date'])}")
                with col3:
                    st.markdown(f"**Status:** {status_badge(cohort['status'])}", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"**Reps:** {stats['rep_count']}")

                # Enrolled reps (active only)
                reps = get_cohort_reps(cohort["id"])
                all_reps = get_cohort_reps(cohort["id"], include_inactive=True)
                inactive_reps = [r for r in all_reps if not r["is_active"]]

                if reps:
                    st.markdown(f"**Active Reps ({len(reps)}):**")
                    rep_data = [{
                        "Name": r["full_name"],
                        "Email": r["email"],
                        "Hire Date": format_date(r["hire_date"]),
                        "Status": r["enrollment_status"].title(),
                    } for r in reps]
                    st.dataframe(pd.DataFrame(rep_data), use_container_width=True, hide_index=True)

                if inactive_reps:
                    st.markdown(f"**Inactive Reps ({len(inactive_reps)}):**")
                    inactive_data = [{
                        "Name": r["full_name"],
                        "Email": r["email"],
                        "Hire Date": format_date(r["hire_date"]),
                    } for r in inactive_reps]
                    st.dataframe(pd.DataFrame(inactive_data), use_container_width=True, hide_index=True)

                # Add rep to cohort
                st.markdown("**Add Rep to Cohort:**")
                available_reps = get_all_users(role="rep")
                enrolled_ids = {r["id"] for r in reps}
                available = [r for r in available_reps if r["id"] not in enrolled_ids]

                if available:
                    with st.form(f"add_rep_{cohort['id']}"):
                        sel_rep = st.selectbox(
                            "Select rep",
                            options=available,
                            format_func=lambda r: f"{r['full_name']} ({r['email']})",
                            key=f"sel_rep_{cohort['id']}",
                        )
                        hire_date = st.date_input("Hire date", value=date.today(), key=f"hire_{cohort['id']}")
                        if st.form_submit_button("Enroll Rep"):
                            enroll_rep(cohort["id"], sel_rep["id"], hire_date.isoformat())
                            st.success(f"Enrolled {sel_rep['full_name']} in {cohort['name']}")
                            st.rerun()
                else:
                    st.caption("All reps are already enrolled.")

                # Status update
                new_status = st.selectbox(
                    "Update status",
                    options=["upcoming", "active", "completed", "archived"],
                    index=["upcoming", "active", "completed", "archived"].index(cohort["status"]),
                    key=f"status_{cohort['id']}",
                )
                if new_status != cohort["status"]:
                    if st.button(f"Update to {new_status.title()}", key=f"update_btn_{cohort['id']}"):
                        execute("UPDATE cohorts SET status = ? WHERE id = ?", (new_status, cohort["id"]))
                        st.success(f"Updated {cohort['name']} to {new_status}")
                        st.rerun()

# --- Tab 2: Create Cohort ---
with tab2:
    st.markdown("#### Create New Cohort")
    with st.form("create_cohort"):
        name = st.text_input("Cohort Name", placeholder="e.g., April 2026")
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start Date", value=date.today())
        with col2:
            end = st.date_input("End Date", value=date.today() + timedelta(weeks=6))

        if st.form_submit_button("Create Cohort", type="primary"):
            if name:
                create_cohort(name, start.isoformat(), end.isoformat(), "upcoming")
                st.success(f"Created cohort: {name}")
                st.rerun()
            else:
                st.error("Please enter a cohort name.")

# --- Tab 3: Manage Users ---
with tab3:
    st.markdown("#### All Users")
    show_inactive = st.checkbox("Show inactive users", value=False)
    users = get_all_users(active_only=not show_inactive)
    if users:
        for u in users:
            col_name, col_role, col_status, col_action = st.columns([3, 2, 1, 2])
            with col_name:
                st.markdown(f"**{u['full_name']}**  \n{u['email']}")
            with col_role:
                st.caption(u["role"].title())
            with col_status:
                if u["is_active"]:
                    st.markdown('<span style="color:#53A318;font-weight:600;">Active</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#dc3545;font-weight:600;">Inactive</span>', unsafe_allow_html=True)
            with col_action:
                if u["role"] == "rep":
                    if u["is_active"]:
                        if st.button("Deactivate", key=f"deact_{u['id']}", type="secondary"):
                            set_user_active(u["id"], False)
                            st.rerun()
                    else:
                        if st.button("Reactivate", key=f"react_{u['id']}", type="primary"):
                            set_user_active(u["id"], True)
                            st.rerun()
        st.markdown("---")

    st.markdown("#### Create New User")
    with st.form("create_user"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
        with col2:
            new_role = st.selectbox("Role", options=["rep", "manager", "admin"])
            managers = get_all_users(role="manager")
            new_manager = st.selectbox(
                "Manager (for reps)",
                options=[None] + managers,
                format_func=lambda m: "None" if m is None else m["full_name"],
            )

        if st.form_submit_button("Create User"):
            if new_name and new_email:
                mgr_id = new_manager["id"] if new_manager else None
                create_user(new_email, new_name, new_role, mgr_id)
                st.success(f"Created user: {new_name}")
                st.rerun()
            else:
                st.error("Please fill in name and email.")
