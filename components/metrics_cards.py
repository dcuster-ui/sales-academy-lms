"""Reusable metric card components."""

import streamlit as st


def metric_row(metrics):
    """Render a row of metric cards. metrics is a list of (label, value, delta) tuples."""
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            if delta is not None:
                st.metric(label=label, value=value, delta=delta)
            else:
                st.metric(label=label, value=value)


def status_badge(status, text=None):
    """Return HTML for a colored status badge."""
    colors = {
        "pass": ("#28a745", "#fff"),
        "fail": ("#dc3545", "#fff"),
        "not_attempted": ("#6c757d", "#fff"),
        "active": ("#53A318", "#fff"),
        "completed": ("#17a2b8", "#fff"),
        "dropped": ("#dc3545", "#fff"),
        "on_hold": ("#ffc107", "#333"),
    }
    bg, fg = colors.get(status, ("#6c757d", "#fff"))
    display = text or status.replace("_", " ").title()
    return f'<span style="background:{bg}; color:{fg}; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:500;">{display}</span>'


def cert_status_badges(cert_statuses):
    """Render a row of certification status badges."""
    html_parts = []
    for cs in cert_statuses:
        if cs["status"] == "pass":
            color = "#28a745"
            icon = "&#10003;"
        elif cs["status"] == "fail":
            color = "#dc3545"
            icon = "&#10007;"
        else:
            color = "#ccc"
            icon = "&#8212;"
        html_parts.append(
            f'<div style="display:inline-block; text-align:center; margin:0 4px;">'
            f'<div style="width:32px; height:32px; border-radius:50%; background:{color}; '
            f'color:#fff; line-height:32px; font-size:16px; margin:0 auto;">{icon}</div>'
            f'<div style="font-size:0.65rem; color:#666; max-width:60px; overflow:hidden; '
            f'text-overflow:ellipsis; white-space:nowrap;">{cs["cert_name"].split(":")[0]}</div></div>'
        )
    st.markdown(
        f'<div style="display:flex; flex-wrap:wrap; gap:4px; padding:8px 0;">{"".join(html_parts)}</div>',
        unsafe_allow_html=True,
    )
