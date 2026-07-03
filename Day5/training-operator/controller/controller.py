"""
Training Controller - watches Training CRs and syncs them to the database.
Uses kopf (Kubernetes Operator Framework) for event handling.
"""

import kopf
import sqlite3
import logging
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/data/trainings.db")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("training-controller")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trainings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cr_name       TEXT UNIQUE NOT NULL,
            namespace     TEXT NOT NULL,
            training_name TEXT NOT NULL,
            duration      INTEGER NOT NULL,
            from_date     TEXT NOT NULL,
            to_date       TEXT NOT NULL,
            mode          TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


def upsert_training(cr_name, namespace, spec):
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM trainings WHERE cr_name = ?", (cr_name,))
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE trainings
            SET training_name = ?,
                duration      = ?,
                from_date     = ?,
                to_date       = ?,
                mode          = ?,
                updated_at    = ?
            WHERE cr_name = ?
        """, (
            spec["trainingName"],
            spec["duration"],
            spec["fromDate"],
            spec["toDate"],
            spec["mode"],
            now,
            cr_name,
        ))
        record_id = row["id"]
        logger.info("Updated training record id=%d for CR '%s'", record_id, cr_name)
    else:
        cursor.execute("""
            INSERT INTO trainings
                (cr_name, namespace, training_name, duration, from_date, to_date, mode, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cr_name,
            namespace,
            spec["trainingName"],
            spec["duration"],
            spec["fromDate"],
            spec["toDate"],
            spec["mode"],
            now,
            now,
        ))
        record_id = cursor.lastrowid
        logger.info("Inserted training record id=%d for CR '%s'", record_id, cr_name)

    conn.commit()
    conn.close()
    return record_id


def delete_training(cr_name):
    conn = get_connection()
    conn.execute("DELETE FROM trainings WHERE cr_name = ?", (cr_name,))
    conn.commit()
    conn.close()
    logger.info("Deleted training record for CR '%s'", cr_name)


# ---------------------------------------------------------------------------
# kopf handlers
# ---------------------------------------------------------------------------

@kopf.on.startup()
def on_startup(settings: kopf.OperatorSettings, **kwargs):
    init_db()
    # Reduce noise for classroom demo
    settings.posting.level = logging.WARNING


@kopf.on.create("tektutor.org", "v1", "trainings")
def on_create(spec, name, namespace, patch, **kwargs):
    logger.info("CREATE event: %s/%s", namespace, name)
    record_id = upsert_training(name, namespace, spec)
    patch.status["state"] = "Synced"
    patch.status["message"] = f"Training '{spec['trainingName']}' added to calendar."
    patch.status["dbRecordId"] = record_id
    return {"message": "Training created and persisted."}


@kopf.on.update("tektutor.org", "v1", "trainings")
def on_update(spec, name, namespace, patch, **kwargs):
    logger.info("UPDATE event: %s/%s", namespace, name)
    record_id = upsert_training(name, namespace, spec)
    patch.status["state"] = "Synced"
    patch.status["message"] = f"Training '{spec['trainingName']}' updated in calendar."
    patch.status["dbRecordId"] = record_id
    return {"message": "Training updated and persisted."}


@kopf.on.delete("tektutor.org", "v1", "trainings")
def on_delete(name, namespace, **kwargs):
    logger.info("DELETE event: %s/%s", namespace, name)
    delete_training(name)
    return {"message": "Training removed from calendar."}
