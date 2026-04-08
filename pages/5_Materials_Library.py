"""Materials Library — Browse and track training materials."""

import streamlit as st
from collections import defaultdict
from auth.auth import require_auth, get_current_user_id, get_current_role, is_admin, is_rep
from components.sidebar import render_sidebar
from models.materials import (
    get_categories, get_materials_with_progress, mark_material_complete,
    mark_material_incomplete, get_material_progress_count, get_total_materials,
)
from models.cohorts import get_all_cohorts, get_cohort_reps
from db.database import execute, query

st.set_page_config(page_title="Materials Library | Sales Academy", page_icon="📋", layout="wide")

require_auth()
render_sidebar()

user_id = get_current_user_id()
role = get_current_role()

st.markdown("### Materials Library")
st.caption("Training decks, video modules, and supporting resources.")

# ── Admin: rep selector to manage completion on behalf of reps ────────────
view_user_id = user_id  # default: viewing own progress
view_user_name = None

if is_admin():
    st.markdown("---")
    mode = st.radio(
        "View as",
        options=["Admin (browse only)", "Manage rep completion"],
        horizontal=True,
        key="mat_view_mode",
    )
    if mode == "Manage rep completion":
        cohorts = get_all_cohorts()
        if cohorts:
            sel_cohort = st.selectbox("Cohort", options=cohorts, format_func=lambda c: c["name"], key="mat_cohort")
            reps = get_cohort_reps(sel_cohort["id"])
            if reps:
                sel_rep = st.selectbox("Rep", options=reps, format_func=lambda r: r["full_name"], key="mat_rep")
                view_user_id = sel_rep["id"]
                view_user_name = sel_rep["full_name"]
                st.info(f"Managing materials for **{view_user_name}**")
            else:
                st.warning("No reps in this cohort.")
    st.markdown("---")

# Progress summary
if role == "rep" or view_user_name:
    done = get_material_progress_count(view_user_id)
    total = get_total_materials()
    label = f"{view_user_name}: " if view_user_name else ""
    st.progress(done / max(total, 1), text=f"{label}{done}/{total} materials completed")

# View toggle and filters
col_view, col_search, col_type = st.columns([1, 2, 1])
with col_view:
    view_by = st.radio("View by", options=["Schedule Day", "Category"], horizontal=True, key="mat_view_by")
with col_search:
    search = st.text_input("Search materials", placeholder="Type to filter...")
with col_type:
    type_filter = st.multiselect("Material type", options=["deck", "video", "document", "link", "other"], default=[])

# Get materials with progress for the selected user
materials = get_materials_with_progress(view_user_id)

# Apply filters
if search:
    materials = [m for m in materials if search.lower() in m["title"].lower() or search.lower() in m["category_name"].lower()]
if type_filter:
    materials = [m for m in materials if m["material_type"] in type_filter]

# Determine if the current view allows completion toggling
can_toggle = role in ("rep", "manager") or (is_admin() and view_user_name is not None)

# Day labels for schedule view
DAY_LABELS = {
    1: "Day 1 — Welcome & Orientation",
    2: "Day 2 — Sales Process, Front End & TUIT",
    3: "Day 3 — Objection Handling, Gatekeepers & Appointment Setting",
    4: "Day 4 — Promotional Programs, AIDG & Presentation",
    5: "Day 5 — Presentation OH, Merchant Center & SalesloftCX",
    6: "Day 6 — Conversation Cards & Value Props",
    7: "Day 7 — Lead Gen & Tools",
    8: "Day 8 — Call Shadowing & Tools",
    9: "Day 9 — 30-Second Commercial & Deep Dives",
    10: "Day 10 — Full Call Block Day",
    11: "Week 3 — Post Close Process",
    12: "Week 3 — Deal Stage & Pipeline",
    16: "Week 4 — Payment Terms",
    17: "Week 4 — Lead Sourcing",
    18: "Week 4 — Information Requests & Cases",
    21: "Week 5 — 3PIP Overview",
}


