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



def plot_trend_analysis(df, title, file_name, save_path=None, dpi=600, fao_shapefile=None):
    """
    Plot trend analysis results mit dynamischer Normalisierung
    - Variablen aus not_normalized_var oder mit 'day' im Namen werden NICHT normalisiert
    """

    not_normalized_params = [
        'max_month', 'min_month', 'month_difference',
        'min_discharge_month', 'max_discharge_month', 
        'number_of_days_summer_snowfall',
        'melt_duration_to_swe50', 'melt_duration_to_swe10', 'accumulation_duration',
        'snowfall_days_accumulation'
        # alle Variablen mit "timing" werden zusätzlich dynamisch erkannt
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

    # Dateiname checken, um zu entscheiden, welche Variable verwendet wird
    file_name_lower = file_name.lower()
    if any(param in file_name_lower for param in not_normalized_params) or "timing" in file_name_lower:
        variable_name = "theil_sen_slope"  # statt trend_percent
    else:
        variable_name = "trend_percent"

    # Normalize Trend data for plotting
    if variable_name == "theil_sen_slope":
        # nicht normalisieren
        df["trend_normalized"] = df[variable_name]
        max_abs = df["trend_normalized"].abs().max()
        if max_abs == 0:
            max_abs = 1  # Vermeidung von Division durch Null, falls alle Werte 0
        norm_trend = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
        cbar_label_trend = "Theil Sen Slope (days)"
    else:
        # normalisieren
        df["trend_normalized"] = df[variable_name] / df[variable_name].abs().max()
        norm_trend = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
        cbar_label_trend = "Normalized Theil Sen Slope"

    # Normalize Mean data for plotting
    df["mean_normalized"] = df["mean"]
    norm_mean = Normalize(vmin=0, vmax=df["mean"].abs().max())
    if variable_name == "theil_sen_slope":
        cbar_label_mean = f"Mean (days)"
    else:
        cbar_label_mean = f"Mean"
    
    
    # Plot-Setup
    fig, (ax_trend, ax_mean) = plt.subplots(1, 2, figsize=(20, 8))


    # === Trend Plot
    # Basins grau
    df.plot(ax=ax_trend, color='#DDE3E7', edgecolor='white', linewidth=0.9)
    df.plot(
        ax=ax_trend,
        column='trend_normalized',
        cmap=custom_cmap,
        edgecolor='black',
        linewidth=0.9,
        norm=norm_trend
    )

    # Signifikanz
    basins_significance = df[df['significant'] == True]
    if not basins_significance.empty:
        basins_significance.plot(
            ax=ax_trend, color='none', edgecolor='black', linewidth=0,
            hatch='/', zorder=7
        )

    ax_trend.set_aspect('auto')
    ax_trend.set_title(title, fontsize=10, fontname="Frutiger")
    ax_trend.axis('off')

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm_trend)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_trend, orientation='horizontal', fraction=0.1, pad=0.04)
    cbar.set_label(cbar_label_trend, fontsize=10, fontname="Frutiger")

    # Legende für Signifikanz
    hatch_patch = mpatches.Patch(
        facecolor='white', hatch='///', edgecolor='black',
        label='Mann Kendall Significance'
    )
    ax_trend.legend(handles=[hatch_patch], loc='lower left', fontsize=10)

    if fao_shapefile is not None:
        fao_gdf = gpd.read_file(fao_shapefile)
        fao_gdf.boundary.plot(ax=ax_trend, edgecolor="black", linewidth=2.5, zorder=10)


    # === Mean Plot
    # Basins grau
    df.plot(ax=ax_mean, color='#DDE3E7', edgecolor='white', linewidth=0.9)
    df.plot(
        ax=ax_mean,
        column='mean_normalized',
        cmap=custom_cmap,
        edgecolor='black',
        linewidth=0.9,
        norm=norm_mean
    )

    ax_mean.set_aspect('auto')
    ax_mean.set_title(f"{title} – Mean per Basin", fontsize=12, fontname="Frutiger")
    ax_mean.axis('off')

    sm_mean = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm_mean)
    sm_mean.set_array([])
    cbar_mean = fig.colorbar(sm_mean, ax=ax_mean, orientation='horizontal', fraction=0.1, pad=0.04)
    cbar_mean.set_label(cbar_label_mean)

    if fao_shapefile is not None:
        fao_gdf.boundary.plot(ax=ax_mean, edgecolor="black", linewidth=2.5, zorder=10)

    plt.tight_layout()


    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)



def process_trend_data_folder(csv_folder_path, shapefile_path, output_folder, 
                            basin_type='basin', dpi=600, fao_shapefile=None):
    """
    Process all CSV files in a folder and create trend analysis plots
    """
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Load shapefile
    input_shp = gpd.read_file(shapefile_path)
    
    # Determine the ID column based on basin_type
    if basin_type.lower() == 'basin':
        id_column = 'basin_id'
        if 'MAJ_BAS' in input_shp.columns:
            input_shp = input_shp.rename(columns={'MAJ_BAS': 'basin_id'})
    elif basin_type.lower() == 'subbasin':
        id_column = 'basin_id'
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
    
    for csv_file in csv_files:
        try:
            print(f"Processing: {os.path.basename(csv_file)}")
            
            trend_df = pd.read_csv(csv_file)
            required_columns = [id_column, 'trend_percent', 'theil_sen_slope', 'significant']
            missing_columns = [col for col in required_columns if col not in trend_df.columns]
            if missing_columns:
                print(f"Warning: Missing columns {missing_columns} in {csv_file}. Skipping...")
                continue
            
            merged_df = input_shp.merge(trend_df, on=id_column, how='inner')
            if merged_df.empty:
                print(f"Warning: No matching records found for {csv_file}. Skipping...")
                continue
            
            filename_without_ext = os.path.splitext(os.path.basename(csv_file))[0]
            title = filename_without_ext.replace('_', ' ').title()
            output_filename = f"{filename_without_ext}.png"
            output_path = os.path.join(output_folder, output_filename)
            
            plot_trend_analysis(merged_df, title=title, file_name=filename_without_ext, save_path=output_path, dpi=dpi, fao_shapefile=fao_shapefile)
            print(f"Successfully created plot: {output_filename}")
            
        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")
            continue
    
    print("Processing completed!")



# Example usage
if __name__ == "__main__":
    # Define paths
    csv_folder = r"C:\Innolab\output\swe\trend_swe_params"
    basin_shapefile = r"C:\Innolab\Daten_fuer_Christina\Data\Basins\FAO_Basins\alpine_basins.shp"
    subbasin_shapefile = r"C:\Innolab\Daten_fuer_Christina\Data\Basins\Subbasins\alpine_subbasins.shp"  # Adjust path as needed
    output_folder = r"C:\Innolab\output\swe\trend_maps_swe_FAO_basins"

    
    # Process with basin data
    process_trend_data_folder(
        csv_folder_path=csv_folder,
        shapefile_path=basin_shapefile,
        output_folder=output_folder,
        basin_type='basin',
        dpi=600,
        fao_shapefile=basin_shapefile
    )

    '''

    # Process with subbasin data
    process_trend_data_folder(
        csv_folder_path=csv_folder,
        shapefile_path=subbasin_shapefile,
        output_folder=output_folder,
        basin_type='subbasin',
        dpi=600,
        fao_shapefile=basin_shapefile
    )
    '''
    
    