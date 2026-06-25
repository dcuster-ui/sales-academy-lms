"""Admin — manage users, run a manual cert sync from Keboola."""

import streamlit as st
from auth.auth import require_role
from components.sidebar import render_sidebar
from db.database import query, execute
from db.keboola_sync import is_keboola_configured, sync_certifications

st.set_page_config(page_title="Admin · Sales Academy", page_icon="⚙️", layout="wide")
require_role(["admin"])
render_sidebar()

st.markdown("### Admin")

tab_users, tab_sync = st.tabs(["Users", "Cert sync"])

with tab_users:
    st.markdown("#### Add a rep")
    with st.form("add_rep"):
        email = st.text_input("Email", placeholder="rep@groupon.com")
        name = st.text_input("Full name", placeholder="Jane Doe")
        managers = query(
            "SELECT id, full_name FROM users WHERE role IN ('manager','admin') ORDER BY full_name"
        )
        mgr_options = ["(none)"] + [f"{m['full_name']}" for m in managers]
        mgr_choice = st.selectbox("Manager", mgr_options)
        cohorts = query("SELECT id, name FROM cohorts WHERE status IN ('upcoming','active') ORDER BY start_date DESC")
        cohort_choice = st.selectbox("Cohort", ["(none)"] + [c["name"] for c in cohorts])
        submitted = st.form_submit_button("Add rep", type="primary")
        if submitted:
            if not email or not name:
                st.error("Email and name are required.")
            else:
                mgr_id = None
                if mgr_choice != "(none)":
                    mgr_id = next(m["id"] for m in managers if m["full_name"] == mgr_choice)
                user_id = execute(
                    "INSERT INTO users (email, full_name, role, manager_id) VALUES (?, ?, 'rep', ?)",
                    (email.strip().lower(), name.strip(), mgr_id),
                )
                if cohort_choice != "(none)":
                    cid = next(c["id"] for c in cohorts if c["name"] == cohort_choice)
                    execute(
                        "INSERT INTO cohort_enrollments (cohort_id, user_id, hire_date) VALUES (?, ?, date('now'))",
                        (cid, user_id),
                    )
                st.success(f"Added {name}.")
                st.rerun()

    st.markdown("---")
    st.markdown("#### All users")
    users = query(
        """SELECT u.id, u.full_name, u.email, u.role, m.full_name AS manager, u.is_active
           FROM users u LEFT JOIN users m ON m.id = u.manager_id
           ORDER BY u.role, u.full_name"""
    )
    st.dataframe(users, use_container_width=True, hide_index=True)

with tab_sync:
    st.markdown("#### Pull certifications from Keboola")
    if not is_keboola_configured():
        st.warning(
            "`KBC_TOKEN` is not set in the environment. Set it on the Keboola data app "
            "and on your local shell for testing."
        )
    else:
        st.caption("Source: `in.c-sales-academy.cert_tracker`. Maps ✅ → pass and 🟥 → fail per rep.")
        if st.button("Run sync now", type="primary"):
            try:
                synced, skipped = sync_certifications()
                st.success(f"Synced {synced} cert results.")
                if skipped:
                    with st.expander(f"{len(skipped)} reps in source that aren't in this app"):
                        st.write(skipped)
            except Exception as e:
                st.error(f"Sync failed: {e}")
