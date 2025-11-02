# check_tables.py
import oracledb

def list_all_tables():
    try:
        DB_USER = "system"
        DB_PASSWORD = "your-password"
        DB_DSN = "localhost:1521/XEPDB1"
        
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN
        )
        
        cursor = connection.cursor()
        
        # Get all tables owned by current user
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        print("📋 ALL TABLES IN DATABASE:")
        print("-" * 40)
        if tables:
            for table in tables:
                print(f"✅ {table[0]}")
        else:
            print("❌ No tables found!")
            
        # Also check case-insensitive search for your tables
        print("\n🔍 SEARCHING FOR CRIME-RELATED TABLES (case-insensitive):")
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE UPPER(table_name) LIKE '%CASE%' 
               OR UPPER(table_name) LIKE '%CRIME%'
               OR UPPER(table_name) LIKE '%EVIDENCE%'
               OR UPPER(table_name) LIKE '%COMPLAIN%'
            ORDER BY table_name
        """)
        
        crime_tables = cursor.fetchall()
        if crime_tables:
            for table in crime_tables:
                print(f"✅ {table[0]}")
        else:
            print("❌ No crime-related tables found!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_all_tables()