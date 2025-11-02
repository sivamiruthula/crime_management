import oracledb

def test_connection():
    try:
        # Connection parameters
        DB_USER = "system"
        DB_PASSWORD = "your-password"
        DB_DSN = "localhost:1521/XEPDB1"
        
        print("🔍 Testing Oracle Database Connection...")
        print(f"User: {DB_USER}")
        print(f"DSN: {DB_DSN}")
        
        # Attempt connection
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN
        )
        
        print("✅ CONNECTION SUCCESSFUL!")
        
        # Test basic query
        cursor = connection.cursor()
        cursor.execute("SELECT 'Hello from Oracle!' FROM DUAL")
        result = cursor.fetchone()
        print(f"Query test: {result[0]}")
        
        # Get database version
        cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
        version = cursor.fetchone()
        print(f"Database: {version[0]}")
        
        # Check current user
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()
        print(f"Connected as: {current_user[0]}")
        
        cursor.close()
        connection.close()
        print("🔒 Connection closed.")
        
        return True
        
    except oracledb.Error as e:
        print(f"❌ CONNECTION FAILED: {e}")
        return False

if __name__ == "__main__":
    test_connection()