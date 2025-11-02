"""
MAIN EXECUTION SCRIPT
Runs the complete crime analytics pipeline
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append('src')

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        'data/raw',
        'data/processed',
        'data/models',
        'outputs/maps',
        'outputs/charts',
        'outputs/reports',
        'src'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Created directory structure")

def run_pipeline(steps='all'):
    """
    Run the complete analytics pipeline
    
    Parameters:
    -----------
    steps : str or list
        Which steps to run:
        - 'all': Run complete pipeline
        - 'generate': Generate demo data only
        - 'preprocess': Preprocess data only
        - 'train': Train models only
        - 'visualize': Create visualizations only
        Or pass a list like ['generate', 'preprocess']
    """
    
    print("\n" + "="*70)
    print("CRIME ANALYTICS & HOTSPOT DETECTION SYSTEM")
    print("Complete Execution Pipeline")
    print("="*70)
    
    start_time = time.time()
    
    # Determine which steps to run
    if steps == 'all':
        run_steps = ['generate', 'preprocess', 'train', 'visualize']
    elif isinstance(steps, str):
        run_steps = [steps]
    else:
        run_steps = steps
    
    # Step 1: Generate Data
    if 'generate' in run_steps:
        print("\n" + "="*70)
        print("STEP 1: GENERATING DEMO DATA")
        print("="*70)
        
        try:
            from data_generator import CrimeDataGenerator
            generator = CrimeDataGenerator(num_records=5000)
            generator.save_data()
            print("✓ Step 1 complete")
        except Exception as e:
            print(f"✗ Error in data generation: {str(e)}")
            return False
    
    # Step 2: Preprocess Data
    if 'preprocess' in run_steps:
        print("\n" + "="*70)
        print("STEP 2: PREPROCESSING DATA & FEATURE ENGINEERING")
        print("="*70)
        
        try:
            from data_preprocessor import CrimeDataPreprocessor
            processor = CrimeDataPreprocessor()
            processor.load_data()
            processor.clean_data()
            processor.engineer_features()
            processor.create_aggregated_features()
            processor.prepare_ml_features()
            processor.save_processed_data()
            print("✓ Step 2 complete")
        except Exception as e:
            print(f"✗ Error in preprocessing: {str(e)}")
            return False
    
    # Step 3: Train Models
    if 'train' in run_steps:
        print("\n" + "="*70)
        print("STEP 3: TRAINING ML/AI MODELS")
        print("="*70)
        
        try:
            from model_trainer import CrimeModelTrainer
            trainer = CrimeModelTrainer()
            trainer.load_data()
            trainer.train_crime_prediction_model()
            trainer.train_severity_prediction_model()
            trainer.train_hotspot_clustering_model()
            trainer.train_dbscan_clustering()
            trainer.train_anomaly_detection_model()
            trainer.train_kernel_density_estimator()
            trainer.save_all_models()
            trainer.generate_performance_report()
            print("✓ Step 3 complete")
        except Exception as e:
            print(f"✗ Error in model training: {str(e)}")
            return False
    
    # Step 4: Create Visualizations
    if 'visualize' in run_steps:
        print("\n" + "="*70)
        print("STEP 4: CREATING VISUALIZATIONS & REPORTS")
        print("="*70)
        
        try:
            from visualizer import CrimeVisualizer
            visualizer = CrimeVisualizer()
            visualizer.load_data()
            visualizer.create_all_visualizations()
            print("✓ Step 4 complete")
        except Exception as e:
            print(f"✗ Error in visualization: {str(e)}")
            return False
    
    # Complete
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("PIPELINE EXECUTION COMPLETE!")
    print("="*70)
    print(f"Total execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print("\nGenerated outputs:")
    print("  📊 Interactive maps in outputs/maps/")
    print("  📈 Charts in outputs/charts/")
    print("  📄 Reports in outputs/reports/")
    print("  🤖 Trained models in data/models/")
    
    return True

def quick_analysis():
    """Quick analysis without full pipeline"""
    print("\n" + "="*70)
    print("QUICK ANALYSIS MODE")
    print("="*70)
    
    import pandas as pd
    import joblib
    
    # Load data
    try:
        df = pd.read_csv('data/models/crimes_with_predictions.csv')
        df_grid = pd.read_csv('data/models/grid_with_clusters.csv')
        
        print(f"\n✓ Loaded data: {len(df)} crime records")
        
        # Quick stats
        print("\nQuick Statistics:")
        print(f"  Total crimes: {len(df)}")
        print(f"  Date range: {df['incident_datetime'].min()} to {df['incident_datetime'].max()}")
        print(f"\nCrime types:")
        print(df['crime_type_description'].value_counts().head())
        print(f"\nHigh-risk areas (top 5):")
        high_risk = df_grid.nlargest(5, 'total_crimes')[['center_lat', 'center_lon', 'total_crimes', 'avg_severity']]
        print(high_risk.to_string(index=False))
        
        # Load a model and make sample prediction
        try:
            model = joblib.load('data/models/crime_prediction_model.pkl')
            print(f"\n✓ Loaded prediction model")
            print(f"  Model type: {type(model).__name__}")
        except:
            print("\n✗ Model not found. Run full pipeline first.")
        
    except FileNotFoundError:
        print("\n✗ Data files not found. Run 'python main.py' first to generate data.")

def print_usage():
    """Print usage instructions"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         CRIME ANALYTICS & HOTSPOT DETECTION SYSTEM               ║
