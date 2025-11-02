import oracledb

def insert_evidence_file(connection, evidence_id, filename, file_type, uploaded_by, description, file_path):
    with open(file_path, 'rb') as file:
        file_data = file.read()
        file_size = len(file_data)

    sql = """
        INSERT INTO evidence_file
        (evidence_id, filename, file_type, file_size, file_content, uploaded_by, description)
        VALUES (:1, :2, :3, :4, :5, :6, :7)
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, (evidence_id, filename, file_type, file_size, file_data, uploaded_by, description))
            connection.commit()
            print(f"✅ File '{filename}' inserted successfully.")
    except Exception as e:
        print(f"❌ Error inserting file: {e}")
        raise


if __name__ == "__main__":
    USER = "SYSTEM"
    PASSWORD = "your-password"
    DSN = "localhost:1521/XE"

    try:
        conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
        print("✅ Connected to Oracle Database.")

        insert_evidence_file(
            connection=conn,
            evidence_id=1,
            filename="crime-scene-photo.jpg",
            file_type="image/jpeg",
            uploaded_by="STF102",
            description="Photo of the crime scene taken on 2025-09-14.",
            file_path=r"C:\Users\akrit\OneDrive\Desktop\PROJECTS\crime_record_app\assets\crime-scene-photo.jpg"
        )

    except Exception as err:
        print("❌ Connection failed:", err)
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔒 Connection closed.")
