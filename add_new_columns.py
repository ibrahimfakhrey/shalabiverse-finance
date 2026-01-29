"""
Migration script: Add new columns to existing tables
- projects: phase, owner_capital
- expense_transactions: phase, is_direct_cost
- employees: contract_type
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'shalabi_verse.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    migrations = [
        # Projects table
        ("projects", "phase", "ALTER TABLE projects ADD COLUMN phase VARCHAR(20) DEFAULT 'building'"),
        ("projects", "owner_capital", "ALTER TABLE projects ADD COLUMN owner_capital NUMERIC(15,2) DEFAULT 0.00"),
        
        # Expense transactions table
        ("expense_transactions", "phase", "ALTER TABLE expense_transactions ADD COLUMN phase VARCHAR(20) DEFAULT 'operating'"),
        ("expense_transactions", "is_direct_cost", "ALTER TABLE expense_transactions ADD COLUMN is_direct_cost BOOLEAN DEFAULT 0"),
        
        # Employees table
        ("employees", "contract_type", "ALTER TABLE employees ADD COLUMN contract_type VARCHAR(20) DEFAULT 'full-time'"),
    ]
    
    for table, column, sql in migrations:
        # Check if column already exists
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        if column in existing_cols:
            print(f"  ⏭ {table}.{column} — already exists")
        else:
            cursor.execute(sql)
            print(f"  ✅ {table}.{column} — added")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    print("🔄 Running migration...\n")
    migrate()
