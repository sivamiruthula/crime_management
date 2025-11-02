"""
VISUALIZER MODULE
Creates interactive maps, charts, and dashboards
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap, MarkerCluster
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
warnings.filterwarnings('ignore')

class CrimeVisualizer:
    def __init__(self):
        # compute root of crime_analytics_project
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # fix outputs path (inside project)
        self.output_dir = os.path.join(self.project_root, 'outputs')
        os.makedirs(f'{self.output_dir}/maps', exist_ok=True)
        os.makedirs(f'{self.output_dir}/charts', exist_ok=True)
        os.makedirs(f'{self.output_dir}/reports', exist_ok=True)

        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

        
    def load_data(self):
        """Load processed data"""
        print("Loading data for visualization...")
        models_dir = os.path.join(self.project_root, 'data', 'models')
        self.df = pd.read_csv(os.path.join(models_dir, 'crimes_with_predictions.csv'))
        self.df_grid = pd.read_csv(os.path.join(models_dir, 'grid_with_clusters.csv'))
        self.df['incident_datetime'] = pd.to_datetime(self.df['incident_datetime'])
        print(f"✓ Loaded {len(self.df)} records")

        
    def create_hotspot_heatmap(self):
        """Create interactive crime hotspot heatmap"""
        print("\nCreating hotspot heatmap...")
        
        # Create base map centered on data
        center_lat = self.df['latitude'].mean()
        center_lon = self.df['longitude'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Prepare heatmap data
        heat_data = [[row['latitude'], row['longitude'], row['risk_score']] 
                     for idx, row in self.df.iterrows()]
        
        # Add heatmap
        HeatMap(
            heat_data,
            min_opacity=0.3,
            max_opacity=0.8,
            radius=15,
            blur=20,
            gradient={0.4: 'blue', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
        ).add_to(m)
        
        # Add cluster markers for high-risk areas
        high_risk = self.df[self.df['risk_score'] > self.df['risk_score'].quantile(0.9)]
        marker_cluster = MarkerCluster().add_to(m)
        
        for idx, row in high_risk.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"""
                    <b>Case ID:</b> {row['case_id']}<br>
                    <b>Crime:</b> {row['crime_type_description']}<br>
                    <b>Severity:</b> {row['severity_level']}<br>
                    <b>Risk Score:</b> {row['risk_score']:.2f}<br>
                    <b>Time:</b> {row['incident_datetime']}
                """,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        
        # Save map
        output_file = f'{self.output_dir}/maps/crime_hotspot_heatmap.html'
        m.save(output_file)
        print(f"✓ Saved hotspot heatmap to {output_file}")
        
        return m
    
    def create_cluster_map(self):
        """Create map showing clustering results"""
        print("Creating cluster visualization map...")
        
        center_lat = self.df_grid['center_lat'].mean()
        center_lon = self.df_grid['center_lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='CartoDB positron'
        )
        
        # Color map for clusters
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                 'lightred', 'beige', 'darkblue', 'darkgreen']
        
        for idx, row in self.df_grid.iterrows():
            if pd.notna(row['cluster']):
                cluster_id = int(row['cluster'])
                color = colors[cluster_id % len(colors)]
                
                folium.CircleMarker(
                    location=[row['center_lat'], row['center_lon']],
                    radius=row['total_crimes'] / 5,
                    popup=f"""
                        <b>Cluster:</b> {cluster_id}<br>
                        <b>Total Crimes:</b> {row['total_crimes']}<br>
                        <b>Avg Severity:</b> {row['avg_severity']:.2f}<br>
                        <b>Night Crime Rate:</b> {row['night_crime_rate']:.2%}
                    """,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6
                ).add_to(m)
        
        output_file = f'{self.output_dir}/maps/crime_clusters_map.html'
        m.save(output_file)
        print(f"✓ Saved cluster map to {output_file}")
        
        return m
    
    def create_temporal_analysis_charts(self):
        """Create temporal analysis charts"""
        print("Creating temporal analysis charts...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Crimes by hour of day
        hourly_crimes = self.df.groupby('hour').size()
        axes[0, 0].bar(hourly_crimes.index, hourly_crimes.values, color='steelblue')
        axes[0, 0].set_xlabel('Hour of Day', fontsize=12)
        axes[0, 0].set_ylabel('Number of Crimes', fontsize=12)
        axes[0, 0].set_title('Crime Distribution by Hour', fontsize=14, fontweight='bold')
        axes[0, 0].grid(alpha=0.3)
        
        # 2. Crimes by day of week
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_crimes = self.df.groupby('day_of_week').size()
        axes[0, 1].bar(range(7), daily_crimes.values, color='coral')
        axes[0, 1].set_xticks(range(7))
        axes[0, 1].set_xticklabels(day_names)
        axes[0, 1].set_xlabel('Day of Week', fontsize=12)
        axes[0, 1].set_ylabel('Number of Crimes', fontsize=12)
        axes[0, 1].set_title('Crime Distribution by Day', fontsize=14, fontweight='bold')
        axes[0, 1].grid(alpha=0.3)
        
        # 3. Crimes by month
        monthly_crimes = self.df.groupby('month').size()
        axes[1, 0].plot(monthly_crimes.index, monthly_crimes.values, 
                       marker='o', linewidth=2, markersize=8, color='green')
        axes[1, 0].set_xlabel('Month', fontsize=12)
        axes[1, 0].set_ylabel('Number of Crimes', fontsize=12)
        axes[1, 0].set_title('Crime Trend by Month', fontsize=14, fontweight='bold')
        axes[1, 0].grid(alpha=0.3)
        
        # 4. Crime type distribution
        crime_types = self.df['crime_type_description'].value_counts().head(10)
        axes[1, 1].barh(range(len(crime_types)), crime_types.values, color='purple')
        axes[1, 1].set_yticks(range(len(crime_types)))
        axes[1, 1].set_yticklabels(crime_types.index)
        axes[1, 1].set_xlabel('Number of Crimes', fontsize=12)
        axes[1, 1].set_title('Top 10 Crime Types', fontsize=14, fontweight='bold')
        axes[1, 1].grid(alpha=0.3, axis='x')
        
        plt.tight_layout()
        output_file = f'{self.output_dir}/charts/temporal_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved temporal analysis to {output_file}")
    
    def create_interactive_dashboard(self):
        """Create interactive Plotly dashboard"""
        print("Creating interactive dashboard...")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Crime Severity Distribution',
                'Priority Level Distribution',
                'districtal Crime Distribution',
                'Time Period Analysis',
                'Crime Status Overview',
                'Risk Score Distribution'
            ),
            specs=[
                [{"type": "pie"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "histogram"}]
            ]
        )
        
        # 1. Severity pie chart
        severity_counts = self.df['severity_level'].value_counts()
        fig.add_trace(
            go.Pie(labels=severity_counts.index, values=severity_counts.values,
                   marker_colors=['#ff9999', '#ffcc99', '#ffff99', '#99ff99']),
            row=1, col=1
        )
        
        # 2. Priority pie chart
        priority_counts = self.df['priority'].value_counts()
        fig.add_trace(
            go.Pie(labels=priority_counts.index, values=priority_counts.values,
                   marker_colors=['#66b3ff', '#99ff99', '#ffcc99', '#ff9999']),
            row=1, col=2
        )
        
        # 3. districtal bar chart
        district_counts = self.df['district'].value_counts()
        fig.add_trace(
            go.Bar(x=district_counts.index, y=district_counts.values,
                   marker_color='steelblue'),
            row=2, col=1
        )
        
        # 4. Time period bar chart
        time_period_counts = self.df['time_period'].value_counts()
        fig.add_trace(
            go.Bar(x=time_period_counts.index, y=time_period_counts.values,
                   marker_color='coral'),
            row=2, col=2
        )
        
        # 5. Status bar chart
        status_counts = self.df['status'].value_counts()
        fig.add_trace(
            go.Bar(x=status_counts.index, y=status_counts.values,
                   marker_color='purple'),
            row=3, col=1
        )
        
        # 6. Risk score histogram
        fig.add_trace(
            go.Histogram(x=self.df['risk_score'], nbinsx=30,
                        marker_color='green'),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            showlegend=False,
            title_text="Crime Analytics Dashboard",
            title_font_size=24
        )
        
        output_file = f'{self.output_dir}/reports/interactive_dashboard.html'
        fig.write_html(output_file)
        print(f"✓ Saved interactive dashboard to {output_file}")
    
    def create_anomaly_report(self):
        """Create anomaly detection report"""
        print("Creating anomaly detection report...")
        
        anomalies = self.df[self.df['is_anomaly'] == True].copy()
        
        if len(anomalies) > 0:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Anomaly locations
            axes[0].scatter(self.df['longitude'], self.df['latitude'], 
                          c='blue', alpha=0.3, s=10, label='Normal')
            axes[0].scatter(anomalies['longitude'], anomalies['latitude'],
                          c='red', alpha=0.7, s=50, marker='x', label='Anomaly')
            axes[0].set_xlabel('Longitude')
            axes[0].set_ylabel('Latitude')
            axes[0].set_title('Anomaly Detection - Spatial Distribution')
            axes[0].legend()
            axes[0].grid(alpha=0.3)
            
            # Anomaly scores distribution
            axes[1].hist(self.df['anomaly_score'], bins=50, color='blue', alpha=0.5, label='All')
            axes[1].hist(anomalies['anomaly_score'], bins=30, color='red', alpha=0.7, label='Anomalies')
            axes[1].set_xlabel('Anomaly Score')
            axes[1].set_ylabel('Frequency')
            axes[1].set_title('Anomaly Score Distribution')
            axes[1].legend()
            axes[1].grid(alpha=0.3)
            
            plt.tight_layout()
            output_file = f'{self.output_dir}/charts/anomaly_detection.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Save anomaly CSV
            anomalies_sorted = anomalies.sort_values('anomaly_score')
            anomalies_sorted[['case_id', 'crime_type_description', 'severity_level',
                            'incident_datetime', 'district', 'district', 
                            'risk_score', 'anomaly_score']].to_csv(
                f'{self.output_dir}/reports/detected_anomalies.csv', index=False
            )
            
            print(f"✓ Saved anomaly report to {output_file}")
            print(f"✓ Detected {len(anomalies)} anomalous cases")
    
    def generate_summary_statistics(self):
        """Generate comprehensive summary statistics"""
        print("Generating summary statistics...")
        
        summary = []
        summary.append("="*70)
        summary.append("CRIME ANALYTICS - SUMMARY STATISTICS")
        summary.append("="*70)
        summary.append(f"\nDataset Overview:")
        summary.append(f"  Total Crime Records: {len(self.df)}")
        summary.append(f"  Date Range: {self.df['incident_datetime'].min()} to {self.df['incident_datetime'].max()}")
        summary.append(f"  Unique districts: {self.df['district'].nunique()}")
        summary.append(f"  Unique Districts: {self.df['district'].nunique()}")
        
        summary.append(f"\n{'='*70}")
        summary.append("Crime Type Distribution:")
        summary.append(f"{'='*70}")
        for crime, count in self.df['crime_type_description'].value_counts().items():
            pct = count / len(self.df) * 100
            summary.append(f"  {crime:<30} {count:>6} ({pct:>5.2f}%)")
        
        summary.append(f"\n{'='*70}")
        summary.append("Severity Distribution:")
        summary.append(f"{'='*70}")
        for severity, count in self.df['severity_level'].value_counts().items():
            pct = count / len(self.df) * 100
            summary.append(f"  {severity:<20} {count:>6} ({pct:>5.2f}%)")
        
        summary.append(f"\n{'='*70}")
        summary.append("districtal Statistics:")
        summary.append(f"{'='*70}")
        for district in self.df['district'].unique():
            district_data = self.df[self.df['district'] == district]
            avg_risk = district_data['risk_score'].mean()
            summary.append(f"  {district:<20} Crimes: {len(district_data):>5}  Avg Risk: {avg_risk:>6.2f}")
        
        summary.append(f"\n{'='*70}")
        summary.append("Temporal Patterns:")
        summary.append(f"{'='*70}")
        summary.append(f"  Weekend Crimes: {(self.df['is_weekend']==1).sum()} ({(self.df['is_weekend']==1).sum()/len(self.df)*100:.1f}%)")
        summary.append(f"  Night Crimes: {(self.df['is_night']==1).sum()} ({(self.df['is_night']==1).sum()/len(self.df)*100:.1f}%)")
        summary.append(f"  Peak Hour: {self.df.groupby('hour').size().idxmax()}:00")
        summary.append(f"  Peak Day: {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][self.df.groupby('day_of_week').size().idxmax()]}")
        
        if 'is_anomaly' in self.df.columns:
            n_anomalies = (self.df['is_anomaly'] == True).sum()
            summary.append(f"\n{'='*70}")
            summary.append("Anomaly Detection:")
            summary.append(f"{'='*70}")
            summary.append(f"  Detected Anomalies: {n_anomalies} ({n_anomalies/len(self.df)*100:.2f}%)")
        
        summary.append(f"\n{'='*70}")
        
        # Save to file
        output_file = f'{self.output_dir}/reports/summary_statistics.txt'
        with open(output_file, 'w') as f:
            f.write('\n'.join(summary))
        
        # Also print to console
        print('\n'.join(summary))
        print(f"\n✓ Saved summary to {output_file}")
    
    def create_all_visualizations(self):
        """Create all visualizations"""
        print("\n" + "="*60)
        print("CREATING ALL VISUALIZATIONS")
        print("="*60)
        
        self.create_hotspot_heatmap()
        self.create_cluster_map()
        self.create_temporal_analysis_charts()
        self.create_interactive_dashboard()
        self.create_anomaly_report()
        self.generate_summary_statistics()
        
        print("\n" + "="*60)
        print("✓ ALL VISUALIZATIONS CREATED!")
        print("="*60)
        print(f"\nOutputs saved to:")
        print(f"  Maps: {self.output_dir}/maps/")
        print(f"  Charts: {self.output_dir}/charts/")
        print(f"  Reports: {self.output_dir}/reports/")

if __name__ == "__main__":
    visualizer = CrimeVisualizer()
    visualizer.load_data()
    visualizer.create_all_visualizations()