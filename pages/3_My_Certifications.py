"""My Certifications — per-rep cert pass/fail history from the Keboola cert tracker."""

import streamlit as st
import pandas as pd
from auth.auth import require_auth, get_current_user_id
from components.sidebar import render_sidebar
from db.database import query
from utils.constants import COLOR_PASS, COLOR_FAIL, COLOR_PENDING

st.set_page_config(page_title="My Certifications · Sales Academy", page_icon="🎓", layout="wide")
require_auth()
render_sidebar()

user_id = get_current_user_id()

st.markdown("### Your Certifications")
st.caption("Pulled from the BD certification tracker. Talk to your manager if a result looks wrong.")

# All certs, with latest attempt (if any) for this user
rows = query(
    """SELECT c.id, c.name, c.category, c.target_week,
              ca.result, ca.score, ca.attempt_number, ca.attempt_date, ca.notes
       FROM certifications c
       LEFT JOIN (
         SELECT certification_id, user_id, result, score, attempt_number, attempt_date, notes,
                ROW_NUMBER() OVER (PARTITION BY certification_id, user_id ORDER BY attempt_number DESC) AS rn
         FROM certification_attempts
         WHERE user_id = ?
       ) ca ON ca.certification_id = c.id AND ca.rn = 1
       WHERE c.is_active = 1
       ORDER BY c.display_order""",
    (user_id,),
)

# Summary cards
total = len(rows)
passed = sum(1 for r in rows if r["result"] == "pass")
failed = sum(1 for r in rows if r["result"] == "fail")
pending = total - passed - failed

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total certifications", total)
c2.metric("✅ Passed", passed)
c3.metric("🟥 Failed", failed)
c4.metric("⏳ Pending", pending)

st.markdown("---")

# Table
def _status_chip(result):
    if result == "pass":
        return f"<span style='background:{COLOR_PASS};color:white;padding:2px 10px;border-radius:10px;font-size:0.85rem'>Pass</span>"
    if result == "fail":
        return f"<span style='background:{COLOR_FAIL};color:white;padding:2px 10px;border-radius:10px;font-size:0.85rem'>Fail</span>"
    return f"<span style='background:{COLOR_PENDING};color:white;padding:2px 10px;border-radius:10px;font-size:0.85rem'>Pending</span>"


display_rows = []
for r in rows:
    display_rows.append({
        "Certification": r["name"],
        "Category": r["category"] or "",
        "Target week": r["target_week"] or "",
        "Status": _status_chip(r["result"]),
        "Score": f"{r['score']:.0f}" if r["score"] is not None else "—",
        "Attempts": r["attempt_number"] or 0,
        "Last attempt": r["attempt_date"] or "—",
    })

df = pd.DataFrame(display_rows)
st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.caption(
    "Score column is shown when the cert source provides one. "
    "The current BD tracker only records pass/fail, so score may be blank."
)
