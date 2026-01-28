#!/usr/bin/env python3
"""
Local development server for Shalabi Verse Financial System
"""
from app import create_app

if __name__ == '__main__':
    app = create_app('development')
    print("\n" + "="*60)
    print("Shalabi Verse Financial Management System")
    print("Starting development server...")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=8080, debug=True)
