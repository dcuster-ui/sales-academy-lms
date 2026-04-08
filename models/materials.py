"""Materials and progress model queries."""

from db.database import query, execute


def get_categories():
    return query("SELECT * FROM material_categories ORDER BY display_order")


def get_materials_by_category(category_id=None):
    if category_id:
        return query(
            "SELECT * FROM materials WHERE category_id = ? ORDER BY display_order, title",
            (category_id,),
        )
    return query("SELECT * FROM materials ORDER BY category_id, display_order, title")


def get_materials_with_progress(user_id):
    """Get all materials with user's completion status."""
    return query(
        """SELECT m.*, mc.name as category_name, mc.display_order as cat_order,
                  COALESCE(mp.status, 'not_started') as progress_status,
                  mp.completed_at
           FROM materials m
           JOIN material_categories mc ON m.category_id = mc.id
           LEFT JOIN material_progress mp ON m.id = mp.material_id AND mp.user_id = ?
           ORDER BY mc.display_order, m.display_order, m.title""",
        (user_id,),
    )


def get_material_progress_count(user_id):
    """Count completed materials for a user."""
    row = query(
        "SELECT COUNT(*) as cnt FROM material_progress WHERE user_id = ? AND status = 'completed'",
        (user_id,),
        one=True,
    )
    return row["cnt"] if row else 0


def get_total_materials():
    row = query("SELECT COUNT(*) as cnt FROM materials", one=True)
    return row["cnt"] if row else 0


def mark_material_complete(user_id, material_id):
    execute(
        """INSERT INTO material_progress (user_id, material_id, status, completed_at)
           VALUES (?, ?, 'completed', datetime('now'))
           ON CONFLICT(user_id, material_id) DO UPDATE SET status='completed', completed_at=datetime('now')""",
        (user_id, material_id),
    )


def mark_material_incomplete(user_id, material_id):
    execute(
        """INSERT INTO material_progress (user_id, material_id, status)
           VALUES (?, ?, 'not_started')
           ON CONFLICT(user_id, material_id) DO UPDATE SET status='not_started', completed_at=NULL""",
        (user_id, material_id),
    )
