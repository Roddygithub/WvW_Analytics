#!/usr/bin/env python3
"""
Script to run database migration on remote server.
Connects directly to PostgreSQL and executes the migration SQL.
"""

import psycopg2
import sys
from pathlib import Path

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "wvw_analytics"
DB_USER = "wvw_user"
DB_PASSWORD = "wvw_secure_password_2024"

def run_migration():
    """Execute the database migration."""
    
    # Read the migration SQL file
    sql_file = Path(__file__).parent / "migrate_db_schema.sql"
    
    if not sql_file.exists():
        print(f"❌ Error: Migration file not found: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r') as f:
        migration_sql = f.read()
    
    print("=== WvW Analytics Database Migration ===")
    print(f"Connecting to database: {DB_NAME}@{DB_HOST}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✓ Connected to database")
        print()
        print("📋 Executing migration SQL...")
        
        # Execute the migration
        cursor.execute(migration_sql)
        
        # Commit the transaction
        conn.commit()
        
        print("✓ Migration executed successfully")
        print()
        
        # Verify columns were added
        print("🔍 Verifying new columns...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_stats' 
              AND column_name IN ('barrier_absorbed', 'stab_out_ms', 'detected_role')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        if len(columns) == 3:
            print("✓ Verification successful - all key columns present:")
            for col in columns:
                print(f"  - {col[0]}")
        else:
            print(f"⚠ Warning: Expected 3 columns, found {len(columns)}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=== Migration Complete ===")
        print("✅ Database schema updated successfully!")
        print()
        print("Next steps:")
        print("  sudo systemctl restart wvw-analytics")
        print("  sudo systemctl status wvw-analytics")
        
        return 0
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())
