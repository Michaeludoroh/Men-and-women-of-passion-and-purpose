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


def gallery_image_path_nullable(cur):
    """SQLite cannot ALTER COLUMN nullability — rebuild table when needed."""
    if not table_exists(cur, "gallery_image"):
        return
    cur.execute("PRAGMA table_info(gallery_image)")
    cols = cur.fetchall()
    image_path_col = next((c for c in cols if c[1] == "image_path"), None)
    if not image_path_col or image_path_col[3] == 0:  # notnull == 0 means nullable
        return

    print("Rebuilding gallery_image to allow nullable image_path for external videos...")
    cur.execute("PRAGMA foreign_keys=OFF")
    cur.execute(
        """
        CREATE TABLE gallery_image_new (
            id INTEGER NOT NULL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL DEFAULT 'events',
            event_name VARCHAR(200),
            image_path VARCHAR(300),
            media_type VARCHAR(20) NOT NULL DEFAULT 'image',
            poster_path VARCHAR(300),
            external_url VARCHAR(500),
            embed_url VARCHAR(500),
            provider VARCHAR(40),
            provider_video_id VARCHAR(120),
            thumbnail_url VARCHAR(500),
            duration_seconds FLOAT,
            mime_type VARCHAR(80),
            file_size INTEGER,
            display_order INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT 0,
            is_published BOOLEAN DEFAULT 1,
            created_at DATETIME,
            updated_at DATETIME
        )
        """
    )
    # Copy overlapping columns dynamically
    cur.execute("PRAGMA table_info(gallery_image)")
    old_names = [c[1] for c in cur.fetchall()]
    new_names = [
        "id", "title", "description", "category", "event_name", "image_path",
        "media_type", "poster_path", "external_url", "embed_url", "provider",
        "provider_video_id", "thumbnail_url", "duration_seconds", "mime_type",
        "file_size", "display_order", "is_featured", "is_published",
        "created_at", "updated_at",
    ]
    shared = [n for n in new_names if n in old_names]
    cols_sql = ", ".join(shared)
    cur.execute(
        f"INSERT INTO gallery_image_new ({cols_sql}) SELECT {cols_sql} FROM gallery_image"
    )
    cur.execute("DROP TABLE gallery_image")
    cur.execute("ALTER TABLE gallery_image_new RENAME TO gallery_image")
    cur.execute("PRAGMA foreign_keys=ON")
    print("gallery_image.image_path is now nullable.")


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
    cur.execute("UPDATE alembic_version SET version_num = 'h5c8d0e2f4a7'")

    # gallery_image media fields
    add_column(cur, "gallery_image", "media_type", "VARCHAR(20) DEFAULT 'image'")
    add_column(cur, "gallery_image", "poster_path", "VARCHAR(300)")
    add_column(cur, "gallery_image", "display_order", "INTEGER DEFAULT 0")
    add_column(cur, "gallery_image", "is_published", "BOOLEAN DEFAULT 1")
    add_column(cur, "gallery_image", "updated_at", "DATETIME")
    add_column(cur, "gallery_image", "event_name", "VARCHAR(200)")
    add_column(cur, "gallery_image", "external_url", "VARCHAR(500)")
    add_column(cur, "gallery_image", "embed_url", "VARCHAR(500)")
    add_column(cur, "gallery_image", "provider", "VARCHAR(40)")
    add_column(cur, "gallery_image", "provider_video_id", "VARCHAR(120)")
    add_column(cur, "gallery_image", "thumbnail_url", "VARCHAR(500)")
    add_column(cur, "gallery_image", "duration_seconds", "FLOAT")
    add_column(cur, "gallery_image", "mime_type", "VARCHAR(80)")
    add_column(cur, "gallery_image", "file_size", "INTEGER")
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

    gallery_image_path_nullable(cur)

    # sermon multimedia fields (independent from gallery)
    add_column(cur, "sermon", "media_type", "VARCHAR(20) DEFAULT 'image'")
    add_column(cur, "sermon", "media_path", "VARCHAR(300)")
    add_column(cur, "sermon", "poster_path", "VARCHAR(300)")
    add_column(cur, "sermon", "external_url", "VARCHAR(500)")
    add_column(cur, "sermon", "embed_url", "VARCHAR(500)")
    add_column(cur, "sermon", "provider", "VARCHAR(40)")
    add_column(cur, "sermon", "provider_video_id", "VARCHAR(120)")
    add_column(cur, "sermon", "thumbnail_url", "VARCHAR(500)")
    add_column(cur, "sermon", "duration_seconds", "FLOAT")
    add_column(cur, "sermon", "mime_type", "VARCHAR(80)")
    add_column(cur, "sermon", "file_size", "INTEGER")
    add_column(cur, "sermon", "updated_at", "DATETIME")
    try:
        cur.execute("UPDATE sermon SET media_type = 'image' WHERE media_type IS NULL OR media_type = ''")
    except Exception:
        pass

    conn.commit()
    conn.close()
    print("Schema patch complete.")


if __name__ == "__main__":
    main()
