"""Add pin_hash column to projects and set default PIN 1234"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'shalabi_verse.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add column
    cursor.execute("PRAGMA table_info(projects)")
    cols = [row[1] for row in cursor.fetchall()]
    
    if 'pin_hash' not in cols:
        cursor.execute("ALTER TABLE projects ADD COLUMN pin_hash VARCHAR(256)")
        print("✅ Added pin_hash column")
    else:
        print("⏭ pin_hash already exists")
    
    # Set default PIN 1234 for all projects
    default_pin = generate_password_hash('1234', method='pbkdf2:sha256')
    cursor.execute("UPDATE projects SET pin_hash = ? WHERE pin_hash IS NULL", (default_pin,))
    print(f"✅ Set default PIN (1234) for {cursor.rowcount} projects")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("🔄 Adding PIN to projects...\n")
    migrate()
    print("\n✅ Done!")
