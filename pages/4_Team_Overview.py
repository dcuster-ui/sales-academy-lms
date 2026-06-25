"""Team Overview — managers/admins see per-rep module progress and cert pass rate."""

import streamlit as st
import pandas as pd
from auth.auth import require_role, get_current_user_id, get_current_role
from components.sidebar import render_sidebar
from db.database import query
from models.modules import team_module_rollup

st.set_page_config(page_title="Team Overview · Sales Academy", page_icon="👥", layout="wide")
require_role(["manager", "admin"])
render_sidebar()

role = get_current_role()
viewer_id = get_current_user_id()

st.markdown("### Team Overview")

# Scope: managers see their own reps; admins see everyone.
if role == "manager":
    scope_label = "Your direct reports"
    manager_filter = viewer_id
else:
    scope_label = "All reps"
    manager_filter = None
    # Optional admin filter: pick a manager to scope to
    managers = query(
        "SELECT id, full_name FROM users WHERE role IN ('manager','admin') AND id IN (SELECT DISTINCT manager_id FROM users WHERE manager_id IS NOT NULL) ORDER BY full_name"
    )
    if managers:
        options = ["All reps"] + [m["full_name"] for m in managers]
        chosen = st.selectbox("Filter by manager", options, index=0)
        if chosen != "All reps":
            manager_filter = next(m["id"] for m in managers if m["full_name"] == chosen)
            scope_label = f"Reps under {chosen}"

st.caption(scope_label)

# --- Module completion rollup ---
rollup = team_module_rollup(manager_id=manager_filter)

# --- Cert pass-rate per rep (latest attempt per cert) ---
cert_rows = query(
    """SELECT u.id AS user_id,
              COUNT(DISTINCT c.id) AS total_certs,
              SUM(CASE WHEN ca.result = 'pass' THEN 1 ELSE 0 END) AS passed_certs
       FROM users u
       CROSS JOIN certifications c
       LEFT JOIN (
         SELECT certification_id, user_id, result,
                ROW_NUMBER() OVER (PARTITION BY certification_id, user_id ORDER BY attempt_number DESC) AS rn
         FROM certification_attempts
       ) ca ON ca.certification_id = c.id AND ca.user_id = u.id AND ca.rn = 1
       WHERE u.role = 'rep' AND u.is_active = 1 AND c.is_active = 1
       GROUP BY u.id"""
)
cert_by_user = {r["user_id"]: r for r in cert_rows}

rows = []
for r in rollup:
    total_lessons = r["total_lessons"] or 0
    completed_lessons = r["completed_lessons"] or 0
    lesson_pct = int(100 * completed_lessons / total_lessons) if total_lessons else 0
    cert = cert_by_user.get(r["user_id"], {})
    total_certs = cert.get("total_certs", 0) or 0
    passed_certs = cert.get("passed_certs", 0) or 0
    cert_pct = int(100 * passed_certs / total_certs) if total_certs else 0
    rows.append({
        "Rep": r["full_name"],
        "Email": r["email"],
        "Lessons complete": f"{completed_lessons}/{total_lessons}",
        "Module %": lesson_pct,
        "Certs passed": f"{passed_certs}/{total_certs}",
        "Cert %": cert_pct,
        "Last activity": (r["last_activity"] or "—")[:10],
    })

if not rows:
    st.info("No reps in scope.")
    st.stop()

df = pd.DataFrame(rows).sort_values(by="Module %", ascending=False)

# Summary metrics
c1, c2, c3 = st.columns(3)
c1.metric("Reps", len(df))
c2.metric("Avg module %", f"{int(df['Module %'].mean())}%")
c3.metric("Avg cert pass %", f"{int(df['Cert %'].mean())}%")

st.markdown("---")
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Module %": st.column_config.ProgressColumn("Module %", min_value=0, max_value=100, format="%d%%"),
        "Cert %": st.column_config.ProgressColumn("Cert %", min_value=0, max_value=100, format="%d%%"),
    },
)
