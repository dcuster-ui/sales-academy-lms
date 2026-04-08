"""Certification model queries — the core of the LMS tracking."""

from db.database import query, execute


def get_all_certifications():
    return query("SELECT * FROM certifications WHERE is_active = 1 ORDER BY display_order")


def get_cert_status_for_user(user_id, cohort_id=None):
    """Get pass/fail status for each certification for a user.
    Returns list of dicts with cert info + latest attempt result.
    """
    certs = get_all_certifications()
    results = []
    for cert in certs:
        params = [user_id, cert["id"]]
        cohort_filter = ""
        if cohort_id:
            cohort_filter = " AND cohort_id = ?"
            params.append(cohort_id)

        # Check if any attempt passed
        passed = query(
            f"""SELECT * FROM certification_attempts
                WHERE user_id = ? AND certification_id = ?{cohort_filter} AND result = 'pass'
                ORDER BY attempt_date DESC LIMIT 1""",
            params,
            one=True,
        )

        # Get total attempts
        attempt_count = query(
            f"""SELECT COUNT(*) as cnt FROM certification_attempts
                WHERE user_id = ? AND certification_id = ?{cohort_filter}""",
            params[:3] if cohort_id else params[:2],
            one=True,
        )

        # Get latest attempt
        latest = query(
            f"""SELECT * FROM certification_attempts
                WHERE user_id = ? AND certification_id = ?{cohort_filter}
                ORDER BY attempt_number DESC LIMIT 1""",
            params,
            one=True,
        )

        results.append({
            "cert_id": cert["id"],
            "cert_name": cert["name"],
            "category": cert["category"],
            "target_week": cert["target_week"],
            "display_order": cert["display_order"],
            "status": "pass" if passed else ("fail" if latest else "not_attempted"),
            "attempts": attempt_count["cnt"] if attempt_count else 0,
            "passed_date": passed["attempt_date"] if passed else None,
            "latest_attempt": latest,
        })
    return results


def get_certs_passed_count(user_id, cohort_id=None):
    """Count how many certifications a user has passed."""
    statuses = get_cert_status_for_user(user_id, cohort_id)
    return sum(1 for s in statuses if s["status"] == "pass")


def get_cohort_cert_heatmap(cohort_id):
    """Get certification heatmap data for an entire cohort.
    Returns dict: {user_id: {cert_id: 'pass'|'fail'|'not_attempted'}}
    """
    from models.cohorts import get_cohort_reps
    reps = get_cohort_reps(cohort_id)
    certs = get_all_certifications()

    heatmap = {}
    for rep in reps:
        statuses = get_cert_status_for_user(rep["id"], cohort_id)
        heatmap[rep["id"]] = {
            "name": rep["full_name"],
            "certs": {s["cert_name"]: s["status"] for s in statuses},
            "passed_count": sum(1 for s in statuses if s["status"] == "pass"),
            "total": len(certs),
        }
    return heatmap


def record_attempt(user_id, certification_id, cohort_id, result, score=None, evaluated_by=None, notes=None):
    """Record a new certification attempt."""
    # Get next attempt number
    row = query(
        """SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_num
           FROM certification_attempts
           WHERE user_id = ? AND certification_id = ? AND cohort_id = ?""",
        (user_id, certification_id, cohort_id),
        one=True,
    )
    attempt_num = row["next_num"]

    return execute(
        """INSERT INTO certification_attempts
           (user_id, certification_id, cohort_id, attempt_number, result, score, evaluated_by, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, certification_id, cohort_id, attempt_num, result, score, evaluated_by, notes),
    )


def get_cert_attempts_history(cohort_id=None, user_id=None, certification_id=None, limit=50):
    """Get certification attempt history with filters."""
    sql = """SELECT ca.*, u.full_name as rep_name, c.name as cert_name,
                    ev.full_name as evaluator_name
             FROM certification_attempts ca
             JOIN users u ON ca.user_id = u.id
             JOIN certifications c ON ca.certification_id = c.id
             LEFT JOIN users ev ON ca.evaluated_by = ev.id
             WHERE 1=1"""
    params = []
    if cohort_id:
        sql += " AND ca.cohort_id = ?"
        params.append(cohort_id)
    if user_id:
        sql += " AND ca.user_id = ?"
        params.append(user_id)
    if certification_id:
        sql += " AND ca.certification_id = ?"
        params.append(certification_id)
    sql += " ORDER BY ca.attempt_date DESC, ca.created_at DESC LIMIT ?"
    params.append(limit)
    return query(sql, params)


def get_cohort_pass_rates(cohort_id):
    """Get pass rate for each certification in a cohort."""
    certs = get_all_certifications()
    from models.cohorts import get_cohort_reps
    reps = get_cohort_reps(cohort_id)
    total_reps = len(reps)
    if total_reps == 0:
        return []

    results = []
    for cert in certs:
        passed_count = 0
        for rep in reps:
            passed = query(
                """SELECT 1 FROM certification_attempts
                   WHERE user_id = ? AND certification_id = ? AND cohort_id = ? AND result = 'pass'
                   LIMIT 1""",
                (rep["id"], cert["id"], cohort_id),
                one=True,
            )
            if passed:
                passed_count += 1
        results.append({
            "cert_name": cert["name"],
            "passed": passed_count,
            "total": total_reps,
            "rate": round(passed_count / total_reps * 100, 1),
        })
    return results
