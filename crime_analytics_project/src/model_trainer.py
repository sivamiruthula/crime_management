"""
MODEL TRAINER MODULE
Trains multiple ML/AI models for crime analytics
"""

import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import classification_report, mean_squared_error, silhouette_score
from sklearn.neighbors import KernelDensity
import warnings
warnings.filterwarnings('ignore')

class CrimeModelTrainer:
    def __init__(self):
        self.models = {}
        self.results = {}
        
    def load_data(self, data_dir='data/processed'):
        """Load processed data"""
        print("Loading processed data...")
        
        self.df_features = pd.read_csv(f'{data_dir}/crimes_with_features.csv')
        self.df_ml = pd.read_csv(f'{data_dir}/ml_features.csv')
        self.df_grid = pd.read_csv(f'{data_dir}/grid_aggregated.csv')
        
        print(f"✓ Loaded {len(self.df_ml)} samples")
        
    def train_crime_prediction_model(self):
        """Train Random Forest for crime type prediction"""
        print("\n" + "="*60)
        print("1. TRAINING CRIME TYPE PREDICTION MODEL (Random Forest)")
        print("="*60)
        
        # Prepare data
        leak_cols = [
    'case_id',
    'target_severity',
    'target_crime_type',
    'target_risk',
    'crime_type_code_encoded',
    'severity_score',
    'priority_score'
]

        feature_cols = [col for col in self.df_ml.columns if col not in leak_cols]
        
        X = self.df_ml[feature_cols]
        y = self.df_ml['target_crime_type'].astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_split=8,
            min_samples_leaf=4,
            random_state=42,
            max_features="sqrt",
            class_weight="balanced",
            n_jobs=-1
        )
        
        print("Training model...")
        cv_scores = cross_val_score(model, X, y, cv=5)
        print(f"  Cross-val Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

        model.fit(X_train, y_train)
        
        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Training Accuracy: {train_score:.4f}")
        print(f"  Test Accuracy: {test_score:.4f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Important Features:")
        print(feature_importance.head(10).to_string(index=False))
        
        # Save model
        self.models['crime_prediction'] = model
        self.results['crime_prediction'] = {
            'train_score': train_score,
            'test_score': test_score,
            'feature_importance': feature_importance
        }
        
        return model
    
    def train_severity_prediction_model(self):
        """Train Random Forest Regressor for severity prediction"""
        print("\n" + "="*60)
        print("2. TRAINING SEVERITY PREDICTION MODEL (Random Forest Regressor)")
        print("="*60)
        
        leak_cols = [
    'case_id',
    'target_severity',
    'target_crime_type',
    'target_risk',
    'crime_type_code_encoded',
    'severity_score',
    'priority_score'
]

        feature_cols = [col for col in self.df_ml.columns if col not in leak_cols]

        
        X = self.df_ml[feature_cols]
        y = self.df_ml['target_severity']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )

        
        model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        
        print("Training model...")
        model.fit(X_train, y_train)
        
        # Evaluate
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Training RMSE: {train_rmse:.4f}")
        print(f"  Test RMSE: {test_rmse:.4f}")
        
        self.models['severity_prediction'] = model
        self.results['severity_prediction'] = {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse
        }
        
        return model
    
    def train_hotspot_clustering_model(self):
        """Train K-Means for spatial clustering"""
        print("\n" + "="*60)
        print("3. TRAINING HOTSPOT CLUSTERING MODEL (K-Means)")
        print("="*60)
        
        # Use spatial features
        from sklearn.preprocessing import StandardScaler

        X = self.df_grid[['center_lat', 'center_lon', 'total_crimes', 
                        'avg_severity', 'night_crime_rate']].copy()

        X.fillna(X.mean(), inplace=True)

        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        
        # Determine optimal k using elbow method
        inertias = []
        silhouette_scores = []
        n_samples = len(X)

        # dynamic safe range
        max_k = min(10, n_samples - 1)

        # Ensure we don't go below 2
        if max_k <= 2:
            max_k = 2

        k_range = range(2, max_k + 1)

        
        print("Finding optimal number of clusters...")
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
            # Skip if all samples assigned to same cluster
            if len(set(kmeans.labels_)) <= 1:
                continue

            silhouette_scores.append(silhouette_score(X, kmeans.labels_))

        # Choose k with best silhouette score
        optimal_k = k_range[np.argmax(silhouette_scores)]
        print(f"Optimal number of clusters: {optimal_k}")
        
        # Train final model
        model = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        model.fit(X)
        
        # Add cluster labels
        self.df_grid['cluster'] = model.labels_
        
        # Cluster statistics
        print(f"\n✓ Model trained successfully!")
        print(f"  Silhouette Score: {silhouette_score(X, model.labels_):.4f}")
        print(f"  Inertia: {model.inertia_:.2f}")
        
        print("\nCluster Statistics:")
        cluster_stats = self.df_grid.groupby('cluster').agg({
            'total_crimes': ['mean', 'sum'],
            'avg_severity': 'mean',
            'center_lat': 'mean',
            'center_lon': 'mean'
        }).round(2)
        print(cluster_stats)
        
        self.models['hotspot_clustering'] = model
        self.results['hotspot_clustering'] = {
            'optimal_k': optimal_k,
            'silhouette_score': silhouette_score(X, model.labels_),
            'cluster_centers': model.cluster_centers_
        }
        
        return model
    
    def train_dbscan_clustering(self):
        """Train DBSCAN for density-based clustering"""
        print("\n" + "="*60)
        print("4. TRAINING DBSCAN CLUSTERING MODEL")
        print("="*60)
        
        # Use lat/lon weighted by crime count
        X = self.df_grid[['center_lat', 'center_lon']].copy()
        weights = self.df_grid['total_crimes'].values
        
        # Train DBSCAN
        model = DBSCAN(eps=0.005, min_samples=5, metric='euclidean')
        labels = model.fit_predict(X, sample_weight=weights)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Number of clusters: {n_clusters}")
        print(f"  Number of noise points: {n_noise}")
        
        self.df_grid['dbscan_cluster'] = labels
        self.models['dbscan_clustering'] = model
        
        return model
    
    def train_anomaly_detection_model(self):
        """Train Isolation Forest for anomaly detection"""
        print("\n" + "="*60)
        print("5. TRAINING ANOMALY DETECTION MODEL (Isolation Forest)")
        print("="*60)
        
        leak_cols = [
    'case_id',
    'target_severity',
    'target_crime_type',
    'target_risk',
    'crime_type_code_encoded',
    'severity_score',
    'priority_score'
]

        feature_cols = [col for col in self.df_ml.columns if col not in leak_cols]

        
        X = self.df_ml[feature_cols]
        
        # Train model
        model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_jobs=-1
        )

        
        print("Training model...")
        model.fit(X)
        
        # Predict anomalies
        predictions = model.predict(X)
        anomaly_scores = model.score_samples(X)
        
        n_anomalies = (predictions == -1).sum()
        anomaly_rate = n_anomalies / len(predictions) * 100
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Detected {n_anomalies} anomalies ({anomaly_rate:.2f}%)")
        
        # Save anomaly info
        self.df_features['is_anomaly'] = predictions == -1
        self.df_features['anomaly_score'] = anomaly_scores
        
        self.models['anomaly_detection'] = model
        self.results['anomaly_detection'] = {
            'n_anomalies': n_anomalies,
            'anomaly_rate': anomaly_rate
        }
        
        return model
    
    def train_kernel_density_estimator(self):
        """Train KDE for hotspot density estimation"""
        print("\n" + "="*60)
        print("6. TRAINING KERNEL DENSITY ESTIMATOR")
        print("="*60)
        
        # Prepare spatial data
        X = self.df_features[['latitude', 'longitude']].values
        
        # Train KDE
        model = KernelDensity(bandwidth=0.01, kernel='gaussian')
        model.fit(X)
        
        # Create density grid
        lat_range = np.linspace(X[:, 0].min(), X[:, 0].max(), 100)
        lon_range = np.linspace(X[:, 1].min(), X[:, 1].max(), 100)
        lat_grid, lon_grid = np.meshgrid(lat_range, lon_range)
        
        grid_points = np.c_[lat_grid.ravel(), lon_grid.ravel()]
        density = np.exp(model.score_samples(grid_points))
        density_grid = density.reshape(lat_grid.shape)
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Density grid shape: {density_grid.shape}")
        
        self.models['kernel_density'] = model
        self.results['kernel_density'] = {
            'density_grid': density_grid,
            'lat_grid': lat_grid,
            'lon_grid': lon_grid
        }
        
        return model
    
    def save_all_models(self, output_dir='data/models'):
        """Save all trained models"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*60)
        print("SAVING MODELS")
        print("="*60)
        
        for name, model in self.models.items():
            filename = f'{output_dir}/{name}_model.pkl'
            joblib.dump(model, filename)
            print(f"✓ Saved {name} model")
        
        # Save results
        import json
        results_serializable = {}
        for key, value in self.results.items():
            results_serializable[key] = {}
            for k, v in value.items():
                if isinstance(v, (np.ndarray, pd.DataFrame)):
                    continue  # Skip arrays

                # Convert numpy values to native python types
                if isinstance(v, (np.integer, np.int64)):
                    v = int(v)
                elif isinstance(v, (np.floating, np.float64)):
                    v = float(v)

                results_serializable[key][k] = v

        
        with open(f'{output_dir}/model_results.json', 'w') as f:
            json.dump(results_serializable, f, indent=2)
        
        # Save processed data with predictions
        self.df_features.to_csv(f'{output_dir}/crimes_with_predictions.csv', index=False)
        self.df_grid.to_csv(f'{output_dir}/grid_with_clusters.csv', index=False)
        
        print(f"\n✓ All models saved to {output_dir}/")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*60)
        print("MODEL PERFORMANCE REPORT")
        print("="*60)
        
        for model_name, metrics in self.results.items():
            print(f"\n{model_name.upper().replace('_', ' ')}:")
            for metric, value in metrics.items():
                if not isinstance(value, (np.ndarray, pd.DataFrame)):
                    print(f"  {metric}: {value}")

if __name__ == "__main__":
    print("=" * 60)
    print("CRIME ANALYTICS MODEL TRAINER")
    print("=" * 60)
    
    trainer = CrimeModelTrainer()
    trainer.load_data()
    
    # Train all models
    trainer.train_crime_prediction_model()
    trainer.train_severity_prediction_model()
    trainer.train_hotspot_clustering_model()
    trainer.train_dbscan_clustering()
    trainer.train_anomaly_detection_model()
    trainer.train_kernel_density_estimator()
    
    # Save everything
    trainer.save_all_models()
    trainer.generate_performance_report()
    
    print("\n" + "="*60)
    print("✓ MODEL TRAINING COMPLETE!")
    print("="*60)
    print("\nNext step: Run visualizer.py or main.py")