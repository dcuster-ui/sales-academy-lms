"""User model queries."""

from db.database import query, execute


def get_all_users(role=None, active_only=True):
    sql = "SELECT * FROM users WHERE 1=1"
    params = []
    if role:
        sql += " AND role = ?"
        params.append(role)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY full_name"
    return query(sql, params)


def get_user(user_id):
    return query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)


def get_reps_for_manager(manager_id):
    return query(
        "SELECT * FROM users WHERE manager_id = ? AND role = 'rep' AND is_active = 1 ORDER BY full_name",
        (manager_id,),
    )


def create_user(email, full_name, role, manager_id=None):
    return execute(
        "INSERT INTO users (email, full_name, role, manager_id) VALUES (?, ?, ?, ?)",
        (email, full_name, role, manager_id),
    )


def set_user_active(user_id, is_active):
    """Activate or deactivate a user. is_active: 1 = active, 0 = inactive."""
    return execute(
        "UPDATE users SET is_active = ?, updated_at = datetime('now') WHERE id = ?",
        (1 if is_active else 0, user_id),
    )
