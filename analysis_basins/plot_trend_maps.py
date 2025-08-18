import os
import glob
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import theilslopes, kendalltau
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap, Normalize
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle



def plot_trend_analysis(df, title, file_name, save_path=None, dpi=300, variable_name="trend_percent"):
    """
    Plot trend analysis results mit dynamischer Normalisierung
    - Variablen aus not_normalized_var oder mit 'day' im Namen werden NICHT normalisiert
    """

    not_normalized_params = [
        'max_month', 'min_month', 'month_distance_hydro', 'month_distance',
        'min_discharge_month', 'max_discharge_month'
        # alle Variablen mit "day" werden zusätzlich dynamisch erkannt
    ]

    # Farbdefinition
    colors = [
        (0.0, "#6B2737"),
        (0.05, "#A63C54"),
        (0.47, "#F4E1E5"),
        (0.5, "#FEFAEF"),
        (0.53, "#DCEDF6"),
        (0.95, "#29749C"),
        (1.0, "#18435A"),
    ]
    custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)

    
    # Normalize if parameter is in unit day or month
    file_name_lower = file_name.lower()
    if any(param in file_name_lower for param in not_normalized_params) or "day" in file_name_lower:
        # nicht normalisieren
        df["trend_normalized"] = df[variable_name]
        max_abs = df["trend_normalized"].abs().max()
        if max_abs == 0:
            max_abs = 1  # Vermeidung von Division durch Null, falls alle Werte 0
        norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
    else:
        # normalisieren
        df["trend_normalized"] = df[variable_name] / df[variable_name].abs().max()
        norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    
    # Plot-Setup
    fig, ax = plt.subplots(figsize=(18, 6))

    # Basins grau
    df.plot(ax=ax, color='#DDE3E7', edgecolor='white', linewidth=0.9)

    # Overlay mit Farben
    df.plot(
        ax=ax,
        column='trend_normalized',
        cmap=custom_cmap,
        edgecolor='black',
        linewidth=0.9,
        norm=norm
    )

    # Signifikanz
    basins_significance = df[df['significant'] == True]
    if not basins_significance.empty:
        basins_significance.plot(
            ax=ax, color='none', edgecolor='black', linewidth=0,
            hatch='/', zorder=7
        )

    ax.set_aspect('auto')
    ax.set_title(title, fontsize=10, fontname="Frutiger")
    ax.axis('off')

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.15, pad=0.04)
    cbar.set_label(f"Slope of Theil-Sen Estimator ({variable_name})")

    # Legende für Signifikanz
    hatch_patch = mpatches.Patch(
        facecolor='white', hatch='///', edgecolor='black',
        label='Mann Kendall Significance'
    )
    ax.legend(handles=[hatch_patch], loc='lower left', fontsize=10)

    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)



def process_trend_data_folder(csv_folder_path, shapefile_path, output_folder, 
                            basin_type='basin', dpi=600):
    """
    Process all CSV files in a folder and create trend analysis plots
    
    Parameters:
    csv_folder_path: Path to folder containing CSV files with trend data
    shapefile_path: Path to shapefile (basin or subbasin)
    output_folder: Path to folder where plots will be saved
    basin_type: 'basin' or 'subbasin' - determines the ID column name for merging
    dpi: Resolution for saved plots
    """
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Load shapefile
    input_shp = gpd.read_file(shapefile_path)
    
    # Determine the ID column based on basin_type
    if basin_type.lower() == 'basin':
        id_column = 'basin_id'
        # Rename column if needed (assuming MAJ_BAS is the basin ID in shapefile)
        if 'MAJ_BAS' in input_shp.columns:
            input_shp = input_shp.rename(columns={'MAJ_BAS': 'basin_id'})
    elif basin_type.lower() == 'subbasin':
        id_column = 'basin_id'
        # Rename column if needed (you might need to adjust this based on your shapefile)
        if 'MAJ_BAS' in input_shp.columns:
            input_shp = input_shp.rename(columns={'MAJ_BAS': 'basin_id'})
    else:
        raise ValueError("basin_type must be either 'basin' or 'subbasin'")
    
    # Get all CSV files in the folder
    csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {csv_folder_path}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process...")
    
    # Process each CSV file
    for csv_file in csv_files:
        try:
            print(f"Processing: {os.path.basename(csv_file)}")
            
            # Load CSV data
            trend_df = pd.read_csv(csv_file)
            
            # Check if required columns exist
            required_columns = [id_column, 'trend_percent', 'significant']
            missing_columns = [col for col in required_columns if col not in trend_df.columns]
            
            if missing_columns:
                print(f"Warning: Missing columns {missing_columns} in {csv_file}. Skipping...")
                continue
            
            # Merge with shapefile
            merged_df = input_shp.merge(trend_df, on=id_column, how='inner')
            
            if merged_df.empty:
                print(f"Warning: No matching records found for {csv_file}. Skipping...")
                continue
            
            # Extract title from filename (remove extension and replace _ with spaces)
            filename_without_ext = os.path.splitext(os.path.basename(csv_file))[0]
            title = filename_without_ext.replace('_', ' ').title()
            
            # Create output filename
            output_filename = f"{filename_without_ext}.png"
            output_path = os.path.join(output_folder, output_filename)
            
            # Create the plot
            plot_trend_analysis(merged_df, title=title, file_name=filename_without_ext, save_path=output_path, dpi=dpi)
            
            print(f"Successfully created plot: {output_filename}")
            
        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")
            continue
    
    print("Processing completed!")


# Example usage
if __name__ == "__main__":
    # Define paths
    csv_folder = r"C:\Innolab\output\discharge\trend_riverdischarge_params"
    basin_shapefile = r"C:\Innolab\Daten_fuer_Christina\Data\Basins\FAO_Basins\alpine_basins.shp"
    subbasin_shapefile = r"C:\Innolab\Daten_fuer_Christina\Data\Basins\Subbasins\alpine_subbasins.shp"  # Adjust path as needed
    output_folder = r"C:\Innolab\output\discharge\trend_maps_riverdischarge_subbasins"


    
    '''
    # Process with basin data
    process_trend_data_folder(
        csv_folder_path=csv_folder,
        shapefile_path=basin_shapefile,
        output_folder=output_folder,
        basin_type='basin',
        dpi=600
    )
    '''
   
   # Process with subbasin data
    process_trend_data_folder(
        csv_folder_path=csv_folder,
        shapefile_path=subbasin_shapefile,
        output_folder=output_folder,
        basin_type='subbasin',
        dpi=600
    )
