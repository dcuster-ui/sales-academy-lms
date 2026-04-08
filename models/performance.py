"""Performance metrics model queries."""

from db.database import query, execute


def get_metrics_for_user(user_id, cohort_id=None):
    sql = "SELECT * FROM performance_metrics WHERE user_id = ?"
    params = [user_id]
    if cohort_id:
        sql += " AND cohort_id = ?"
        params.append(cohort_id)
    sql += " ORDER BY report_week"
    return query(sql, params)


def get_rep_weekly_metrics(user_id, cohort_id):
    """Get a single rep's weekly metrics with week numbers (for rep self-view)."""
    return query(
        """SELECT pm.*, u.full_name as rep_name,
                  ce.hire_date,
                  CAST((julianday(pm.report_week) - julianday(ce.hire_date)) / 7 + 1 AS INTEGER) as week_num
           FROM performance_metrics pm
           JOIN users u ON pm.user_id = u.id
           JOIN cohort_enrollments ce ON ce.user_id = pm.user_id AND ce.cohort_id = pm.cohort_id
           WHERE pm.user_id = ? AND pm.cohort_id = ?
           ORDER BY pm.report_week""",
        (user_id, cohort_id),
    )


def get_rep_metric_summary(user_id, cohort_id):
    """Get aggregated metrics for a single rep."""
    return query(
        """SELECT
               SUM(dials) as total_dials,
               SUM(solid_calls) as total_solid_calls,
               SUM(connected) as total_connected,
               SUM(dm_connect) as total_dm_connect,
               SUM(appointments_set) as total_appointments,
               SUM(needs_assessment) as total_needs_assessment,
               SUM(presentations) as total_presentations,
               SUM(close_won) as total_deals,
               SUM(um_closed) as total_um_closed,
               SUM(um_launched) as total_um_launched,
               SUM(gp_amount) as total_gp,
               SUM(revenue) as total_revenue
           FROM performance_metrics
           WHERE user_id = ? AND cohort_id = ?""",
        (user_id, cohort_id),
        one=True,
    )


def get_metrics_for_cohort(cohort_id):
    return query(
        """SELECT pm.*, u.full_name as rep_name
           FROM performance_metrics pm
           JOIN users u ON pm.user_id = u.id
           WHERE pm.cohort_id = ?
           ORDER BY pm.report_week, u.full_name""",
        (cohort_id,),
    )


def get_weekly_metrics_by_rep(cohort_id):
    """Get week-over-week metrics grouped by rep, with week number."""
    return query(
        """SELECT pm.*, u.full_name as rep_name,
                  ce.hire_date,
                  CAST((julianday(pm.report_week) - julianday(ce.hire_date)) / 7 + 1 AS INTEGER) as week_num
           FROM performance_metrics pm
           JOIN users u ON pm.user_id = u.id
           JOIN cohort_enrollments ce ON ce.user_id = pm.user_id AND ce.cohort_id = pm.cohort_id
           WHERE pm.cohort_id = ?
           ORDER BY pm.report_week, u.full_name""",
        (cohort_id,),
    )


def get_cohort_metric_summary(cohort_id):
    """Get aggregated metrics for a cohort."""
    return query(
        """SELECT
               COUNT(DISTINCT user_id) as reps_with_data,
               SUM(dials) as total_dials,
               SUM(solid_calls) as total_solid_calls,
               SUM(connected) as total_connected,
               SUM(dm_connect) as total_dm_connect,
               SUM(appointments_set) as total_appointments,
               SUM(needs_assessment) as total_needs_assessment,
               SUM(presentations) as total_presentations,
               SUM(close_won) as total_deals,
               SUM(um_closed) as total_um_closed,
               SUM(um_launched) as total_um_launched,
               SUM(gp_amount) as total_gp,
               SUM(revenue) as total_revenue
           FROM performance_metrics
           WHERE cohort_id = ?""",
        (cohort_id,),
        one=True,
    )


def get_rep_weekly_totals(cohort_id):
    """Get per-rep totals across all weeks for comparison."""
    return query(
        """SELECT u.full_name as rep_name,
                  SUM(pm.dials) as total_dials,
                  SUM(pm.solid_calls) as total_solid_calls,
                  SUM(pm.connected) as total_connected,
                  SUM(pm.dm_connect) as total_dm_connect,
                  SUM(pm.appointments_set) as total_appointments,
                  SUM(pm.needs_assessment) as total_needs_assessment,
                  SUM(pm.presentations) as total_presentations,
                  SUM(pm.close_won) as total_deals,
                  SUM(pm.gp_amount) as total_gp
           FROM performance_metrics pm
           JOIN users u ON pm.user_id = u.id
           WHERE pm.cohort_id = ?
           GROUP BY u.full_name
           ORDER BY SUM(pm.dials) DESC""",
        (cohort_id,),
    )


def upsert_metric(user_id, cohort_id, report_week, dials=0, solid_calls=0,
                   connected=0, dm_connect=0, appointments_set=0,
                   needs_assessment=0, presentations=0, close_won=0,
                   um_closed=0, um_launched=0, gp_amount=0,
                   pipeline_value=0, revenue=0, notes=None, entered_by=None):
    return execute(
        """INSERT INTO performance_metrics
           (user_id, cohort_id, report_week, dials, solid_calls, connected,
            dm_connect, appointments_set, needs_assessment, presentations,
            close_won, um_closed, um_launched, gp_amount,
            pipeline_value, revenue, notes, entered_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id, report_week) DO UPDATE SET
            dials=excluded.dials, solid_calls=excluded.solid_calls,
            connected=excluded.connected, dm_connect=excluded.dm_connect,
            appointments_set=excluded.appointments_set,
            needs_assessment=excluded.needs_assessment,
            presentations=excluded.presentations, close_won=excluded.close_won,
            um_closed=excluded.um_closed, um_launched=excluded.um_launched,
            gp_amount=excluded.gp_amount, pipeline_value=excluded.pipeline_value,
            revenue=excluded.revenue, notes=excluded.notes, entered_by=excluded.entered_by""",
        (user_id, cohort_id, report_week, dials, solid_calls, connected,
         dm_connect, appointments_set, needs_assessment, presentations,
         close_won, um_closed, um_launched, gp_amount,
         pipeline_value, revenue, notes, entered_by),
    )