║                        Usage Guide                               ║
╚══════════════════════════════════════════════════════════════════╝

BASIC USAGE:
------------
1. Run complete pipeline:
   python main.py

2. Run specific steps:
   python main.py generate     # Generate demo data only
   python main.py preprocess   # Preprocess data only
   python main.py train        # Train models only
   python main.py visualize    # Create visualizations only

3. Quick analysis:
   python main.py quick        # Quick stats from existing data

4. Help:
   python main.py help         # Show this message

FILE STRUCTURE:
---------------
crime_analytics_project/
│
├── data/
│   ├── raw/              # Generated demo data
│   ├── processed/        # Cleaned & featured data
│   └── models/           # Trained ML models
│
├── outputs/
│   ├── maps/            # Interactive crime maps
│   ├── charts/          # Statistical visualizations
│   └── reports/         # Analysis reports
│
└── src/
    ├── data_generator.py      # Demo data generation
    ├── data_preprocessor.py   # Data cleaning & features
    ├── model_trainer.py       # ML model training
    └── visualizer.py          # Visualization creation

MODELS TRAINED:
---------------
1. Random Forest Classifier - Crime type prediction
2. Random Forest Regressor - Severity prediction
3. K-Means Clustering - Hotspot identification
4. DBSCAN - Density-based clustering
5. Isolation Forest - Anomaly detection
6. Kernel Density Estimation - Crime density mapping

OUTPUTS CREATED:
----------------
• crime_hotspot_heatmap.html - Interactive heatmap
• crime_clusters_map.html - Cluster visualization
• temporal_analysis.png - Time-based charts
• interactive_dashboard.html - Full dashboard
• anomaly_detection.png - Anomaly visualization
• summary_statistics.txt - Statistical report
• detected_anomalies.csv - Anomalous cases

For more information, see README.md
    """)

if __name__ == "__main__":
    # Create directory structure
    create_directory_structure()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'help':
            print_usage()
        elif command == 'quick':
            quick_analysis()
        elif command in ['generate', 'preprocess', 'train', 'visualize']:
            run_pipeline(command)
        else:
            print(f"Unknown command: {command}")
            print("Run 'python main.py help' for usage instructions")
    else:
        # Run complete pipeline
        success = run_pipeline('all')
        
        if success:
            print("\n" + "="*70)
            print("🎉 SUCCESS! Your crime analytics system is ready!")
            print("="*70)
            print("\nOpen these files in your browser:")
            print("  • outputs/maps/crime_hotspot_heatmap.html")
            print("  • outputs/reports/interactive_dashboard.html")
            print("\nView analysis reports:")
            print("  • outputs/reports/summary_statistics.txt")
            print("  • outputs/reports/detected_anomalies.csv")