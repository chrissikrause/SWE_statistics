import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path
from scipy.stats import zscore
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class BasinClusteringAnalysis:
    def __init__(self, folder_path, output_path, shapefile_path):
        self.folder_path = Path(folder_path)
        self.output_path = Path(output_path)
        self.shapefile_path = shapefile_path
        self.df_combined = None
        self.df_zscore = None
        self.df_pca = None
        self.pca_model = None
        self.distance_matrices = {}
        self.clustering_results = {}
        
    def load_and_combine_data(self):
        """Load and combine all trend CSV files"""
        print("Loading and combining trend data...")
        df_combined = pd.DataFrame()
        
        # Loop through all CSV files in the folder
        for csv_file in self.folder_path.glob("trend_results_*.csv"):
            # Extract variable name from filename
            variable_name = csv_file.stem.replace("trend_results_", "")
            
            # Load CSV and keep only required columns
            df = pd.read_csv(csv_file)
            df = df[['basin_id', 'theil_sen_slope']].rename(
                columns={'theil_sen_slope': variable_name}
            )
            
            # Merge into combined DataFrame
            if df_combined.empty:
                df_combined = df
            else:
                df_combined = pd.merge(df_combined, df, on='basin_id', how='outer')
        
        # Set basin_id as index and clean data
        df_combined.set_index('basin_id', inplace=True)
        
        # Replace 0 values with NaN
        df_combined.replace(0, np.nan, inplace=True)
        
        # Remove specific basins
        basins_to_remove = [4025, 4018, 4021, 4012]
        df_combined = df_combined.drop(index=basins_to_remove, errors='ignore')
        
        self.df_combined = df_combined
        print(f"Combined data shape: {df_combined.shape}")
        df_combined.to_csv(self.output_path)
        return df_combined
    
    def standardize_data(self):
        """Apply Z-score normalization"""
        print("Standardizing data...")
        self.df_zscore = self.df_combined.apply(lambda x: zscore(x, nan_policy='omit'))
        return self.df_zscore
    
    def calculate_distance_matrices(self):
        """Calculate Euclidean and Correlation distance matrices"""
        print("Calculating distance matrices...")
        data_filled = self.df_zscore.fillna(0)
        
        # Euclidean distance
        euclid_dist = pd.DataFrame(
            squareform(pdist(data_filled.values, metric='euclidean')),
            index=data_filled.index,
            columns=data_filled.index
        )
        
        # Correlation distance (1 - correlation)
        corr_dist = pd.DataFrame(
            squareform(pdist(data_filled.values, metric='correlation')),
            index=data_filled.index,
            columns=data_filled.index
        )
        
        self.distance_matrices = {
            'euclidean': euclid_dist,
            'correlation': corr_dist
        }
        
        return self.distance_matrices
    
    def perform_pca(self):
        """Perform PCA for visualization"""
        print("Performing PCA...")
        data_filled = self.df_zscore.fillna(0)
        
        self.pca_model = PCA(n_components=2)
        principal_components = self.pca_model.fit_transform(data_filled)
        
        self.df_pca = pd.DataFrame(
            principal_components,
            columns=['PC1', 'PC2'],
            index=data_filled.index
        )
        
        print(f"Explained variance ratio: {self.pca_model.explained_variance_ratio_}")
        return self.df_pca
    
    def perform_clustering(self, n_clusters=3):
        """Perform all clustering methods on both distance matrices"""
        print("Performing clustering analysis...")
        
        for dist_name, dist_matrix in self.distance_matrices.items():
            print(f"  Clustering with {dist_name} distance...")
            
            # Prepare data
            data_filled = self.df_zscore.fillna(0)
            condensed_dist = squareform(dist_matrix.values)
            
            # 1. Hierarchical Clustering
            Z = linkage(condensed_dist, method='average')
            hierarchical_labels = fcluster(Z, t=n_clusters, criterion='maxclust')
            
            # 2. K-Means Clustering (on original data, not distance matrix)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans_labels = kmeans.fit_predict(data_filled)
            
            # 3. DBSCAN Clustering
            # Determine eps based on distance matrix percentiles
            eps_value = np.percentile(dist_matrix.values[np.triu_indices_from(dist_matrix.values, k=1)], 10)
            dbscan = DBSCAN(eps=eps_value, min_samples=2, metric='precomputed')
            dbscan_labels = dbscan.fit_predict(dist_matrix.values)
            
            # Store results
            self.clustering_results[dist_name] = {
                'hierarchical': hierarchical_labels,
                'kmeans': kmeans_labels + 1,  # Add 1 to match other numbering
                'dbscan': dbscan_labels + 1 if len(set(dbscan_labels)) > 1 else np.ones_like(dbscan_labels),
                'linkage_matrix': Z
            }
    
    def plot_clustering_results(self):
        """Create comprehensive clustering plots"""
        print("Creating clustering plots...")
        
        # Define colors for clusters
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Create subplots for all combinations
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Clustering Results: Different Methods and Distance Metrics', fontsize=16)
        
        methods = ['hierarchical', 'kmeans', 'dbscan']
        distances = ['euclidean', 'correlation']
        
        for i, dist_name in enumerate(distances):
            for j, method in enumerate(methods):
                ax = axes[i, j]
                
                # Get cluster labels
                labels = self.clustering_results[dist_name][method]
                unique_labels = np.unique(labels)
                
                # Plot each cluster
                for k, cluster_id in enumerate(unique_labels):
                    if cluster_id == 0 and method == 'dbscan':  # Noise points in DBSCAN
                        color = 'gray'
                        label = 'Noise'
                    else:
                        color = colors[k % len(colors)]
                        label = f'Cluster {cluster_id}'
                    
                    mask = labels == cluster_id
                    subset = self.df_pca[mask]
                    
                    ax.scatter(subset['PC1'], subset['PC2'], 
                             color=color, edgecolor='white', s=50, 
                             label=label, alpha=0.7)
                
                ax.set_xlabel('PC1')
                ax.set_ylabel('PC2')
                ax.set_title(f'{method.title()} - {dist_name.title()} Distance')
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_dendrograms(self):
        """Plot dendrograms for hierarchical clustering"""
        print("Creating dendrograms...")
        
        fig, axes = plt.subplots(1, 2, figsize=(20, 6))
        
        for i, (dist_name, results) in enumerate(self.clustering_results.items()):
            ax = axes[i]
            
            dendrogram(results['linkage_matrix'], 
                      labels=self.df_pca.index.astype(str),
                      leaf_rotation=90,
                      ax=ax)
            ax.set_title(f'Hierarchical Clustering Dendrogram - {dist_name.title()} Distance')
            ax.set_ylabel('Distance')
        
        plt.tight_layout()
        plt.show()
    
    def create_spatial_maps(self):
        """Create spatial maps showing clustering results"""
        print("Creating spatial maps...")
        
        try:
            # Load shapefile
            basins_gdf = gpd.read_file(self.shapefile_path)
            basins_gdf['MAJ_BAS'] = basins_gdf['MAJ_BAS'].astype(self.df_combined.index.dtype)
            
            # Create subplots for spatial maps
            fig, axes = plt.subplots(2, 3, figsize=(20, 14))
            fig.suptitle('Spatial Distribution of Clusters', fontsize=16)
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            methods = ['hierarchical', 'kmeans', 'dbscan']
            distances = ['euclidean', 'correlation']
            
            for i, dist_name in enumerate(distances):
                for j, method in enumerate(methods):
                    ax = axes[i, j]
                    
                    # Create temporary dataframe with cluster info
                    cluster_data = pd.DataFrame({
                        'cluster': self.clustering_results[dist_name][method]
                    }, index=self.df_pca.index)
                    
                    # Merge with shapefile
                    map_data = basins_gdf.merge(cluster_data, left_on='MAJ_BAS', 
                                              right_index=True, how='left')
                    
                    # Create color mapping
                    unique_clusters = cluster_data['cluster'].unique()
                    color_map = {cluster: colors[i % len(colors)] for i, cluster in enumerate(unique_clusters)}
                    map_data['color'] = map_data['cluster'].map(color_map)
                    map_data['color'] = map_data['color'].fillna('#d3d3d3')  # Gray for unclustered
                    
                    # Plot
                    map_data.plot(color=map_data['color'], edgecolor='black', 
                                linewidth=0.5, ax=ax)
                    ax.set_title(f'{method.title()} - {dist_name.title()}')
                    ax.axis('off')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Could not create spatial maps: {e}")
            print("Please check if the shapefile path is correct")
    
    def print_cluster_summary(self):
        """Print summary statistics for each clustering method"""
        print("\n" + "="*60)
        print("CLUSTERING SUMMARY")
        print("="*60)
        
        for dist_name in ['euclidean', 'correlation']:
            print(f"\n{dist_name.upper()} DISTANCE:")
            print("-" * 40)
            
            for method in ['hierarchical', 'kmeans', 'dbscan']:
                labels = self.clustering_results[dist_name][method]
                unique_labels = np.unique(labels)
                
                print(f"\n{method.title()}:")
                print(f"  Number of clusters: {len(unique_labels)}")
                
                for cluster_id in unique_labels:
                    count = np.sum(labels == cluster_id)
                    if cluster_id == 0 and method == 'dbscan':
                        print(f"  Noise points: {count}")
                    else:
                        print(f"  Cluster {cluster_id}: {count} basins")
    
    def run_complete_analysis(self):
        """Run the complete clustering analysis pipeline"""
        print("Starting complete clustering analysis...")
        print("="*50)
        
        # Load and prepare data
        self.load_and_combine_data()
        self.standardize_data()
        self.calculate_distance_matrices()
        self.perform_pca()
        
        # Perform clustering
        self.perform_clustering()
        
        # Create visualizations
        self.plot_clustering_results()
        self.plot_dendrograms()
        self.create_spatial_maps()
        
        # Print summary
        self.print_cluster_summary()
        
        print("\nAnalysis complete!")
        return self

# Usage example:
if __name__ == "__main__":
    # Update these paths to match your data
    folder_path = r"C:\Innolab\output\swe\trend_swe_params"
    output_path = r"C:\Innolab\output\swe\combined_trend_data_swe.csv"
    shapefile_path = r"C:\Innolab\Daten_fuer_Christina\Data\Basins\Subbasins\alpine_subbasins.shp"
    # Run analysis
    analyzer = BasinClusteringAnalysis(folder_path, shapefile_path)
    analyzer.run_complete_analysis()
    
    # Access results
    # analyzer.df_combined  # Original combined data
    # analyzer.df_pca       # PCA results
    # analyzer.clustering_results  # All clustering results