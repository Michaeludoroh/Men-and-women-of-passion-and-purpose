"""Apply missing schema columns for dev SQLite databases created via create_all()."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "site.db")


def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def add_column(cur, table, column, definition):
    if not column_exists(cur, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"Added {table}.{column}")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # prayer_request
    add_column(cur, "prayer_request", "phone", "VARCHAR(30)")
    add_column(cur, "prayer_request", "category", "VARCHAR(50) DEFAULT 'other'")
    add_column(cur, "prayer_request", "consent_follow_up", "BOOLEAN DEFAULT 0")
    add_column(cur, "prayer_request", "is_prayed_for", "BOOLEAN DEFAULT 0")
    add_column(cur, "prayer_request", "is_archived", "BOOLEAN DEFAULT 0")

    # donation
    add_column(cur, "donation", "user_id", "INTEGER")
    add_column(cur, "donation", "currency", "VARCHAR(10) DEFAULT 'NGN'")
    add_column(cur, "donation", "category", "VARCHAR(50) DEFAULT 'tithing'")
    add_column(cur, "donation", "payment_status", "VARCHAR(20) DEFAULT 'pending'")
    add_column(cur, "donation", "verified_at", "DATETIME")

    # leader
    add_column(cur, "leader", "org_level", "VARCHAR(50) DEFAULT 'coordinator'")
    add_column(cur, "leader", "video", "VARCHAR(300)")
    add_column(cur, "leader", "email", "VARCHAR(255)")
    add_column(cur, "leader", "phone", "VARCHAR(30)")
    add_column(cur, "leader", "department", "VARCHAR(120)")
    add_column(cur, "leader", "facebook_url", "VARCHAR(500)")
    add_column(cur, "leader", "instagram_url", "VARCHAR(500)")
    add_column(cur, "leader", "youtube_url", "VARCHAR(500)")
    add_column(cur, "leader", "twitter_url", "VARCHAR(500)")
    add_column(cur, "leader", "is_active", "BOOLEAN DEFAULT 1")
    add_column(cur, "leader", "updated_at", "DATETIME")

    # application
    add_column(cur, "application", "is_read", "BOOLEAN DEFAULT 0")

    # Stamp alembic to latest
    cur.execute("UPDATE alembic_version SET version_num = 'f3a6b8c0d2e5'")

    # gallery_image media fields
    add_column(cur, "gallery_image", "media_type", "VARCHAR(20) DEFAULT 'image'")
    add_column(cur, "gallery_image", "poster_path", "VARCHAR(300)")
    add_column(cur, "gallery_image", "display_order", "INTEGER DEFAULT 0")
    add_column(cur, "gallery_image", "is_published", "BOOLEAN DEFAULT 1")
    add_column(cur, "gallery_image", "updated_at", "DATETIME")
    # Backfill media_type for existing rows
    try:
        cur.execute("UPDATE gallery_image SET media_type = 'image' WHERE media_type IS NULL OR media_type = ''")
    except Exception:
        pass
    try:
        cur.execute("UPDATE gallery_image SET is_published = 1 WHERE is_published IS NULL")
    except Exception:
        pass
    try:
        cur.execute("UPDATE gallery_image SET display_order = 0 WHERE display_order IS NULL")
    except Exception:
        pass

    conn.commit()
    conn.close()
    print("Schema patch complete.")


if __name__ == "__main__":
    main()
