"""
DATA PREPROCESSOR & FEATURE ENGINEERING MODULE
Cleans data and creates features for ML models
"""
import oracledb
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime
import os

class CrimeDataPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
    
    def connect_db(self, user, password, dsn):
        """
        Connect to Oracle DB
        """
        self.conn = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        print("✓ Connected to Oracle database")

        
    def load_data(self):
        """Load data directly from Oracle DB"""
        print("Loading datasets from database...")

        query = lambda q: pd.read_sql(q, con=self.conn)

        self.df_crimes = query("""
SELECT
    c.case_id,
    c.incident_datetime AS "incident_datetime",
    c.incident_location,
    l.latitude,
    l.longitude,
    l.district,
    ct.code AS crime_type_code,
    ct.description AS crime_type_description,
    ct.severity_level,
    comp.age AS complainant_age,
    c.priority,
    c.status
FROM CASE_TABLE c
LEFT JOIN LOCATION l ON c.incident_location = l.location_id
LEFT JOIN CRIME_TYPE ct ON c.crime_type_id = ct.crime_type_id
LEFT JOIN COMPLAINANT comp ON c.COMPLAINANT_ID = comp.COMPLAINANT_ID
""")

        print(self.df_crimes.columns.tolist())
        self.df_investigations = query("SELECT * FROM INVESTIGATION")
        self.df_evidence = query("SELECT * FROM EVIDENCE")
        self.df_suspects = query("SELECT * FROM SUSPECT")
        self.df_witnesses = query("SELECT * FROM WITNESS")

        print(f"✓ Loaded {len(self.df_crimes)} crime records")
        return self.df_crimes

    
    def clean_data(self):
        """Clean and validate data"""
        print("\nCleaning data...")
        
        df = self.df_crimes.copy()
        
        # Convert datetime
        df.columns = df.columns.str.lower()
        df['incident_datetime'] = pd.to_datetime(df['incident_datetime'])
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['case_id'])
        
        # Handle missing values
        df['latitude'].fillna(df['latitude'].mean(), inplace=True)
        df['longitude'].fillna(df['longitude'].mean(), inplace=True)
        df['complainant_age'].fillna(df['complainant_age'].median(), inplace=True)
        
        # Validate coordinates
        df = df[(df['latitude'].between(12.5, 13.5)) & 
                (df['longitude'].between(79.8, 80.8))]
        
        print(f"✓ Cleaned data: {len(df)} records remaining")
        self.df_clean = df
        return df
    
    def engineer_features(self):
        """Create features for ML models"""
        print("\nEngineering features...")
        
        df = self.df_clean.copy()
        
        # TEMPORAL FEATURES
        df['hour'] = df['incident_datetime'].dt.hour
        df['day_of_week'] = df['incident_datetime'].dt.dayofweek
        df['day_of_month'] = df['incident_datetime'].dt.day
        df['month'] = df['incident_datetime'].dt.month
        df['year'] = df['incident_datetime'].dt.year
        df['quarter'] = df['incident_datetime'].dt.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_night'] = ((df['hour'] >= 20) | (df['hour'] <= 6)).astype(int)
        
        # Time periods
        def categorize_time(hour):
            if 6 <= hour < 12:
                return 'Morning'
            elif 12 <= hour < 18:
                return 'Afternoon'
            elif 18 <= hour < 22:
                return 'Evening'
            else:
                return 'Night'
        
        df['time_period'] = df['hour'].apply(categorize_time)
        
        # SPATIAL FEATURES
        # Distance from city center (13.0827, 80.2707)
        city_center = (13.0827, 80.2707)
        df['dist_from_center'] = np.sqrt(
            (df['latitude'] - city_center[0])**2 + 
            (df['longitude'] - city_center[1])**2
        )
        
        # Create grid cells for spatial analysis
        df['lat_grid'] = (df['latitude'] * 100).round().astype(int)
        df['lon_grid'] = (df['longitude'] * 100).round().astype(int)
        df['grid_cell'] = df['lat_grid'].astype(str) + '_' + df['lon_grid'].astype(str)
        
        # CRIME FREQUENCY FEATURES
        # Count crimes per grid cell
        grid_counts = df['grid_cell'].value_counts()
        df['grid_crime_count'] = df['grid_cell'].map(grid_counts)
        
        # Count crimes per district
        district_counts = df['district'].value_counts()
        df['district_crime_count'] = df['district'].map(district_counts)
        
        # Crime density score (crimes per square km proxy)
        df['crime_density_score'] = df['grid_crime_count'] / (df['dist_from_center'] + 0.1)
        
        # TEMPORAL AGGREGATION FEATURES
        # Crimes in same hour across dataset
        hour_counts = df.groupby(['day_of_week', 'hour']).size()
        df['hour_crime_rate'] = df.apply(
            lambda x: hour_counts.get((x['day_of_week'], x['hour']), 0), axis=1
        )
        
        # CATEGORICAL ENCODING
        categorical_cols = ['district', 'time_period', 'crime_type_code']
        for col in categorical_cols:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col])
            self.label_encoders[col] = le
        
        # SEVERITY MAPPING
        severity_map = {'Minor': 1, 'Moderate': 2, 'Serious': 3, 'Critical': 4}
        df['severity_score'] = df['severity_level'].map(severity_map)
        
        # PRIORITY MAPPING
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
        df['priority_score'] = df['priority'].map(priority_map)
        
        # STATUS ENCODING
        status_map = {
            'Reported': 1, 'Assigned': 2, 'Under Investigation': 3,
            'Pending': 4, 'Closed': 5, 'Cold Case': 6
        }
        df['status_encoded'] = df['status'].map(status_map)
        
        # AGE GROUP
        df['age_group'] = pd.cut(df['complainant_age'], 
                                 bins=[0, 25, 40, 60, 100],
                                 labels=['Young', 'Adult', 'Middle-aged', 'Senior'])
        
        # RISK SCORE (composite feature)
        df['risk_score'] = (
            df['severity_score'] * 0.4 +
            df['crime_density_score'] * 0.3 +
            df['grid_crime_count'] / df['grid_crime_count'].max() * 30 * 0.3
        )
        
        print(f"✓ Created {len(df.columns) - len(self.df_clean.columns)} new features")
        self.df_features = df
        return df
    
    def create_aggregated_features(self):
        """Create aggregated statistics per location"""
        print("\nCreating aggregated features...")
        
        df = self.df_features.copy()
        
        # Group by grid cell
        grid_agg = df.groupby('grid_cell').agg({
            'case_id': 'count',
            'severity_score': 'mean',
            'priority_score': 'mean',
            'latitude': 'mean',
            'longitude': 'mean',
            'is_weekend': 'mean',
            'is_night': 'mean'
        }).reset_index()
        
        grid_agg.columns = ['grid_cell', 'total_crimes', 'avg_severity', 
                           'avg_priority', 'center_lat', 'center_lon',
                           'weekend_crime_rate', 'night_crime_rate']
        
        # Crime type distribution per grid
        crime_type_pivot = df.groupby(['grid_cell', 'crime_type_code']).size().unstack(fill_value=0)
        crime_type_pivot = crime_type_pivot.add_prefix('crime_type_')
        
        # Merge back
        grid_agg = grid_agg.merge(crime_type_pivot, on='grid_cell', how='left')
        
        self.grid_aggregated = grid_agg
        print(f"✓ Created aggregated data for {len(grid_agg)} grid cells")
        return grid_agg
    
    def prepare_ml_features(self):
        """Prepare final feature matrix for ML models"""
        print("\nPreparing ML feature matrix...")
        
        df = self.df_features.copy()
        
        # Select numeric features for ML
        feature_cols = [
            'latitude', 'longitude', 'hour', 'day_of_week', 'month',
            'is_weekend', 'is_night', 'dist_from_center',
            'grid_crime_count', 'district_crime_count', 'crime_density_score',
            'hour_crime_rate', 'severity_score', 'priority_score',
            'complainant_age', 'district_encoded',
            'time_period_encoded', 'crime_type_code_encoded'
        ]
        
        X = df[feature_cols].copy()
        
        # Handle any remaining NaNs
        X.fillna(X.median(), inplace=True)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=feature_cols, index=X.index)
        
        # Add target variables
        X_scaled_df['case_id'] = df['case_id'].values
        X_scaled_df['target_severity'] = df['severity_score'].values
        X_scaled_df['target_crime_type'] = df['crime_type_code_encoded'].values
        X_scaled_df['target_risk'] = df['risk_score'].values
        
        self.ml_features = X_scaled_df
        print(f"✓ Prepared {len(feature_cols)} features for {len(X_scaled_df)} samples")
        return X_scaled_df, feature_cols
    
    def save_processed_data(self, output_dir='data/processed'):
        """Save all processed datasets"""
        os.makedirs(output_dir, exist_ok=True)
        
        self.df_features.to_csv(f'{output_dir}/crimes_with_features.csv', index=False)
        self.grid_aggregated.to_csv(f'{output_dir}/grid_aggregated.csv', index=False)
        self.ml_features.to_csv(f'{output_dir}/ml_features.csv', index=False)
        
        # Save encoders and scaler
        import joblib
        joblib.dump(self.label_encoders, f'{output_dir}/label_encoders.pkl')
        joblib.dump(self.scaler, f'{output_dir}/scaler.pkl')
        
        print(f"\n✓ Saved processed data to {output_dir}/")
        print(f"  - crimes_with_features.csv")
        print(f"  - grid_aggregated.csv")
        print(f"  - ml_features.csv")
        print(f"  - label_encoders.pkl")
        print(f"  - scaler.pkl")
    
    def get_data_summary(self):
        """Print data summary statistics"""
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        
        df = self.df_features
        
        print(f"\nTotal Records: {len(df)}")
        print(f"Date Range: {df['incident_datetime'].min()} to {df['incident_datetime'].max()}")
        print(f"\nCrime Types Distribution:")
        print(df['crime_type_description'].value_counts())
        print(f"\nSeverity Distribution:")
        print(df['severity_level'].value_counts())
        print(f"\nStatus Distribution:")
        print(df['status'].value_counts())
        print(f"\nTop 5 Districts:")
        print(df['district'].value_counts().head())

if __name__ == "__main__":
    print("=" * 60)
    print("CRIME DATA PREPROCESSOR")
    print("=" * 60)

    processor = CrimeDataPreprocessor()

    processor.connect_db(
        user="police_system",
        password="Police123#",
        dsn="localhost:1521/XEPDB1"
    )

    processor.load_data()
    processor.clean_data()
    processor.engineer_features()
    processor.create_aggregated_features()
    processor.prepare_ml_features()
    processor.save_processed_data()
    processor.get_data_summary()

    print("\n✓ Preprocessing complete!")
