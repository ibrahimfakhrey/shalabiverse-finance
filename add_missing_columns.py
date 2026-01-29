#!/usr/bin/env python3
"""
Standalone script to add missing columns to existing tables.
Run this after updating the code to add the new columns.
Safe to run multiple times - checks if columns exist before adding.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'shalabi_verse.db')


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    changes = []

    # Projects: add phase
    if not column_exists(cursor, 'projects', 'phase'):
        cursor.execute("ALTER TABLE projects ADD COLUMN phase VARCHAR(20) DEFAULT 'building'")
        changes.append("projects.phase")
    
    # Projects: add owner_capital
    if not column_exists(cursor, 'projects', 'owner_capital'):
        cursor.execute("ALTER TABLE projects ADD COLUMN owner_capital NUMERIC(15,2) DEFAULT 0.00")
        changes.append("projects.owner_capital")
    
    # Expense transactions: add phase
    if not column_exists(cursor, 'expense_transactions', 'phase'):
        cursor.execute("ALTER TABLE expense_transactions ADD COLUMN phase VARCHAR(20) DEFAULT 'operating'")
        changes.append("expense_transactions.phase")
    
    # Expense transactions: add is_direct_cost
    if not column_exists(cursor, 'expense_transactions', 'is_direct_cost'):
        cursor.execute("ALTER TABLE expense_transactions ADD COLUMN is_direct_cost BOOLEAN DEFAULT 0")
        changes.append("expense_transactions.is_direct_cost")
    
    # Employees: add contract_type
    if not column_exists(cursor, 'employees', 'contract_type'):
        cursor.execute("ALTER TABLE employees ADD COLUMN contract_type VARCHAR(20) DEFAULT 'full-time'")
        changes.append("employees.contract_type")

    conn.commit()
    conn.close()

    if changes:
        print(f"Added {len(changes)} columns: {', '.join(changes)}")
    else:
        print("All columns already exist. No changes needed.")


if __name__ == '__main__':
    main()