def render_material(m):
    """Render a single material row with open/toggle/edit controls."""
    icon = {"deck": "📊", "video": "🎬", "document": "📄", "link": "🔗", "other": "📁"}.get(m["material_type"], "📁")

    if is_admin():
        c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
    else:
        c1, c2, c3 = st.columns([4, 1, 1])

    with c1:
        st.markdown(f"{icon} **{m['title']}**")
        if m.get("description"):
            st.caption(m["description"])
        type_label = m["material_type"].title()
        cat_label = f" | {m['category_name']}" if view_by == "Schedule Day" else ""
        link_status = "" if m.get("url") else " | **No link**"
        st.caption(f"{type_label}{cat_label}{link_status}")

    with c2:
        if m.get("url"):
            st.link_button("Open", m["url"], use_container_width=True)
        elif not is_admin():
            st.caption("No link yet")

    with c3:
        if can_toggle:
            is_done = m["progress_status"] == "completed"
            if st.checkbox(
                "Done" if is_done else "Mark done",
                value=is_done,
                key=f"mat_{m['id']}_{view_user_id}",
            ):
                if not is_done:
                    mark_material_complete(view_user_id, m["id"])
                    st.rerun()
            else:
                if is_done:
                    mark_material_incomplete(view_user_id, m["id"])
                    st.rerun()

    # Admin: inline edit link
    if is_admin():
        with c4:
            if st.button("Edit", key=f"edit_{m['id']}", use_container_width=True):
                st.session_state[f"editing_mat_{m['id']}"] = True

        if st.session_state.get(f"editing_mat_{m['id']}"):
            with st.form(f"edit_form_{m['id']}"):
                new_url = st.text_input("URL (Google Drive / YouTube link)", value=m.get("url") or "", key=f"url_{m['id']}")
                new_desc = st.text_input("Description", value=m.get("description") or "", key=f"desc_{m['id']}")
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    if st.form_submit_button("Save", type="primary"):
                        execute(
                            "UPDATE materials SET url = ?, description = ? WHERE id = ?",
                            (new_url or None, new_desc or None, m["id"]),
                        )
                        st.session_state.pop(f"editing_mat_{m['id']}", None)
                        st.rerun()
                with ecol2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.pop(f"editing_mat_{m['id']}", None)
                        st.rerun()


if not materials:
    st.info("No materials match your filters.")
elif view_by == "Schedule Day":
    # Group by schedule_day
    by_day = defaultdict(list)
    for m in materials:
        day = m.get("schedule_day") or 0
        by_day[day].append(m)

    for day_num in sorted(by_day.keys()):
        items = by_day[day_num]
        completed = sum(1 for m in items if m["progress_status"] == "completed")
        label = DAY_LABELS.get(day_num, f"Day {day_num}")

        with st.expander(f"**{label}** — {completed}/{len(items)} completed", expanded=(day_num <= 2)):
            for m in items:
                render_material(m)
else:
    # Group by category (original view)
    by_category = defaultdict(list)
    for m in materials:
        by_category[m["category_name"]].append(m)

    for cat_name in sorted(by_category.keys(), key=lambda x: by_category[x][0]["cat_order"]):
        items = by_category[cat_name]
        completed = sum(1 for m in items if m["progress_status"] == "completed")

        with st.expander(f"**{cat_name}** — {completed}/{len(items)} completed", expanded=False):
            for m in items:
                render_material(m)

# Admin: Add Material
if is_admin():
    st.markdown("---")
    st.markdown("#### Add New Material")
    categories = get_categories()

    with st.form("add_material"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title")
            category = st.selectbox("Category", options=categories, format_func=lambda c: c["name"])
            mat_type = st.selectbox("Type", options=["deck", "video", "document", "link", "other"])
        with col2:
            url = st.text_input("URL (Google Drive link)")
            description = st.text_input("Description (optional)")
            week_avail = st.number_input("Week available", min_value=1, max_value=6, value=1)

        if st.form_submit_button("Add Material"):
            if title and category:
                execute(
                    """INSERT INTO materials (category_id, title, material_type, url, description, week_available, is_required)
                       VALUES (?, ?, ?, ?, ?, ?, 1)""",
                    (category["id"], title, mat_type, url or None, description or None, week_avail),
                )
                st.success(f"Added: {title}")
                st.rerun()
            else:
                st.error("Title and category are required.")
