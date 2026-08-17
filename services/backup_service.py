import os
import shutil
import sqlite3
from datetime import datetime

# =====================================================================
# Database Backup & Restore
#
# Uses SQLite's own online Backup API (Connection.backup()) rather than
# a plain file copy - this is safe even while the app has the database
# open elsewhere, since SQLite handles the read consistency itself.
# A plain file copy can capture a half-written page if something is
# mid-write at that exact moment; the backup API cannot.
# =====================================================================

DB_PATH = "database/inventory.db"
BACKUP_FOLDER = "backups"
KEEP_BACKUPS = 14   # how many recent backups to retain before pruning


def create_backup():
    """
    Creates a timestamped backup of the live database, then prunes old
    backups beyond KEEP_BACKUPS. Returns the path to the new backup.
    Raises on failure - callers decide whether that should be silent
    (auto-backup on close) or shown to the user (manual "Backup Now").
    """
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_path = os.path.join(BACKUP_FOLDER, f"inventory_backup_{timestamp}.db")

    source_conn = sqlite3.connect(DB_PATH)
    dest_conn = sqlite3.connect(dest_path)

    try:
        with dest_conn:
            source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    _cleanup_old_backups()

    return dest_path


def list_backups():
    """
    Returns backups newest-first as a list of dicts:
    {"path", "filename", "modified" (datetime), "size_bytes"}
    """
    if not os.path.isdir(BACKUP_FOLDER):
        return []

    backups = []
    for fname in os.listdir(BACKUP_FOLDER):
        if not fname.endswith(".db"):
            continue
        full_path = os.path.join(BACKUP_FOLDER, fname)
        backups.append({
            "path": full_path,
            "filename": fname,
            "modified": datetime.fromtimestamp(os.path.getmtime(full_path)),
            "size_bytes": os.path.getsize(full_path),
        })

    backups.sort(key=lambda b: b["modified"], reverse=True)
    return backups


def _cleanup_old_backups():
    backups = list_backups()
    for backup in backups[KEEP_BACKUPS:]:
        try:
            os.remove(backup["path"])
        except OSError:
            pass  # never let cleanup failure block a successful backup


def restore_backup(backup_path):
    """
    Overwrites the live database with the chosen backup file.
    The app must be restarted afterward - any already-open database
    connections elsewhere in the running app won't see the swap.
    """
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Safety copy of the current (about-to-be-replaced) database, in
    # case the wrong backup was picked - this can be recovered from
    # backups/_before_restore.db.
    if os.path.isfile(DB_PATH):
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        shutil.copy2(DB_PATH, os.path.join(BACKUP_FOLDER, "_before_restore.db"))

    shutil.copy2(backup_path, DB_PATH)


def format_size(size_bytes):
    """Human-readable file size, e.g. 482.3 KB / 1.2 MB."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"