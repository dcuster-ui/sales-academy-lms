"""Training Schedule — Weekly calendar view of the 6-week program."""

import streamlit as st
from auth.auth import require_auth, get_current_role
from components.sidebar import render_sidebar
from utils.constants import ACTIVITY_COLORS

st.set_page_config(page_title="Training Schedule | Sales Academy", page_icon="📋", layout="wide")

require_auth()
render_sidebar()

st.markdown("### Training Schedule")
st.caption("6-week Sales Academy new hire training program")

# Static schedule data based on the training agenda spreadsheet
# Assumption: Using the schedule as-is from the Google Sheet since it's the master template
SCHEDULE = {
    "Week 1": {
        "Monday (Day 1)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Welcome New Hires", "classroom"),
            ("9:45 - 10:45", "HR & Facilities Orientation", "classroom"),
            ("10:45 - 11:15", "IT Setup", "other"),
            ("11:15 - 11:45", "Sales Psychology", "classroom"),
            ("11:45 - 12:15", "Organizing for Success", "classroom"),
            ("12:15 - 12:45", "Lunch", "lunch"),
            ("1:45 - 2:30", "Welcome to Groupon", "classroom"),
            ("2:30 - 3:00", "Groupon Platform", "classroom"),
            ("3:00 - 3:30", "Why Groupon Works", "classroom"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Groupon Certification", "certification"),
            ("4:30 - 5:00", "Industry Education: HBW", "classroom"),
            ("5:00 - 5:30", "Industry Education HBW Certification", "certification"),
        ],
        "Tuesday (Day 2)": [
            ("7:00 - 7:15", "Leadership Floor Presence", "huddle"),
            ("7:15 - 7:45", "Morning Huddle", "huddle"),
            ("7:45 - 8:15", "Sales Process Overview", "classroom"),
            ("8:15 - 8:45", "Sales Process & Psychology Activity", "classroom"),
            ("8:45 - 9:15", "Front End Training", "classroom"),
            ("9:15 - 9:45", "10 Minute Break", "break"),
            ("9:45 - 10:15", "Front End Certification", "certification"),
            ("10:15 - 10:45", "Front End Roleplay", "roleplay"),
            ("10:45 - 11:15", "HR Tasks", "other"),
            ("11:15 - 11:45", "Lunch", "lunch"),
            ("11:45 - 12:00", "TUIT & Needs Assessment Training", "classroom"),
            ("12:30 - 1:00", "Front End Objection Handling", "classroom"),
            ("1:00 - 1:30", "Front End Objection Handling Certification", "certification"),
            ("1:30 - 2:00", "Front End Objection Handling Roleplay", "roleplay"),
            ("2:00 - 2:30", "10 Minute Break", "break"),
            ("2:30 - 3:00", "TUIT & Needs Assessment Certification", "certification"),
            ("3:00 - 3:30", "TUIT & Needs Assessment Roleplay", "roleplay"),
        ],
        "Wednesday (Day 3)": [
            ("7:00 - 7:15", "Leadership Floor Presence", "huddle"),
            ("7:15 - 7:45", "Morning Huddle", "huddle"),
            ("7:45 - 8:15", "TUIT & NA Objection Handling", "classroom"),
            ("8:15 - 8:45", "Salesforce Overview", "classroom"),
            ("8:45 - 9:15", "Appointment Setting Training", "classroom"),
            ("9:15 - 9:45", "10 Minute Break", "break"),
            ("9:45 - 10:15", "Appointment Setting Certification", "certification"),
            ("10:15 - 10:45", "Appointment Setting Roleplay", "roleplay"),
            ("10:45 - 11:15", "Gatekeeper Training", "classroom"),
            ("11:15 - 11:45", "Gatekeeper Certification", "certification"),
            ("11:45 - 12:15", "Gatekeeper Roleplay", "roleplay"),
            ("12:15 - 1:00", "Lunch", "lunch"),
            ("1:45 - 2:30", "Salesloft Cadence Training", "classroom"),
            ("2:30 - 3:00", "Merchant Quality Training", "classroom"),
            ("3:00 - 3:30", "10 Minute Break", "break"),
            ("3:30 - 4:00", "Front End Roleplay", "roleplay"),
            ("4:00 - 4:30", "Pre-Call Prep Training", "classroom"),
            ("4:30 - 5:00", "Pre-Call Prep", "other"),
        ],
        "Thursday (Day 4)": [
            ("7:00 - 7:15", "Leadership Floor Presence", "huddle"),
            ("7:15 - 7:45", "Morning Huddle", "huddle"),
            ("7:45 - 8:15", "TUIT & NA OH Certification", "certification"),
            ("8:15 - 8:45", "Front End & Gatekeeper Roleplay", "roleplay"),
            ("8:45 - 9:15", "AM Call Block", "call_block"),
            ("9:15 - 9:45", "Call Block Review", "call_block"),
            ("9:45 - 10:15", "10 Minute Break", "break"),
            ("10:15 - 10:45", "AM Call Block", "call_block"),
            ("10:45 - 11:15", "Promotional Program Training", "classroom"),
            ("11:15 - 11:45", "Lunch", "lunch"),
            ("1:45 - 2:30", "Salesforce Dialer Training", "classroom"),
            ("2:30 - 3:00", "Deal Structure Training", "classroom"),
            ("3:00 - 3:30", "AIDG Training", "classroom"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Presentation Training", "classroom"),
            ("4:30 - 5:00", "Presentation Certification", "certification"),
            ("5:00 - 5:30", "Presentation Roleplay", "roleplay"),
        ],
        "Friday (Day 5)": [
            ("7:00 - 7:15", "Leadership Floor Presence", "huddle"),
            ("7:15 - 7:45", "Morning Huddle", "huddle"),
            ("7:45 - 8:15", "Presentation Objection Handling", "classroom"),
            ("8:15 - 8:45", "Presentation OH Certification", "certification"),
            ("8:45 - 9:15", "Presentation OH Roleplay", "roleplay"),
            ("9:15 - 9:45", "Merchant Center Training", "classroom"),
            ("9:45 - 10:15", "10 Minute Break", "break"),
            ("10:15 - 10:45", "Pre-Call Prep", "other"),
            ("10:45 - 11:15", "PM Call Block", "call_block"),
            ("11:15 - 11:45", "Lunch", "lunch"),
            ("1:45 - 2:30", "SalesloftCX Training", "classroom"),
            ("2:30 - 3:00", "SalesloftCX Call Review", "call_block"),
            ("3:00 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 5:00", "PM Call Block", "call_block"),
        ],
    },
    "Week 2": {
        "Monday (Day 6)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 10:15", "Groupon Value and Benefits", "classroom"),
            ("10:15 - 10:45", "Pre-Call Prep", "other"),
            ("10:45 - 11:15", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("11:15 - 11:45", "Roleplay", "roleplay"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Massage Deep Dive Deck / Video", "video"),
            ("4:30 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
        "Tuesday (Day 7)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 10:15", "Lead Generation and House Hunting", "classroom"),
            ("10:15 - 10:45", "Pre-Call Prep", "other"),
            ("10:45 - 11:15", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("11:15 - 11:45", "Roleplay", "roleplay"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Scalp Care Deep Dive (Head Spa)", "video"),
            ("4:30 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
        "Wednesday (Day 8)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 10:15", "Call Shadowing (Flex)", "shadowing"),
            ("10:15 - 10:45", "Pre-Call Prep", "other"),
            ("10:45 - 11:15", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("11:15 - 11:45", "Roleplay", "roleplay"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Injectables Deep Dive", "video"),
            ("4:30 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
        "Thursday (Day 9)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 10:15", "30 Second Commercial Activity", "classroom"),
            ("10:15 - 10:45", "Pre-Call Prep", "other"),
            ("10:45 - 11:15", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("11:15 - 11:45", "Roleplay", "roleplay"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 4:30", "Nails Deep Dive Deck / Video", "video"),
            ("4:30 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
        "Friday (Day 10)": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 11:45", "AM Call Block", "call_block"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Reps Review Their Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
    },
    "Weeks 3-6": {
        "Daily Structure": [
            ("9:00 - 9:15", "Leadership Floor Presence", "huddle"),
            ("9:15 - 9:45", "Morning Huddle", "huddle"),
            ("9:45 - 10:15", "Pre-Call Prep", "other"),
            ("10:15 - 11:15", "AM Call Block", "call_block"),
            ("11:15 - 11:45", "SalesloftCX - Review Calls", "call_block"),
            ("11:45 - 12:15", "10 Minute Break", "break"),
            ("12:15 - 1:00", "AM Call Block", "call_block"),
            ("1:00 - 1:45", "Lunch", "lunch"),
            ("1:45 - 2:00", "PM Huddle", "huddle"),
            ("2:00 - 2:30", "SalesloftCX - Review Calls", "call_block"),
            ("2:30 - 3:30", "PM Call Block", "call_block"),
            ("3:30 - 4:00", "10 Minute Break", "break"),
            ("4:00 - 5:00", "PM Call Block", "call_block"),
            ("5:00 - 5:30", "EOD Tasks", "other"),
        ],
        "Weekly Additions": [
            ("Varies", "Post Close Training (Week 3)", "classroom"),
            ("Varies", "Deal Structure Deep Dive (Week 3)", "classroom"),
            ("Varies", "Payment Terms Training (Week 4)", "classroom"),
            ("Varies", "Lead Sourcing & Creation (Week 4)", "classroom"),
            ("Varies", "3PIP Overview (Week 5)", "classroom"),
            ("Varies", "Advanced Roleplay Sessions (Weeks 3-6)", "roleplay"),
        ],
    },
}

# Render schedule
week_tabs = st.tabs(list(SCHEDULE.keys()))

for tab, (week_name, days) in zip(week_tabs, SCHEDULE.items()):
    with tab:
        if week_name in ("Week 1", "Week 2"):
            day_names = list(days.keys())
            day_cols = st.columns(len(day_names))
            for col, day_name in zip(day_cols, day_names):
                with col:
                    st.markdown(f"**{day_name}**")
                    for time_slot, activity, activity_type in days[day_name]:
                        color = ACTIVITY_COLORS.get(activity_type, "#95A5A6")
                        st.markdown(
                            f'<div style="background:{color}15; border-left:3px solid {color}; '
                            f'padding:4px 8px; margin:2px 0; border-radius:0 4px 4px 0; font-size:0.75rem;">'
                            f'<div style="color:#666; font-size:0.65rem;">{time_slot}</div>'
                            f'<div style="font-weight:500;">{activity}</div></div>',
                            unsafe_allow_html=True,
                        )
        else:
            # Weeks 3-6: Simplified view
            for section_name, items in days.items():
                st.markdown(f"**{section_name}**")
                for time_slot, activity, activity_type in items:
                    color = ACTIVITY_COLORS.get(activity_type, "#95A5A6")
                    st.markdown(
                        f'<div style="background:{color}15; border-left:3px solid {color}; '
                        f'padding:4px 8px; margin:2px 0; border-radius:0 4px 4px 0; font-size:0.85rem;">'
                        f'<div style="color:#666; font-size:0.75rem;">{time_slot}</div>'
                        f'<div style="font-weight:500;">{activity}</div></div>',
                        unsafe_allow_html=True,
                    )

# Legend
st.markdown("---")
st.markdown("**Legend:**")
legend_cols = st.columns(7)
legend_items = [
    ("Classroom", "classroom"), ("Call Block", "call_block"), ("Certification", "certification"),
    ("Roleplay", "roleplay"), ("Huddle", "huddle"), ("Video/Shadowing", "video"), ("Break/Other", "break"),
]
for col, (label, atype) in zip(legend_cols, legend_items):
    color = ACTIVITY_COLORS.get(atype, "#95A5A6")
    with col:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<div style="width:12px;height:12px;background:{color};border-radius:2px;"></div>'
            f'<span style="font-size:0.8rem;">{label}</span></div>',
            unsafe_allow_html=True,
        )
