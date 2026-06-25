"""My Path — the rep's default landing. Module list with progress and a 'continue' CTA."""

import streamlit as st
from auth.auth import require_auth, get_current_user_id
from components.sidebar import render_sidebar
from models.modules import (
    VERTICAL_LABELS,
    list_verticals,
    module_progress_for_user,
    next_lesson_for_user,
    get_user_vertical,
    set_user_vertical,
)

st.set_page_config(page_title="My Path · Sales Academy", page_icon="📋", layout="wide")
require_auth()
render_sidebar()

user_id = get_current_user_id()
user_name = st.session_state.get("user_name", "")
verticals = list_verticals()

# --- Vertical picker ---
current_vertical = get_user_vertical(user_id)
if current_vertical not in verticals:
    current_vertical = None

top = st.columns([4, 2])
with top[0]:
    st.markdown(f"### Welcome back, {user_name.split(' ')[0] if user_name else 'there'} 👋")
with top[1]:
    if verticals:
        labels = [VERTICAL_LABELS.get(v, v) for v in verticals]
        default_idx = verticals.index(current_vertical) if current_vertical else 0
        chosen_label = st.selectbox("Your vertical", labels, index=default_idx, key="vertical_picker")
        chosen = verticals[labels.index(chosen_label)]
        if chosen != current_vertical:
            set_user_vertical(user_id, chosen)
            st.rerun()
        current_vertical = chosen

if not current_vertical:
    st.info("No onboarding content has been loaded yet.")
    st.stop()

# --- Continue-where-you-left-off ---
next_lesson = next_lesson_for_user(user_id, vertical=current_vertical)
if next_lesson:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown("**Continue where you left off**")
            st.markdown(f"**{next_lesson['module_title']}** → {next_lesson['lesson_title']}")
        with c2:
            if st.button("Start", type="primary", use_container_width=True):
                st.session_state["active_lesson_id"] = next_lesson["lesson_id"]
                st.switch_page("pages/2_Lesson.py")
else:
    st.success(f"🎉 You've completed every lesson in {VERTICAL_LABELS.get(current_vertical, current_vertical)}. Nice work.")

st.markdown("---")
st.markdown(f"### Your modules — {VERTICAL_LABELS.get(current_vertical, current_vertical)}")

rollup = module_progress_for_user(user_id, vertical=current_vertical)
if not rollup:
    st.info("No modules in this vertical yet.")
else:
    # Group modules by week so the long list stays scannable
    by_week: dict[int, list] = {}
    for m in rollup:
        by_week.setdefault(m["week_target"] or 0, []).append(m)

    for week in sorted(by_week.keys()):
        st.markdown(f"#### Week {week}" if week else "#### Other")
        for m in by_week[week]:
            with st.container(border=True):
                top = st.columns([5, 2, 1])
                with top[0]:
                    st.markdown(f"**{m['title']}**")
                with top[1]:
                    pct = m["pct"] or 0
                    st.progress(pct / 100, text=f"{m['completed']}/{m['total']} lessons · {pct}%")
                with top[2]:
                    label = "Review" if pct == 100 else ("Resume" if pct > 0 else "Open")
                    if st.button(label, key=f"open_{m['module_id']}", use_container_width=True):
                        st.session_state["active_module_id"] = m["module_id"]
                        st.session_state.pop("active_lesson_id", None)
                        st.switch_page("pages/2_Lesson.py")
