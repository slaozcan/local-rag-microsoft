import sqlite3
import json

DB_NAME = "rag_demo.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS chunks")

    cursor.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_chunk(source, text, embedding):
    conn = get_connection()
    cursor = conn.cursor()

    embedding_json = json.dumps(embedding)

    cursor.execute(
        "INSERT INTO chunks (source, text, embedding) VALUES (?, ?, ?)",
        (source, text, embedding_json)
    )

    conn.commit()
    conn.close()


def get_all_chunks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, source, text, embedding FROM chunks")
    rows = cursor.fetchall()

    conn.close()

    chunks = []

    for row in rows:
        chunks.append({
            "id": row[0],
            "source": row[1],
            "text": row[2],
            "embedding": json.loads(row[3])
        })

    return chunks