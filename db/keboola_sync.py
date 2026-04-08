"""Keboola sync — pull certification data from Keboola Storage into local SQLite."""

import os
import csv
import io
import requests
from db.database import query, execute, get_connection

# Keboola connection settings
KBC_URL = os.environ.get("KBC_URL", "https://connection.groupon.keboola.cloud")
KBC_TOKEN = os.environ.get("KBC_TOKEN", "")
CERT_TABLE_ID = "in.c-sales-academy.cert_tracker"

# Map Keboola column names → local certification names
CERT_COLUMN_MAP = {
    "Front_End": "Front End",
    "OH_Front_End": "OH: Front End",
    "TUIT__Needs": "TUIT & Needs Assessment",
    "OH_TUIT": "OH: TUIT",
    "Presentation": "Presentation: The What & The How",
    "OH_Presentation": "OH: Presentation",
    "Appt_Setting": "Appointment Setting",
    "Gatekeepers": "Gatekeepers",
    "Promo_Programs": "Promotional Programs",
    "Salesloft": "Salesloft",
}


def is_keboola_configured():
    """Check if Keboola token is available."""
    return bool(KBC_TOKEN)


def fetch_cert_data():
    """Fetch cert tracker CSV from Keboola Storage API."""
    url = f"{KBC_URL}/v2/storage/tables/{CERT_TABLE_ID}/data-preview"
    headers = {"X-StorageApi-Token": KBC_TOKEN}
    resp = requests.get(url, headers=headers, params={"limit": 500})
    resp.raise_for_status()
    return resp.text


def sync_certifications():
    """Pull cert data from Keboola and upsert into local SQLite.

    Returns (synced_count, skipped_names) tuple.
    """
    csv_text = fetch_cert_data()
    reader = csv.DictReader(io.StringIO(csv_text))

    # Build lookup: cert name → cert id
    certs = query("SELECT id, name FROM certifications WHERE is_active = 1")
    cert_name_to_id = {c["name"]: c["id"] for c in certs}

    # Build lookup: full_name → (user_id, cohort_id)
    users = query(
        """SELECT u.id as user_id, u.full_name, ce.cohort_id
           FROM users u
           JOIN cohort_enrollments ce ON ce.user_id = u.id
           WHERE u.role = 'rep' AND u.is_active = 1 AND ce.status = 'active'"""
    )
    name_to_user = {u["full_name"]: u for u in users}

    conn = get_connection()
    cursor = conn.cursor()
    synced = 0
    skipped = []

    for row in reader:
        rep_name = row.get("Name", "").strip()
        if not rep_name:
            continue

        user = name_to_user.get(rep_name)
        if not user:
            skipped.append(rep_name)
            continue

        user_id = user["user_id"]
        cohort_id = user["cohort_id"]

        for col_name, cert_name in CERT_COLUMN_MAP.items():
            value = row.get(col_name, "").strip()
            cert_id = cert_name_to_id.get(cert_name)
            if not cert_id:
                continue

            if value == "\u2705":  # ✅
                result = "pass"
            elif value == "\U0001f7e5":  # 🟥
                result = "fail"
            else:
                continue

            # Check if an attempt already exists for this user+cert+cohort
            existing = cursor.execute(
                """SELECT id, result FROM certification_attempts
                   WHERE user_id = ? AND certification_id = ? AND cohort_id = ?
                   ORDER BY attempt_number DESC LIMIT 1""",
                (user_id, cert_id, cohort_id),
            ).fetchone()

            if existing:
                # Update if result changed
                if existing[1] != result:
                    cursor.execute(
                        """UPDATE certification_attempts SET result = ?, attempt_date = date('now')
                           WHERE id = ?""",
                        (result, existing[0]),
                    )
                    synced += 1
            else:
                # Insert new attempt
                cursor.execute(
                    """INSERT INTO certification_attempts
                       (user_id, certification_id, cohort_id, attempt_number, result, notes)
                       VALUES (?, ?, ?, 1, ?, 'Synced from Google Sheet')""",
                    (user_id, cert_id, cohort_id, result),
                )
                synced += 1

    conn.commit()
    conn.close()
    return synced, skipped
