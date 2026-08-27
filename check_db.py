import sqlite3
import json

conn = sqlite3.connect("rag_demo.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tablolar:", cursor.fetchall())

cursor.execute("PRAGMA table_info(chunks);")
print("\nKolonlar:")

for col in cursor.fetchall():
    print(col)

cursor.execute("SELECT COUNT(*) FROM chunks;")
print("\nChunk sayısı:", cursor.fetchone()[0])

cursor.execute("SELECT id, source, text, embedding FROM chunks LIMIT 5;")
rows = cursor.fetchall()

for row in rows:
    embedding = json.loads(row[3])

    print("-" * 40)
    print("ID:", row[0])
    print("Kaynak:", row[1])
    print("Metin:", row[2])
    print("Embedding uzunluğu:", len(embedding))
    print("İlk 10 embedding değeri:", embedding[:10])

conn.close()