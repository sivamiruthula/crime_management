"""
DATA POPULATOR for Existing Oracle Database Schema
Generates realistic demo crime data matching your existing tables
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import oracledb


class CrimeDataPopulator:
    def __init__(self, num_cases=1000):
        self.num_cases = num_cases
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2024, 12, 31)
        
        # Will store IDs for foreign key relationships
        self.case_ids = []
        self.complainant_ids = []
        self.crime_type_ids = []
        self.staff_ids = []
        self.location_ids = []

        
    def get_connection(self, user, password, host='localhost', port=1521, service_name='XE'):
        """Establish Oracle database connection"""
        try:
            dsn = f"{host}:{port}/{service_name}"
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            print("✓ Connected to Oracle database")
            print(f"  Database version: {connection.version}")
            return connection
        except oracledb.Error as error:
            print(f"✗ Connection error: {error}")
            raise
    
    def fetch_existing_data(self, connection):
        """Fetch existing reference data (crime types, staff, etc.)"""
        cursor = connection.cursor()
        
        print("\nFetching existing reference data...")
        
        # Get crime types
        cursor.execute("SELECT CRIME_TYPE_ID, CODE, DESCRIPTION, SEVERITY_LEVEL FROM CRIME_TYPE WHERE IS_ACTIVE = 1")
        crime_types = cursor.fetchall()
        self.crime_type_ids = [{'id': ct[0], 'code': ct[1], 'desc': ct[2], 'severity': ct[3]} for ct in crime_types]
        print(f"  ✓ Found {len(self.crime_type_ids)} crime types")
        
        # If no crime types exist, create some
        if not self.crime_type_ids:
            print("  ! No crime types found. Creating default crime types...")
            self.create_crime_types(connection)
            cursor.execute("SELECT CRIME_TYPE_ID, CODE, DESCRIPTION, SEVERITY_LEVEL FROM CRIME_TYPE WHERE IS_ACTIVE = 1")
            crime_types = cursor.fetchall()
            self.crime_type_ids = [{'id': ct[0], 'code': ct[1], 'desc': ct[2], 'severity': ct[3]} for ct in crime_types]
        
        # Get staff IDs (for assignments)
        cursor.execute("SELECT STAFFID FROM USERLOGIN WHERE IS_ACTIVE = 1")
        staff = cursor.fetchall()
        self.staff_ids = [s[0] for s in staff]
        print(f"  ✓ Found {len(self.staff_ids)} active staff")
        
        if not self.staff_ids:
            print("  ! No active staff found. Creating demo staff...")
            self.create_demo_staff(connection)
            cursor.execute("SELECT STAFFID FROM USERLOGIN WHERE IS_ACTIVE = 1")
            staff = cursor.fetchall()
            self.staff_ids = [s[0] for s in staff]

        # Get location IDs
        cursor.execute("SELECT LOCATION_ID FROM LOCATION")
        locations = cursor.fetchall()
        self.location_ids = [l[0] for l in locations]
        print(f"  ✓ Found {len(self.location_ids)} locations")

        # If none exist, create demo locations
        if not self.location_ids:
            print("  ! No locations found. Creating demo locations...")
            self.create_demo_locations(connection)
            cursor.execute("SELECT LOCATION_ID FROM LOCATION")
            locations = cursor.fetchall()
            self.location_ids = [l[0] for l in locations]

    
    def create_crime_types(self, connection):
        """Create default crime types if none exist"""
        cursor = connection.cursor()
        
        crime_types = [
            ('TH', 'Theft', 'Moderate'),
            ('AS', 'Assault', 'Serious'),
            ('BR', 'Burglary', 'Serious'),
            ('VT', 'Vehicle Theft', 'Moderate'),
            ('DR', 'Drug Related', 'Critical'),
            ('FR', 'Fraud', 'Moderate'),
            ('VN', 'Vandalism', 'Minor'),
            ('RB', 'Robbery', 'Critical'),
            ('HM', 'Homicide', 'Critical'),
            ('CY', 'Cybercrime', 'Serious')
        ]
        
        for code, desc, severity in crime_types:
            cursor.execute("""
                INSERT INTO CRIME_TYPE (CODE, DESCRIPTION, SEVERITY_LEVEL, IS_ACTIVE, CREATED_AT)
                VALUES (:1, :2, :3, 1, SYSTIMESTAMP)
            """, (code, desc, severity))
        
        connection.commit()
        print(f"    ✓ Created {len(crime_types)} crime types")
    
    def create_demo_staff(self, connection):
        """Create demo staff users if none exist"""
        cursor = connection.cursor()
        
        staff_data = [
            ('OFF001', 'Kumar', 'Singh', 'Police Officer', 'North'),
            ('OFF002', 'Priya', 'Sharma', 'Detective', 'South'),
            ('OFF003', 'Raj', 'Patel', 'Inspector', 'Central'),
            ('OFF004', 'Lakshmi', 'Reddy', 'Constable', 'East'),
            ('OFF005', 'Arun', 'Iyer', 'Senior Inspector', 'West')
        ]
        
        for staff_id, surname, othername, rank, dept in staff_data:
            cursor.execute("""
                INSERT INTO USERLOGIN (STAFFID, SURNAME, OTHERNAMES, EMAIL, PHONE, ROLE, 
                                      PASSWORD, DEPARTMENT, RANK_POSITION, IS_ACTIVE, CREATED_AT)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, 1, SYSTIMESTAMP)
            """, (staff_id, surname, othername, f'{staff_id.lower()}@police.gov', 
                  f'+91{random.randint(7000000000, 9999999999)}', 'Officer', 
                  'demo123', dept, rank))
        
        connection.commit()
        print(f"    ✓ Created {len(staff_data)} demo staff")
    
    def create_demo_locations(self, connection):
        cursor = connection.cursor()

        demo_locations = [
            ("Downtown Junction", "Central", 13.0827, 80.2707),
            ("Marina Beach Road", "South", 13.0404, 80.2824),
            ("T Nagar Market", "West", 13.0418, 80.2337),
            ("IT Corridor OMR", "East", 12.9716, 80.2215),
            ("Ambattur Zone", "North", 13.1134, 80.1603)
        ]

        for name, district, lat, lon in demo_locations:
            cursor.execute("""
                INSERT INTO LOCATION (LOCATION_NAME, DISTRICT, LATITUDE, LONGITUDE, CREATED_AT)
                VALUES (:1, :2, :3, :4, SYSTIMESTAMP)
            """, (name, district, lat, lon))

        connection.commit()
        print(f"    ✓ Created {len(demo_locations)} demo locations")


    def generate_timestamp(self):
        """Generate realistic timestamp"""
        days = (self.end_date - self.start_date).days
        random_date = self.start_date + timedelta(days=random.randint(0, days))
        hour_weights = [1, 1, 1, 1, 2, 3, 4, 5, 4, 3, 3, 4, 
                       5, 4, 4, 5, 6, 7, 8, 9, 8, 7, 5, 3]
        hour = random.choices(range(24), weights=hour_weights)[0]
        return random_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    
    def populate_complainants(self, connection, count=None):
        if count is None:
            count = self.num_cases
        """Create complainant records"""
        cursor = connection.cursor()
        print(f"\nGenerating {count} complainants...")
        
        first_names = ['Raj', 'Priya', 'Kumar', 'Lakshmi', 'Arun', 'Deepa', 'Vijay', 'Meena', 
                      'Ravi', 'Anjali', 'Suresh', 'Divya', 'Karthik', 'Kavya']
        last_names = ['Kumar', 'Singh', 'Patel', 'Sharma', 'Reddy', 'Iyer', 'Nair', 'Das',
                     'Gupta', 'Verma', 'Rao', 'Mehta']
        
        regions = ['Central', 'North', 'South', 'East', 'West']
        districts = ['Downtown', 'Parkside', 'Coastal Zone', 'Market District', 'University Area']
        locations = ['Street A', 'Street B', 'Avenue C', 'Road D', 'Colony E']
        
        complainants_created = 0
        for i in range(count):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            cursor.execute("""
                INSERT INTO COMPLAINANT (NAME, AGE, GENDER, OCCUPATION, PHONE, EMAIL,
                                        ADDRESS, REGION, DISTRICT, LOCATION, CREATED_AT)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, SYSTIMESTAMP)
            """, (name, 
                  random.randint(18, 75),
                  random.choice(['Male', 'Female', 'Other']),
                  random.choice(['Business', 'Service', 'Student', 'Professional', 'Other']),
                  f'+91{random.randint(7000000000, 9999999999)}',
                  f'complainant{i}@example.com',
                  f'{random.randint(1, 999)} {random.choice(locations)}',
                  random.choice(regions),
                  random.choice(districts),
                  random.choice(locations)))
            complainants_created += 1
            
            if (i + 1) % 100 == 0:
                connection.commit()
                print(f"  Created {i + 1}/{count} complainants...")
        
        connection.commit()
        
        # Fetch created complainant IDs
        cursor.execute("SELECT COMPLAINANT_ID FROM COMPLAINANT")
        self.complainant_ids = [row[0] for row in cursor.fetchall()]
        print(f"✓ Created {complainants_created} complainants")
    
    def populate_cases(self, connection,count=None):
        if count is None:
            count = self.num_cases
        """Create case records"""
        cursor = connection.cursor()
        print(f"\nGenerating {self.num_cases} cases...")
        
        priorities = ['Low', 'Medium', 'High', 'Critical']
        
        statuses = [
    "Reported",
    "Assigned",
    "Under Investigation",
    "Pending",
    "Closed",
    "Cold Case"
]


        cases_created = 0
        for i in range(self.num_cases):
            crime_type = random.choice(self.crime_type_ids)
            complainant_id = random.choice(self.complainant_ids)
            staff_id = random.choice(self.staff_ids) if self.staff_ids else None
            incident_time = self.generate_timestamp()
            
            location_id = random.choice(self.location_ids)

            
            cursor.execute("""
                INSERT INTO CASE_TABLE (COMPLAINANT_ID, CRIME_TYPE_ID, CASE_TITLE, 
                                       INCIDENT_DATETIME, INCIDENT_LOCATION, DESCRIPTION,
                                       PRIORITY, STATUS, NCO_STAFFID, CID_OFFICER_STAFFID,
                                       ASSIGNED_AT, CREATED_AT, UPDATED_AT)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, SYSTIMESTAMP, SYSTIMESTAMP)
            """, (complainant_id,
                  crime_type['id'],
                  f"{crime_type['desc']} Case #{i+1}",
                  incident_time,
                  location_id,
                  f"Reported incident of {crime_type['desc'].lower()}",
                  random.choice(priorities),
                  random.choice(statuses),
                  staff_id,
                  staff_id,
                  incident_time + timedelta(hours=random.randint(1, 48))))
            
            cases_created += 1
            
            if (i + 1) % 200 == 0:
                connection.commit()
                print(f"  Created {i + 1}/{self.num_cases} cases...")
        
        connection.commit()
        
        # Fetch created case IDs
        cursor.execute("SELECT CASE_ID FROM CASE_TABLE")
        self.case_ids = [row[0] for row in cursor.fetchall()]
        print(f"✓ Created {cases_created} cases")
    
    def populate_investigations(self, connection):
        """Create investigation records (60% of cases)"""
        cursor = connection.cursor()
        print("\nGenerating investigation records...")
        
        investigation_types = ['Initial', 'Follow-up', 'Evidence Collection', 'Interview', 'Final Report']
        inv_count = 0
        
        for case_id in self.case_ids:
            if random.random() < 0.6:  # 60% of cases
                num_investigations = random.randint(1, 4)
                for j in range(num_investigations):
                    officer_id = random.choice(self.staff_ids) if self.staff_ids else None
                    
                    cursor.execute("""
                        INSERT INTO INVESTIGATION (CASE_ID, CID_OFFICER_STAFFID, INVESTIGATION_TYPE,
                                                  INVESTIGATION_NOTE, FINDINGS, EVIDENCE_COLLECTED,
                                                  NEXT_STEPS, INVESTIGATION_DATE, CREATED_AT)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, SYSTIMESTAMP)
                    """, (case_id,
                          officer_id,
                          random.choice(investigation_types),
                          f"Investigation notes for case {case_id}",
                          f"Findings from {random.choice(investigation_types).lower()}",
                          random.choice(['Yes', 'No', 'Partial']),
                          'Continue investigation' if random.random() < 0.7 else 'Close case',
                          datetime.now() - timedelta(days=random.randint(1, 60))))
                    inv_count += 1
        
        connection.commit()
        print(f"✓ Created {inv_count} investigation records")
    
    def populate_evidence(self, connection):
        """Create evidence records (50% of cases)"""
        cursor = connection.cursor()
        print("\nGenerating evidence records...")
        
        evidence_types = [
    "Physical",
    "Digital",
    "Document",
    "Biological",
    "Photographic",
    "Video",
    "Audio",
    "Other"
]

        storage_locations = ['Evidence Room A', 'Evidence Room B', 'Digital Storage', 'Forensic Lab']
        statuses = [
    "Collected",
    "In Analysis",
    "Analyzed",
    "Returned",
    "Destroyed",
    "Missing"
]

        
        ev_count = 0
        for case_id in self.case_ids:
            if random.random() < 0.5:  # 50% of cases
                num_evidence = random.randint(1, 4)
                for j in range(num_evidence):
                    collector_id = random.choice(self.staff_ids) if self.staff_ids else None
                    
                    cursor.execute("""
                        INSERT INTO EVIDENCE (CASE_ID, EVIDENCE_TYPE, DESCRIPTION, COLLECTED_BY,
                                             COLLECTION_DATE, STORAGE_LOCATION, CHAIN_OF_CUSTODY,
                                             STATUS, CREATED_AT, UPDATED_AT)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, SYSTIMESTAMP, SYSTIMESTAMP)
                    """, (case_id,
                          random.choice(evidence_types),
                          f"Evidence item for case {case_id}",
                          collector_id,
                          datetime.now() - timedelta(days=random.randint(1, 30)),
                          random.choice(storage_locations),
                          f"Collected by Officer {collector_id}",
                          random.choice(statuses)))
                    ev_count += 1
        
        connection.commit()
        print(f"✓ Created {ev_count} evidence records")
    
    def populate_suspects(self, connection):
        """Create suspect records (40% of cases)"""
        cursor = connection.cursor()
        print("\nGenerating suspect records...")
        
        statuses = [
    "Person of Interest",
    "Suspect",
    "Arrested",
    "Charged",
    "Cleared",
    "Wanted"
]

        
        sus_count = 0
        for case_id in self.case_ids:
            if random.random() < 0.4:  # 40% of cases
                num_suspects = random.randint(1, 3)
                for j in range(num_suspects):
                    cursor.execute("""
                        INSERT INTO SUSPECT (CASE_ID, NAME, ALIAS, AGE, GENDER, ADDRESS,
                                            PHONE, DESCRIPTION, CRIMINAL_HISTORY, STATUS,
                                            ADDED_BY, CREATED_AT, UPDATED_AT)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, SYSTIMESTAMP, SYSTIMESTAMP)
                    """, (case_id,
                          f"Suspect {random.randint(1, 999)}",
                          f"Alias{random.randint(1, 999)}" if random.random() < 0.3 else None,
                          random.randint(18, 65),
                          random.choice(['Male', 'Female', 'Other']),
                          f"Address {random.randint(1, 999)}",
                          f'+91{random.randint(7000000000, 9999999999)}' if random.random() < 0.5 else None,
                          'Physical description',
                          'Prior offenses' if random.random() < 0.4 else 'No record',
                          random.choice(statuses),
                          random.choice(self.staff_ids) if self.staff_ids else None))
                    sus_count += 1
        
        connection.commit()
        print(f"✓ Created {sus_count} suspect records")
    
    def populate_witnesses(self, connection):
        cursor = connection.cursor()
        print("\nGenerating witness records...")

        witness_types = ['Witness', 'Victim', 'Expert', 'Character']
        reliability = ['High', 'Medium', 'Low', 'Unknown']

        wit_count = 0
        for case_id in self.case_ids:
            if random.random() < 0.55:
                num_witnesses = random.randint(1, 4)
                for j in range(num_witnesses):
                    statement_date = datetime.now() - timedelta(days=random.randint(1, 45))

                    cursor.execute("""
                        INSERT INTO WITNESS (CASE_ID, NAME, AGE, GENDER, CONTACT_INFO,
                                            ADDRESS, STATEMENT, STATEMENT_DATE, STATEMENT_TAKEN_BY,
                                            WITNESS_TYPE, RELIABILITY_RATING, CREATED_AT, UPDATED_AT)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, SYSTIMESTAMP, SYSTIMESTAMP)
                    """, (
                        case_id,
                        f"Witness {random.randint(1, 999)}",
                        random.randint(18, 75),
                        random.choice(['Male', 'Female', 'Other']),
                        f'+91{random.randint(7000000000, 9999999999)}',
                        f"Witness Address {random.randint(1, 999)}",
                        f"Witness statement for case {case_id}",
                        statement_date,
                        random.choice(self.staff_ids),   # NO None!
                        random.choice(witness_types),
                        random.choice(reliability)
                    ))
                    wit_count += 1

        connection.commit()
        print(f"✓ Created {wit_count} witness records")

    
    def verify_data(self, connection):
        """Verify inserted data"""
        cursor = connection.cursor()
        
        print("\n" + "=" * 60)
        print("DATA VERIFICATION")
        print("=" * 60)
        
        tables = [
            'CRIME_TYPE', 'COMPLAINANT', 'CASE_TABLE', 
            'INVESTIGATION', 'EVIDENCE', 'SUSPECT', 'WITNESS'
        ]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
            except:
                print(f"  {table}: Unable to query")
        
        print("=" * 60)
    
    def run(self, user, password, host='localhost', port=1521, service_name='XE'):
        """Main execution method"""
        print("=" * 60)
        print("CRIME DATABASE POPULATOR")
        print("=" * 60)
        
        try:
            # Connect to database
            connection = self.get_connection(user, password, host, port, service_name)
            
            # Fetch existing reference data
            self.fetch_existing_data(connection)
            
            # Populate tables
            self.populate_complainants(connection, count=20)
            self.populate_cases(connection, count=20)
            self.populate_investigations(connection)
            self.populate_evidence(connection)
            self.populate_suspects(connection)
            self.populate_witnesses(connection)
            
            # Verify data
            self.verify_data(connection)
            
            print("\n✓ Data population complete!")
            
            connection.close()
            print("✓ Database connection closed")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            raise


if __name__ == "__main__":
    # CONFIGURATION - UPDATE THESE VALUES
    DB_USER = "police_system"        # Your Oracle username
    DB_PASSWORD = "Police123#"    # Your Oracle password
    DB_HOST = "hemajelli"            # Usually localhost
    DB_PORT = 1521                   # Default Oracle port
    DB_SERVICE = "xepdb1"                # Your service name (XE, XEPDB1, ORCL, etc.)
    NUM_CASES = 300                # Number of cases to generate
    
    # Run the populator
    populator = CrimeDataPopulator(num_cases=NUM_CASES)
    populator.run(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE)