import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "extractiq.db"


def create_database():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            page_count INTEGER,
            extracted_text TEXT,
            extracted_information TEXT,
            stored_filename TEXT,
            created_at TEXT NOT NULL DEFAULT ''
        )
    """)
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(documents)")}
    migrations = {
        "extracted_information": "ALTER TABLE documents ADD COLUMN extracted_information TEXT",
        "stored_filename": "ALTER TABLE documents ADD COLUMN stored_filename TEXT",
        "created_at": "ALTER TABLE documents ADD COLUMN created_at TEXT NOT NULL DEFAULT ''",
    }
    for column, statement in migrations.items():
        if column not in columns:
            cursor.execute(statement)
    connection.commit()
    connection.close()


def save_document(filename, page_count, extracted_text, information, stored_filename):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents
                (filename, page_count, extracted_text, extracted_information,
                 stored_filename, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                page_count,
                extracted_text,
                json.dumps(information),
                stored_filename,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cursor.lastrowid


def list_documents():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, filename, page_count, extracted_information, created_at
            FROM documents ORDER BY id DESC
            """
        ).fetchall()
    documents = []
    for row in rows:
        document = dict(row)
        document["extracted_information"] = json.loads(
            document["extracted_information"] or "{}"
        )
        documents.append(document)
    return documents


def get_document(document_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    if row is None:
        return None
    document = dict(row)
    document["extracted_information"] = json.loads(
        document["extracted_information"] or "{}"
    )
    return document


def delete_document(document_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM documents WHERE id = ?", (document_id,)
        )
        return cursor.rowcount > 0