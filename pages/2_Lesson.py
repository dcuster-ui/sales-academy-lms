"""Lesson viewer — render lesson content and let the rep mark it complete."""

import streamlit as st
from auth.auth import require_auth, get_current_user_id
from components.sidebar import render_sidebar
from models.modules import (
    get_module,
    get_lesson,
    list_lessons,
    get_lesson_progress,
    mark_lesson,
    get_lesson_css,
)

st.set_page_config(page_title="Lesson · Sales Academy", page_icon="📖", layout="wide")
require_auth()
render_sidebar()

user_id = get_current_user_id()

# Resolve which lesson to show: explicit lesson takes precedence, then module's first lesson
lesson_id = st.session_state.get("active_lesson_id")
module_id = st.session_state.get("active_module_id")

if not lesson_id and module_id:
    lessons = list_lessons(module_id)
    if lessons:
        lesson_id = lessons[0]["id"]
        st.session_state["active_lesson_id"] = lesson_id

if not lesson_id:
    st.info("Pick a module from **My Path** to start a lesson.")
    if st.button("← Back to My Path"):
        st.switch_page("pages/1_My_Path.py")
    st.stop()

lesson = get_lesson(lesson_id)
if not lesson:
    st.error("Lesson not found.")
    st.stop()

module = get_module(lesson["module_id"])
lessons_in_module = list_lessons(module["id"])
idx = next((i for i, l in enumerate(lessons_in_module) if l["id"] == lesson_id), 0)

# --- Header / breadcrumb ---
top = st.columns([6, 2])
with top[0]:
    st.markdown(f"<span style='color:#888'>{module['title']}</span>", unsafe_allow_html=True)
    st.markdown(f"### {lesson['title']}")
with top[1]:
    st.caption(f"Lesson {idx + 1} of {len(lessons_in_module)}")
    if lesson.get("est_minutes"):
        st.caption(f"⏱️ ~{lesson['est_minutes']} min")

st.markdown("---")

# --- Content ---
ctype = lesson["content_type"]
if ctype == "html" and lesson.get("content_body"):
    css = get_lesson_css()
    wrapped = (
        f"<style>{css}</style>"
        "<div class='res-card' style='background:var(--card);padding:18px;border:1px solid var(--line);border-radius:14px;'>"
        f"{lesson['content_body']}"
        "</div>"
    )
    st.components.v1.html(wrapped, height=900, scrolling=True)
elif ctype == "video" and lesson.get("url"):
    st.video(lesson["url"])
elif ctype in ("link", "doc") and lesson.get("url"):
    st.markdown(f"📎 Open this resource in a new tab to work through it:")
    st.link_button(f"Open: {lesson['title']}", lesson["url"], use_container_width=False)
    st.caption(lesson["url"])
else:
    st.warning("This lesson has no content attached yet.")

st.markdown("---")

# --- Mark complete + navigation ---
prog = get_lesson_progress(user_id, lesson_id)
status = prog["status"] if prog else "not_started"

cols = st.columns([2, 2, 2, 2])
with cols[0]:
    if st.button("← Previous", disabled=(idx == 0), use_container_width=True):
        st.session_state["active_lesson_id"] = lessons_in_module[idx - 1]["id"]
        st.rerun()
with cols[1]:
    if status == "completed":
        st.success("✅ Completed")
    else:
        if st.button("Mark complete", type="primary", use_container_width=True):
            mark_lesson(user_id, lesson_id, "completed")
            st.rerun()
with cols[2]:
    if status == "completed" and st.button("Reset to in-progress", use_container_width=True):
        mark_lesson(user_id, lesson_id, "in_progress")
        st.rerun()
with cols[3]:
    if st.button("Next →", disabled=(idx == len(lessons_in_module) - 1), type="primary", use_container_width=True):
        st.session_state["active_lesson_id"] = lessons_in_module[idx + 1]["id"]
        st.rerun()

# Bottom nav back to path
st.markdown("")
if st.button("← Back to My Path"):
    st.switch_page("pages/1_My_Path.py")
