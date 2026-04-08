"""Seed data for Sales Academy — February & March 2026 cohorts."""


def seed_all(conn):
    """Insert all initial data. Called by database.py when DB is empty."""
    cursor = conn.cursor()

    # --- Users ---
    # Admins (training team)
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
    admin_id = 1  # Dani Langan

    # Managers (also have admin access)
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

    # Reps who are no longer active (removed from roster)
    inactive_reps = {"Diamond Davis"}

    # ===== FEBRUARY 2026 COHORT (Jamere Walton) =====
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

    # ===== MARCH 2026 COHORT (Max Josef) =====
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
    cert_ids = []
    for name, category, order, target_week in certs:
        cursor.execute(
            "INSERT INTO certifications (name, category, display_order, target_week) VALUES (?, ?, ?, ?)",
            (name, category, order, target_week),
        )
        cert_ids.append(cursor.lastrowid)

    # --- Seed certification results ---

    # FEBRUARY cohort: all completed (6 weeks done), all 10/10 passed
    for rid in feb_rep_ids:
        for cid in cert_ids:
            cursor.execute(
                """INSERT INTO certification_attempts
                   (user_id, certification_id, cohort_id, attempt_number, result, attempt_date)
                   VALUES (?, ?, ?, 1, 'pass', '2026-03-20')""",
                (rid, cid, feb_cohort_id),
            )

    # MARCH cohort: in progress — Diamond Davis 6/10, all others 10/10
    for i, rid in enumerate(mar_rep_ids):
        rep_name = mar_reps[i][1]
        for j, cid in enumerate(cert_ids):
            if rep_name == "Diamond Davis" and j in [1, 3, 4, 5]:
                cursor.execute(
                    """INSERT INTO certification_attempts
                       (user_id, certification_id, cohort_id, attempt_number, result, attempt_date)
                       VALUES (?, ?, ?, 1, 'fail', '2026-03-28')""",
                    (rid, cid, mar_cohort_id),
                )
            else:
                cursor.execute(
                    """INSERT INTO certification_attempts
                       (user_id, certification_id, cohort_id, attempt_number, result, attempt_date)
                       VALUES (?, ?, ?, 1, 'pass', '2026-03-28')""",
                    (rid, cid, mar_cohort_id),
                )

    # --- Material Categories ---
    categories = [
        ("Sales Process (Pre-Close)", 1),
        ("Objection Handling", 2),
        ("Conversation Cards", 3),
        ("Groupon", 4),
        ("Market Management", 5),
        ("Pipeline Process", 6),
        ("Sales Process (Post Close)", 7),
        ("Tooling", 8),
        ("3PIP", 9),
        ("SOP", 10),
    ]
    cat_ids = {}
    for name, order in categories:
        cursor.execute(
            "INSERT INTO material_categories (name, display_order) VALUES (?, ?)",
            (name, order),
        )
        cat_ids[name] = cursor.lastrowid

    # --- Materials (from the materials library sheet) ---
    # Google Drive folder URLs sourced from Sales Academy Training Materials drive
    _SP = "https://drive.google.com/drive/folders/"  # folder prefix
    _DOC = "https://docs.google.com/document/d/"     # doc prefix

    materials_data = [
        # (title, type, category_id, week, schedule_day, url)
        # Day 1: Welcome, Groupon overview, orientation
        ("Welcome / SIP & BD Expectations", "deck", cat_ids["Groupon"], 1, 1, _SP + "1qkszJreCAIwwkpj49KC-DWjhEOE2uf88"),
        ("Organizing for Success", "deck", cat_ids["Tooling"], 1, 1, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        ("Groupon Platform", "deck", cat_ids["Groupon"], 1, 1, _SP + "1dGuZ3H90ZfCquEjBpXEWGND0kBHdTsPe"),
        ("Industry Education", "deck", cat_ids["Groupon"], 1, 1, _SP + "1nzASPAY2IoCxdiubuvyL3u1plUYx-0Mv"),
        ("BD Instruction Manual", "document", cat_ids["SOP"], 1, 1, _DOC + "1PU_HjFXnVIGCIZHFYfSzaLGcAavGlJz0vUq8x7h0oP0/edit"),
        # Day 2: Sales Process, Front End, TUIT, Front End OH
        ("Sales Process Overview", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "14p6bicNyUES4GtH10G9W9MNzpo88bDjP"),
        ("Sales Process Overview", "video", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "14p6bicNyUES4GtH10G9W9MNzpo88bDjP"),
        ("Front End", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "1JWRHAUVuRA51Pha3qQkSyjj2w8lbMGVf"),
        ("Front End", "video", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "1JWRHAUVuRA51Pha3qQkSyjj2w8lbMGVf"),
        ("TUIT & Needs Assessment", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "1WgotCyXkbk_oLfgroLJNbWd4G8vRfhVq"),
        ("TUIT & Needs Assessment", "video", cat_ids["Sales Process (Pre-Close)"], 1, 2, _SP + "1WgotCyXkbk_oLfgroLJNbWd4G8vRfhVq"),
        ("Objection Handling: Front End", "deck", cat_ids["Objection Handling"], 1, 2, _SP + "1mRJ93772Q3rW5B3vbXJctfVj6MQW0aIT"),
        ("Objection Handling: Front End", "video", cat_ids["Objection Handling"], 1, 2, _SP + "1mRJ93772Q3rW5B3vbXJctfVj6MQW0aIT"),
        # Day 3: TUIT OH, Appointment Setting, Gatekeepers, Salesloft, Salesforce
        ("Objection Handling: Needs Assessment", "deck", cat_ids["Objection Handling"], 1, 3, _SP + "1QI7adBaOQUZ3kka24t73SLBkX8KXkXDP"),
        ("Objection Handling: Needs Assessment", "video", cat_ids["Objection Handling"], 1, 3, _SP + "1QI7adBaOQUZ3kka24t73SLBkX8KXkXDP"),
        ("Appointment Setting", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 3, _SP + "1XAa2EgoPUhcRe0shEagS07z7FMRPhIhs"),
        ("Appointment Setting", "video", cat_ids["Sales Process (Pre-Close)"], 1, 3, _SP + "1XAa2EgoPUhcRe0shEagS07z7FMRPhIhs"),
        ("Working with Gatekeepers", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 3, _SP + "1coF65lhqZTNxNbRKrqtdXtKP8ZpFJdpi"),
        ("Working with Gatekeepers", "video", cat_ids["Sales Process (Pre-Close)"], 1, 3, _SP + "1coF65lhqZTNxNbRKrqtdXtKP8ZpFJdpi"),
        ("Navigating Salesforce", "deck", cat_ids["Tooling"], 1, 3, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        ("Salesloft User Guide", "deck", cat_ids["Tooling"], 1, 3, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        ("Merchant Quality & Deal Structure Overview", "deck", cat_ids["Market Management"], 1, 3, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
        # Day 4: Promotional Programs, Deal Structure, AIDG, Presentation
        ("Promotional Programs", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 4, _SP + "1vFYADvJHRkJmYrYLVfwCj4ac6pqQSS79"),
        ("AIDG - Guide for Sales", "document", cat_ids["Tooling"], 1, 4, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        ("Presentation: The What and The How", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 4, _SP + "1bAs-IvNQ34lWQrAePYqRlItId_ydu2Kx"),
        # Day 5: Presentation OH, Merchant Center, SalesloftCX
        ("Objection Handling: Presentation", "deck", cat_ids["Objection Handling"], 1, 5, _SP + "1_qtYYrLGXvObOIw30MAkJm1ktmZxWx_6"),
        ("Objection Handling: Presentation", "video", cat_ids["Objection Handling"], 1, 5, _SP + "1_qtYYrLGXvObOIw30MAkJm1ktmZxWx_6"),
        ("Merchant Center", "deck", cat_ids["Sales Process (Pre-Close)"], 1, 5, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
        ("Coffee To Go", "deck", cat_ids["Tooling"], 1, 5, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        # Days 6-10 (Week 2): Conversation Cards, deep dives, call blocks
        ("BD Conversation Card - Full Version", "deck", cat_ids["Conversation Cards"], 2, 6, _SP + "1EeeRMe5wKoO7Q0V-M-B8eUYDz1VmCP2M"),
        ("BD Conversation Card - Short Version", "deck", cat_ids["Conversation Cards"], 2, 6, _SP + "1EeeRMe5wKoO7Q0V-M-B8eUYDz1VmCP2M"),
        ("DCT Guide for Sales - Unified Flow", "document", cat_ids["Tooling"], 2, 7, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        ("Zingtree - One Pager", "document", cat_ids["Tooling"], 2, 8, _SP + "1dASxvGfAg-5IkrVhu77ZNgwt-_6C3Tzh"),
        # Weeks 3-6: Post Close, Pipeline, 3PIP
        ("Post Close Process", "deck", cat_ids["Sales Process (Post Close)"], 3, 11, _SP + "1-5Xq_SEt9bgZbABFsm_uJit77LFqVGjE"),
        ("Post-Close Tasks: Gemini Deal Edits", "deck", cat_ids["Sales Process (Post Close)"], 3, 11, _SP + "1-5Xq_SEt9bgZbABFsm_uJit77LFqVGjE"),
        ("Deal Stage Breakdown for Success", "deck", cat_ids["Pipeline Process"], 3, 12, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
        ("Payment Terms", "deck", cat_ids["Sales Process (Post Close)"], 4, 16, _SP + "1n8ClJoatvlBkLWwc-qUhbkdtkIHU0zaq"),
        ("Lead Sourcing and Creation", "deck", cat_ids["Pipeline Process"], 4, 17, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
        ("Information Requests & Cases", "deck", cat_ids["Sales Process (Post Close)"], 4, 18, _SP + "1-5Xq_SEt9bgZbABFsm_uJit77LFqVGjE"),
        ("3PIP Overview for TTD Sales", "deck", cat_ids["3PIP"], 5, 21, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
        ("3PIP Overview for TTD Sales", "video", cat_ids["3PIP"], 5, 21, _SP + "131Wn590U5Ey9XCoEuvD0_s5g1Gx3knSG"),
    ]

    for title, mtype, cat_id, week, day, url in materials_data:
        cursor.execute(
            """INSERT INTO materials (category_id, title, material_type, url, week_available, schedule_day, is_required)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (cat_id, title, mtype, url, week, day),
        )

    # --- Performance Metrics (real BD tracker data from Keboola/BigQuery) ---
    # Source: out.c-bd-performance.bd_tracker

    def _insert_perf(perf_rows, name_to_id, cohort_id):
        for row in perf_rows:
            name, week, dials, solid, conn_, dmc, appts, na, pres, cw, umc, uml, gp = row
            uid = name_to_id.get(name)
            if uid:
                cursor.execute(
                    """INSERT INTO performance_metrics
                       (user_id, cohort_id, report_week, dials, solid_calls, connected,
                        dm_connect, appointments_set, needs_assessment, presentations,
                        close_won, um_closed, um_launched, gp_amount)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (uid, cohort_id, week, dials, solid, conn_, dmc, appts, na, pres, cw, umc, uml, gp),
                )

    # FEBRUARY cohort — Jamere Walton's team (6 weeks of data, deals closing)
    feb_name_to_id = {name: feb_rep_ids[i] for i, (_, name) in enumerate(feb_reps)}
    feb_perf = [
        # (rep_name, report_week, dials, solid_calls, connected, dm_connect, appts, needs_assess, presentations, close_won, um_closed, um_launched, gp_amount)
        ("Abby Estrada",      "2026-02-23",  67,  2,  30,  0, 0, 0, 0, 0, 0, 0, 0),
        ("Abby Estrada",      "2026-03-02", 304, 27, 126, 22, 1, 1, 0, 0, 0, 0, 0),
        ("Abby Estrada",      "2026-03-09", 475, 28, 196, 26, 3, 0, 0, 0, 0, 0, 0),
        ("Abby Estrada",      "2026-03-16", 359, 30, 146, 30, 0, 2, 0, 0, 0, 0, 0),
        ("Abby Estrada",      "2026-03-23", 288, 33,  91, 24, 4, 0, 2, 0, 0, 0, 0),
        ("Abby Estrada",      "2026-03-30", 367, 24, 131, 44, 5, 1, 0, 2, 0, 0, 0),
        ("Auden Tully",       "2026-02-23",  38,  4,  24,  4, 1, 0, 0, 0, 0, 0, 0),
        ("Auden Tully",       "2026-03-02", 172, 22,  77, 22, 2, 3, 2, 0, 0, 0, 0),
        ("Auden Tully",       "2026-03-09", 345, 21,  99, 28, 3, 2, 0, 1, 0, 1, 27),
        ("Auden Tully",       "2026-03-16", 259, 21,  86, 26, 2, 2, 0, 1, 1, 1, 27),
        ("Auden Tully",       "2026-03-23", 208, 21,  80, 29, 5, 1, 0, 0, 0, 0, 0),
        ("Auden Tully",       "2026-03-30", 135, 18,  61, 31, 0, 3, 2, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-02-23",   0,  0,   0,  0, 0, 0, 0, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-03-02", 230, 21,  81, 26, 4, 2, 0, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-03-09", 223, 39,  70, 26, 1, 0, 0, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-03-16", 307, 22,  89, 22, 2, 0, 0, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-03-23", 219, 27,  59, 21, 4, 3, 0, 0, 0, 0, 0),
        ("Dhara Patel",       "2026-03-30", 205, 19,  56, 22, 3, 1, 1, 1, 1, 0, 0),
        ("Lindsey Gulliksen", "2026-02-23",  42,  6,  22,  5, 1, 0, 0, 0, 0, 0, 0),
        ("Lindsey Gulliksen", "2026-03-02", 345, 28, 133, 22, 3, 1, 0, 0, 0, 0, 0),
        ("Lindsey Gulliksen", "2026-03-09", 323, 34, 145, 31, 1, 3, 2, 0, 0, 0, 0),
        ("Lindsey Gulliksen", "2026-03-16", 400, 24, 144, 21, 1, 1, 2, 0, 0, 0, 0),
        ("Lindsey Gulliksen", "2026-03-23", 178, 16,  58, 16, 1, 2, 1, 1, 0, 0, 0),
        ("Lindsey Gulliksen", "2026-03-30", 261, 26,  89, 25, 1, 4, 2, 1, 1, 0, 0),
        ("Michael Wu",        "2026-02-23",  93,  7,  44,  6, 0, 0, 0, 0, 0, 0, 0),
        ("Michael Wu",        "2026-03-02", 330, 29, 137, 17, 1, 1, 0, 0, 0, 0, 0),
        ("Michael Wu",        "2026-03-09", 236, 31,  74, 13, 2, 2, 1, 0, 0, 0, 0),
        ("Michael Wu",        "2026-03-16", 187, 35,  69, 13, 1, 3, 2, 1, 1, 0, 0),
        ("Michael Wu",        "2026-03-23", 200, 46,  81, 11, 1, 2, 1, 0, 0, 0, 0),
        ("Michael Wu",        "2026-03-30", 107, 32,  49, 21, 4, 2, 1, 1, 1, 0, 0),
        ("Naomi Desrosiers",  "2026-02-23",  67,  5,  27,  1, 0, 0, 0, 0, 0, 0, 0),
        ("Naomi Desrosiers",  "2026-03-02", 331, 26, 123, 20, 2, 2, 1, 0, 0, 0, 0),
        ("Naomi Desrosiers",  "2026-03-09", 361, 20, 121, 22, 2, 2, 0, 0, 0, 0, 0),
        ("Naomi Desrosiers",  "2026-03-16", 330, 19, 133, 28, 2, 1, 2, 0, 0, 0, 0),
        ("Naomi Desrosiers",  "2026-03-23", 375, 14, 132, 27, 0, 2, 1, 0, 0, 0, 0),
        ("Naomi Desrosiers",  "2026-03-30", 290, 17, 102, 27, 0, 1, 0, 2, 1, 0, 0),
        ("Nathaniel Ramos",   "2026-02-23",   0,  0,   0,  0, 0, 0, 0, 0, 0, 0, 0),
        ("Nathaniel Ramos",   "2026-03-02", 320, 17,  83,  5, 1, 1, 0, 0, 0, 0, 0),
        ("Nathaniel Ramos",   "2026-03-09", 435, 26, 128, 12, 1, 2, 0, 0, 0, 0, 0),
        ("Nathaniel Ramos",   "2026-03-16", 479, 19, 113, 13, 0, 2, 1, 0, 0, 0, 0),
        ("Nathaniel Ramos",   "2026-03-23", 255, 24,  84,  7, 2, 3, 0, 0, 0, 0, 0),
        ("Nathaniel Ramos",   "2026-03-30", 268, 27,  94, 15, 1, 2, 2, 1, 1, 0, 0),
        ("Sama Ahmed",        "2026-02-23", 134, 13,  55,  9, 1, 1, 0, 0, 0, 0, 0),
        ("Sama Ahmed",        "2026-03-02", 484, 29, 124, 22, 0, 3, 1, 0, 0, 0, 0),
        ("Sama Ahmed",        "2026-03-09", 447, 20, 121, 26, 4, 2, 1, 0, 0, 0, 0),
        ("Sama Ahmed",        "2026-03-16", 532, 33, 116, 24, 2, 1, 0, 0, 0, 0, 0),
        ("Sama Ahmed",        "2026-03-23", 297, 34,  81, 26, 4, 4, 1, 1, 1, 0, 0),
        ("Sama Ahmed",        "2026-03-30", 371, 37,  74, 30, 1, 6, 1, 0, 0, 0, 0),
        ("Vasi Skopis",       "2026-02-23", 176,  6,  51,  6, 2, 1, 0, 0, 0, 0, 0),
        ("Vasi Skopis",       "2026-03-02", 608, 42, 145, 29, 2, 3, 2, 0, 0, 0, 0),
        ("Vasi Skopis",       "2026-03-09", 612, 39, 154, 33, 6, 2, 2, 1, 0, 1, 53),
        ("Vasi Skopis",       "2026-03-16", 452, 40, 152, 59, 3, 9, 4, 1, 1, 0, 53),
        ("Vasi Skopis",       "2026-03-23", 622, 41, 179, 86, 8, 8, 1, 0, 0, 2, 0),
        ("Vasi Skopis",       "2026-03-30", 478, 47, 148, 72, 2, 8, 1, 1, 1, 0, 53),
    ]
    _insert_perf(feb_perf, feb_name_to_id, feb_cohort_id)

    # MARCH cohort — Max Josef's team (2 weeks of data)
    mar_name_to_id = {name: mar_rep_ids[i] for i, (_, name) in enumerate(mar_reps)}
    mar_perf = [
        ("Asalah Muhammad",    "2026-03-23",  90,  9,  74,  5, 0, 0, 0, 0, 0, 0, 0),
        ("Asalah Muhammad",    "2026-03-30", 458, 41, 187, 28, 1, 0, 0, 0, 0, 0, 0),
        ("Eric Washington",    "2026-03-23",  72,  6,  17,  3, 0, 0, 0, 0, 0, 0, 0),
        ("Eric Washington",    "2026-03-30", 348, 29,  81,  6, 1, 0, 0, 0, 0, 0, 0),
        ("Izzeldeen Abdelhadi","2026-03-23",  73,  1,  17, 10, 1, 0, 0, 0, 0, 0, 0),
        ("Izzeldeen Abdelhadi","2026-03-30", 435, 13,  63, 35, 2, 2, 2, 0, 0, 0, 0),
        ("Joe Yoon",           "2026-03-23",  43,  3,  18,  1, 0, 0, 0, 0, 0, 0, 0),
        ("Joe Yoon",           "2026-03-30", 494, 12,  78, 14, 2, 0, 0, 0, 0, 0, 0),
        ("Khris Stevens",      "2026-03-23",  75,  1,  13,  1, 1, 0, 0, 0, 0, 0, 0),
        ("Khris Stevens",      "2026-03-30", 402, 12,  52, 18, 1, 3, 0, 0, 0, 0, 0),
        ("Maggie Scott",       "2026-03-23",  88,  2,  30,  0, 0, 0, 0, 0, 0, 0, 0),
        ("Maggie Scott",       "2026-03-30", 525, 27, 100, 35, 1, 2, 0, 0, 0, 0, 0),
        ("Mark Starling",      "2026-03-23",  68,  7,  15,  2, 1, 0, 0, 0, 0, 0, 0),
        ("Mark Starling",      "2026-03-30", 380, 47,  87, 16, 1, 0, 0, 0, 0, 0, 0),
        ("Olivier Onze",       "2026-03-23",  23,  3,  11,  4, 1, 1, 0, 0, 0, 0, 0),
        ("Olivier Onze",       "2026-03-30", 472, 28, 102, 21, 1, 0, 0, 0, 0, 0, 0),
        ("William Velazquez",  "2026-03-23",  69,  5,  12,  5, 0, 0, 0, 0, 0, 0, 0),
        ("William Velazquez",  "2026-03-30", 396, 26,  53, 15, 2, 2, 0, 0, 0, 0, 0),
    ]
    _insert_perf(mar_perf, mar_name_to_id, mar_cohort_id)

    conn.commit()
    print("Seed data loaded successfully.")
