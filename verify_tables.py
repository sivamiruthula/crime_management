import oracledb

def verify_database_setup():
    USER = "system"
    PASSWORD = "your-password"
    DSN = "localhost:1521/XEPDB1"
    
    try:
        conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
        cursor = conn.cursor()
        
        # Check critical tables
        tables_to_check = [
            'CASE_TABLE', 'COMPLAINANT', 'CRIME_TYPE', 'USERLOGIN',
            'INVESTIGATION', 'CASE_ASSIGNMENT_HISTORY', 'EVIDENCE'
        ]
        
        print("🔍 Checking database tables...")
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} rows")
            except Exception as e:
                print(f"❌ {table}: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    verify_database_setup()