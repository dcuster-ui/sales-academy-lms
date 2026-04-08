"""Cohort and enrollment model queries."""

from db.database import query, execute


def get_all_cohorts(status=None):
    sql = "SELECT * FROM cohorts"
    params = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY start_date DESC"
    return query(sql, params)


def get_cohort(cohort_id):
    return query("SELECT * FROM cohorts WHERE id = ?", (cohort_id,), one=True)


def get_cohort_for_user(user_id):
    """Get the active cohort enrollment for a user."""
    return query(
        """SELECT c.*, ce.hire_date, ce.status as enrollment_status
           FROM cohorts c
           JOIN cohort_enrollments ce ON c.id = ce.cohort_id
           WHERE ce.user_id = ? AND ce.status = 'active'
           ORDER BY c.start_date DESC LIMIT 1""",
        (user_id,),
        one=True,
    )


def get_cohort_reps(cohort_id, include_inactive=False):
    """Get all reps enrolled in a cohort. Filters out inactive reps by default."""
    sql = """SELECT u.*, ce.hire_date, ce.status as enrollment_status
             FROM users u
             JOIN cohort_enrollments ce ON u.id = ce.user_id
             WHERE ce.cohort_id = ? AND ce.status = 'active'"""
    if not include_inactive:
        sql += " AND u.is_active = 1"
    sql += " ORDER BY u.full_name"
    return query(sql, (cohort_id,))


def get_cohort_stats(cohort_id):
    """Get summary stats for a cohort."""
    rep_count = query(
        """SELECT COUNT(*) as cnt FROM cohort_enrollments ce
           JOIN users u ON ce.user_id = u.id
           WHERE ce.cohort_id = ? AND ce.status = 'active' AND u.is_active = 1""",
        (cohort_id,),
        one=True,
    )
    return {"rep_count": rep_count["cnt"] if rep_count else 0}


def create_cohort(name, start_date, end_date, status="upcoming"):
    return execute(
        "INSERT INTO cohorts (name, start_date, end_date, status) VALUES (?, ?, ?, ?)",
        (name, start_date, end_date, status),
    )


def enroll_rep(cohort_id, user_id, hire_date):
    return execute(
        "INSERT OR IGNORE INTO cohort_enrollments (cohort_id, user_id, hire_date) VALUES (?, ?, ?)",
        (cohort_id, user_id, hire_date),
    )
