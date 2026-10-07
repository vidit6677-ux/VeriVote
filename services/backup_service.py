import os
import sqlite3
from datetime import datetime, timezone

from config import DATABASE_PATH, LEVEL_DATABASE_PATHS


def create_database_backup(destination_dir):
    """Create consistent SQLite backups for the primary and level stores."""

    os.makedirs(destination_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sources = {"verivote": DATABASE_PATH, **{
        level.lower(): path for level, path in LEVEL_DATABASE_PATHS.items()
    }}
    created = []

    for name, source in sources.items():
        if not os.path.exists(source):
            continue

        destination = os.path.join(destination_dir, f"{name}-{stamp}.db")
        source_connection = sqlite3.connect(source)
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
            created.append(destination)
        finally:
            destination_connection.close()
            source_connection.close()

    return created
