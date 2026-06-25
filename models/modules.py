"""Modules, lessons, and lesson progress."""

from db.database import query, execute, get_connection

VERTICAL_LABELS = {
    "hbw": "Health, Beauty & Wellness",
    "ttd": "Things To Do",
    "fd": "Food & Drink",
    "ha": "Home & Auto",
}


def list_verticals():
    rows = query("SELECT DISTINCT vertical FROM modules WHERE is_active = 1 AND vertical IS NOT NULL ORDER BY vertical")
    return [r["vertical"] for r in rows]


def list_modules(vertical=None):
    if vertical:
        return query(
            """SELECT id, slug, title, description, display_order, week_target, vertical, is_required
               FROM modules
               WHERE is_active = 1 AND vertical = ?
               ORDER BY display_order, id""",
            (vertical,),
        )
    return query(
        """SELECT id, slug, title, description, display_order, week_target, vertical, is_required
           FROM modules
           WHERE is_active = 1
           ORDER BY display_order, id"""
    )


def get_lesson_css():
    row = query("SELECT value FROM app_config WHERE key = 'lesson_css'", one=True)
    return row["value"] if row else ""


def get_user_vertical(user_id):
    row = query("SELECT vertical FROM user_preferences WHERE user_id = ?", (user_id,), one=True)
    return row["vertical"] if row else None


def set_user_vertical(user_id, vertical):
    conn = get_connection()
    conn.execute(
        """INSERT INTO user_preferences (user_id, vertical) VALUES (?, ?)
           ON CONFLICT(user_id) DO UPDATE SET vertical = excluded.vertical""",
        (user_id, vertical),
    )
    conn.commit()
    conn.close()


def get_module(module_id):
    return query("SELECT * FROM modules WHERE id = ?", (module_id,), one=True)


def get_module_by_slug(slug):
    return query("SELECT * FROM modules WHERE slug = ?", (slug,), one=True)


def list_lessons(module_id):
    return query(
        """SELECT id, module_id, slug, title, display_order, content_type, content_body, url, est_minutes
           FROM lessons
           WHERE module_id = ?
           ORDER BY display_order, id""",
        (module_id,),
    )


def get_lesson(lesson_id):
    return query("SELECT * FROM lessons WHERE id = ?", (lesson_id,), one=True)


def get_lesson_progress(user_id, lesson_id):
    return query(
        "SELECT status, completed_at FROM lesson_progress WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
        one=True,
    )


def mark_lesson(user_id, lesson_id, status):
    """status in ('not_started','in_progress','completed')."""
    completed_at = "datetime('now')" if status == "completed" else "NULL"
    conn = get_connection()
    conn.execute(
        f"""INSERT INTO lesson_progress (user_id, lesson_id, status, completed_at)
            VALUES (?, ?, ?, {completed_at})
            ON CONFLICT(user_id, lesson_id) DO UPDATE SET
              status = excluded.status,
              completed_at = {completed_at}""",
        (user_id, lesson_id, status),
    )
    conn.commit()
    conn.close()


def module_progress_for_user(user_id, vertical=None):
    """Return [{module_id, title, slug, display_order, week_target, total, completed, pct}] for one user.

    Filtered to a single vertical when given.
    """
    where_extra = "AND m.vertical = ?" if vertical else ""
    params = (user_id, vertical) if vertical else (user_id,)
    return query(
        f"""SELECT m.id AS module_id,
                  m.title,
                  m.slug,
                  m.display_order,
                  m.week_target,
                  m.vertical,
                  COUNT(l.id) AS total,
                  SUM(CASE WHEN lp.status = 'completed' THEN 1 ELSE 0 END) AS completed,
                  CAST(
                    CASE WHEN COUNT(l.id) = 0 THEN 0
                         ELSE 100.0 * SUM(CASE WHEN lp.status = 'completed' THEN 1 ELSE 0 END) / COUNT(l.id)
                    END AS INTEGER) AS pct
           FROM modules m
           LEFT JOIN lessons l ON l.module_id = m.id
           LEFT JOIN lesson_progress lp ON lp.lesson_id = l.id AND lp.user_id = ?
           WHERE m.is_active = 1 {where_extra}
           GROUP BY m.id
           ORDER BY m.display_order, m.id""",
        params,
    )


def next_lesson_for_user(user_id, vertical=None):
    """First lesson (by module order, then lesson order) that the user hasn't completed."""
    where_extra = "AND m.vertical = ?" if vertical else ""
    params = (user_id, vertical) if vertical else (user_id,)
    return query(
        f"""SELECT l.id AS lesson_id, l.title AS lesson_title, l.module_id,
                  m.title AS module_title, m.slug AS module_slug
           FROM lessons l
           JOIN modules m ON m.id = l.module_id
           LEFT JOIN lesson_progress lp ON lp.lesson_id = l.id AND lp.user_id = ?
           WHERE m.is_active = 1 {where_extra}
             AND (lp.status IS NULL OR lp.status != 'completed')
           ORDER BY m.display_order, m.id, l.display_order, l.id
           LIMIT 1""",
        params,
        one=True,
    )


def team_module_rollup(manager_id=None):
    """Per-rep rollup: total lessons, completed lessons, last activity."""
    params = ()
    where = "WHERE u.role = 'rep' AND u.is_active = 1"
    if manager_id is not None:
        where += " AND u.manager_id = ?"
        params = (manager_id,)
    return query(
        f"""SELECT u.id AS user_id, u.full_name, u.email, u.manager_id,
                   (SELECT COUNT(*) FROM lessons l JOIN modules m ON m.id = l.module_id WHERE m.is_active = 1) AS total_lessons,
                   COALESCE(SUM(CASE WHEN lp.status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_lessons,
                   MAX(lp.completed_at) AS last_activity
            FROM users u
            LEFT JOIN lesson_progress lp ON lp.user_id = u.id
            LEFT JOIN lessons l ON l.id = lp.lesson_id
            LEFT JOIN modules m ON m.id = l.module_id AND m.is_active = 1
            {where}
            GROUP BY u.id
            ORDER BY u.full_name""",
        params,
    )
