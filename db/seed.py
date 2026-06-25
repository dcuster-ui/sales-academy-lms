"""Seed data for Sales Academy — users, cohorts, certifications, modules."""

import json
import os


def seed_all(conn):
    """Insert all initial data. Called by database.py when DB is empty."""
    cursor = conn.cursor()

    # --- Users (training admins) ---
    admin_users = [
        ("dcuster@groupon.com", "Dani Langan"),
        ("ghooper@groupon.com", "Geoff Hooper"),
        ("rmoreno@groupon.com", "Raquel Moreno"),
        ("cneuendorf@groupon.com", "Chad Neuendorf"),
    ]
    for email, name in admin_users:
        cursor.execute(
            "INSERT INTO users (email, full_name, role) VALUES (?, ?, ?)",
            (email, name, "admin"),
        )

    # Managers (treated as admin so they get the team views)
    cursor.execute(
        "INSERT INTO users (email, full_name, role) VALUES (?, ?, ?)",
        ("mjosef@groupon.com", "Max Josef", "admin"),
    )
    manager_josef_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (email, full_name, role) VALUES (?, ?, ?)",
        ("jawalton@groupon.com", "Jamere Walton", "admin"),
    )
    manager_walton_id = cursor.lastrowid

    # Reps no longer on roster
    inactive_reps = {"Diamond Davis"}

    # --- February 2026 cohort (Walton) ---
    feb_reps = [
        ("aestrada@groupon.com", "Abby Estrada"),
        ("atully@groupon.com", "Auden Tully"),
        ("dpatel@groupon.com", "Dhara Patel"),
        ("lgulliksen@groupon.com", "Lindsey Gulliksen"),
        ("mwu@groupon.com", "Michael Wu"),
        ("ndesrosiers@groupon.com", "Naomi Desrosiers"),
        ("nramos@groupon.com", "Nathaniel Ramos"),
        ("sahmed@groupon.com", "Sama Ahmed"),
        ("vskopis@groupon.com", "Vasi Skopis"),
    ]
    feb_rep_ids = []
    for email, name in feb_reps:
        is_active = 0 if name in inactive_reps else 1
        cursor.execute(
            "INSERT INTO users (email, full_name, role, manager_id, is_active) VALUES (?, ?, 'rep', ?, ?)",
            (email, name, manager_walton_id, is_active),
        )
        feb_rep_ids.append(cursor.lastrowid)

    cursor.execute(
        "INSERT INTO cohorts (name, start_date, end_date, status) VALUES (?, ?, ?, ?)",
        ("February 2026", "2026-02-23", "2026-04-03", "completed"),
    )
    feb_cohort_id = cursor.lastrowid
    for rid in feb_rep_ids:
        cursor.execute(
            "INSERT INTO cohort_enrollments (cohort_id, user_id, hire_date) VALUES (?, ?, ?)",
            (feb_cohort_id, rid, "2026-02-23"),
        )

    # --- March 2026 cohort (Josef) ---
    mar_reps = [
        ("asmuhammad@groupon.com", "Asalah Muhammad"),
        ("didavis@groupon.com", "Diamond Davis"),
        ("erwashington@groupon.com", "Eric Washington"),
        ("iabdelhadi@groupon.com", "Izzeldeen Abdelhadi"),
        ("joyoon@groupon.com", "Joe Yoon"),
        ("kstevens@groupon.com", "Khris Stevens"),
        ("mascott@groupon.com", "Maggie Scott"),
        ("mstarling@groupon.com", "Mark Starling"),
        ("oonze@groupon.com", "Olivier Onze"),
        ("wvelazquez@groupon.com", "William Velazquez"),
    ]
    mar_rep_ids = []
    for email, name in mar_reps:
        is_active = 0 if name in inactive_reps else 1
        cursor.execute(
            "INSERT INTO users (email, full_name, role, manager_id, is_active) VALUES (?, ?, 'rep', ?, ?)",
            (email, name, manager_josef_id, is_active),
        )
        mar_rep_ids.append(cursor.lastrowid)

    cursor.execute(
        "INSERT INTO cohorts (name, start_date, end_date, status) VALUES (?, ?, ?, ?)",
        ("March 2026", "2026-03-23", "2026-05-01", "active"),
    )
    mar_cohort_id = cursor.lastrowid
    for rid in mar_rep_ids:
        cursor.execute(
            "INSERT INTO cohort_enrollments (cohort_id, user_id, hire_date) VALUES (?, ?, ?)",
            (mar_cohort_id, rid, "2026-03-23"),
        )

    # --- Certifications ---
    certs = [
        ("Front End", "Sales Process", 1, 1),
        ("OH: Front End", "Objection Handling", 2, 2),
        ("TUIT & Needs Assessment", "Sales Process", 3, 2),
        ("OH: TUIT", "Objection Handling", 4, 3),
        ("Presentation: The What & The How", "Sales Process", 5, 3),
        ("OH: Presentation", "Objection Handling", 6, 3),
        ("Appointment Setting", "Sales Process", 7, 4),
        ("Gatekeepers", "Sales Process", 8, 4),
        ("Promotional Programs", "Sales Process", 9, 5),
        ("Salesloft", "Tooling", 10, 5),
    ]
    for name, category, order, target_week in certs:
        cursor.execute(
            "INSERT INTO certifications (name, category, display_order, target_week) VALUES (?, ?, ?, ?)",
            (name, category, order, target_week),
        )

    # --- Modules / lessons (from seed_modules.json) ---
    seed_path = os.path.join(os.path.dirname(__file__), "seed_modules.json")
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Stash the original report's <style> block so the lesson viewer can render
        # the embedded res-card HTML with its original look.
        css = data.get("lesson_css") or ""
        if css:
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value) VALUES ('lesson_css', ?)",
                (css,),
            )

        for m in data.get("modules", []):
            cursor.execute(
                """INSERT INTO modules (slug, title, description, display_order, week_target, vertical, is_required)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    m["slug"],
                    m["title"],
                    m.get("description"),
                    m.get("display_order", 0),
                    m.get("week_target"),
                    m.get("vertical"),
                    1 if m.get("is_required", True) else 0,
                ),
            )
            module_id = cursor.lastrowid
            for i, lesson in enumerate(m.get("lessons", []), start=1):
                cursor.execute(
                    """INSERT INTO lessons (module_id, slug, title, display_order, content_type, content_body, url, est_minutes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        module_id,
                        lesson["slug"],
                        lesson["title"],
                        lesson.get("display_order", i),
                        lesson["content_type"],
                        lesson.get("content_body"),
                        lesson.get("url"),
                        lesson.get("est_minutes"),
                    ),
                )

    conn.commit()
    print("Seed data loaded successfully.")
