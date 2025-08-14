import os
import psycopg


def test_can_query_chinook_tables():
    dsn = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5433/chinook")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM album;")
            albums = cur.fetchone()[0]
            assert albums > 0


