from pathlib import Path
import sqlite3
import sys
import os

# Determine if running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # If frozen, the executable is inside a directory (e.g. /Release/smart_pricing/smart_pricing.exe).
    # We want the database to be in a 'data' folder at the Release root (/Release/data),
    # so we go up one level from the executable's directory.
    base_dir = Path(sys.executable).parent.parent
else:
    # If running normally (dev), use the backend directory
    base_dir = Path(__file__).parent

DB_DIR = base_dir / "data"
DB_FILE = DB_DIR / "Quetung.db"

# Ensure the directory exists (only critical if we were creating a new DB,
# but good practice for robustness)
if not DB_DIR.exists():
    # In a frozen app, we might expect the user to provide the 'data' folder.
    # However, if it doesn't exist, we can't do much but print.
    pass

print("USING DB FILE:", DB_FILE.resolve())

def get_conn():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn
