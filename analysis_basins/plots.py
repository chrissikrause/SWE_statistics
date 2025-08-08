import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import theilslopes, kendalltau
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from matplotlib.colors import SymLogNorm

#     results_df['trend_percent'] = results_df['slope']/results_df['mean_overall']



# Min-max normalize a column to [-1, 1]
def normalize_trends(df):
    """
    Normalizes the 'trend_percent' column in the DataFrame to a scale of -1 to 1
    while preserving the sign of the original values.

    Parameters:
    - df: pandas DataFrame with a 'trend_percent' column.

    Returns:
    - df: DataFrame with an added 'normalized_trend' column.
    """
    # Ensure the column exists
    if 'trend_percent' not in df.columns:
        raise ValueError("'trend_percent' column is missing from the DataFrame.")

    # Normalize with respect to the maximum and minimum absolute values
    abs_trends = np.abs(df['trend_percent'])
    max_trend = abs_trends.max()

    # Normalize by max value while keeping the sign
    df['normalized_trend'] = np.sign(df['trend_percent']) * (abs_trends / max_trend)

    return df





#%%plot
# Create a custom colormap




def plot(input_df, save_path=None, dpi=300):
    merged_gdf = filtered_gdf.merge(input_df, on='basin_id', how='inner')
    

    
    # colors = [
    #     (0.0, "#18435A"),  # Deep blue at 0% (start)
    
    #     (0.05, "#29749C"),  # Intermediate light blue at 15%
        
    
    #     (0.47, "#DCEDF6"),  # Intermediate off-white at 40%
    #     (0.5, "#FEFAEF"),  # Off-white at 50%
    
    #     (0.53, "#F4E1E5"),  # Intermediate light red at 60%
        
    
    #     (0.95, "#A63C54"),  # Intermediate deep red at 85%
    #     (1.0, "#6B2737"),   # Deep red at 100% (end)
    # ]
    
    
    colors = [
    (0.0, "#6B2737"),  # Deep red at 0% (start)

    (0.05, "#A63C54"),  # Intermediate deep red at 15%
    
    (0.47, "#F4E1E5"),  # Intermediate light red at 40%
    (0.5, "#FEFAEF"),   # Off-white at 50%

    (0.53, "#DCEDF6"),  # Intermediate off-white at 60%
    
    (0.95, "#29749C"),  # Intermediate light blue at 85%
    (1.0, "#18435A"),   # Deep blue at 100% (end)
    ]
    
    # Create a custom colormap with more smooth transitions
    custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)
    
    # Calculate robust min and max for normalization
    percentile_5 = np.percentile(merged_gdf['normalized_trend'], 5)
    percentile_95 = np.percentile(merged_gdf['normalized_trend'], 95)
    
    epsilon = 1e-24
    vmin = min(percentile_5, -epsilon)
    vmax = max(percentile_95, epsilon)
    
    # Define normalization range using robust percentiles
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(18, 6))
    
    # Plot the entire basins in light grey first
    gdf.plot(ax=ax, color='#DDE3E7', edgecolor='white', linewidth=0.9)
    filtered_gdf.plot(ax=ax, color='#B3C2CA', edgecolor='white', linewidth=0.9)
    
    # Overlay the basins with colors according to normalized_trend
    merged_gdf.plot(
        ax=ax,
        column='normalized_trend',
        cmap=custom_cmap,
        edgecolor='black',
        linewidth=0.9,
        norm=norm
    )
    
    # Add hatched layer for basins with significance of 1
    basins_significance_1 = merged_gdf[merged_gdf['significant'] == 1]
    basins_significance_1.plot(
        ax=ax,
        color='none',
        edgecolor='black',  # Remove the outline
        linewidth=0,       # Ensure no additional outline
        hatch='/',
        zorder=7  # Draw this on top of the overlay
    )
    
    # Set the aspect ratio to 'auto'
    ax.set_aspect('auto')
    
    # Limit the plot to the northern hemisphere (latitude > 0)
    ax.set_ylim(0, 90)
    ax.set_xlim(-180, 180)
    
    # Hide the axes
    ax.axis('off')
    
    # Save the plot if a save_path is provided
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    # Show the plot
    plt.show()
    
    
    
    
plot(normalized_df_dis)
plot(normalized_df_evo)
    
plot(normalized_df_snow)
plot(normalized_df_rain)
plot(normalized_df_glacier)
plot(normalized_df_soilmoisture)
plot(normalized_df_groundwater)
plot(normalized_df_temp)




plot(normalized_df_dis, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/discharge.tif", dpi=600)
plot(normalized_df_evo, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/evo.tif", dpi=600)


plot(normalized_df_snow, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/snow.tif", dpi=600)
plot(normalized_df_rain, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/rain.tif", dpi=600)
plot(normalized_df_glacier, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/glacier.tif", dpi=600)
plot(normalized_df_soilmoisture, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/soilmoisture.tif", dpi=600)
plot(normalized_df_groundwater, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/groundwater.tif", dpi=600)
plot(normalized_df_temp, save_path="C:/Users/schi_sm/Documents/_2_Papers/Snow_Rivers/Manuscript/Figures/Multiplot/temp.tif", dpi=600)



# def plot_all(dataframes, filtered_gdf, gdf):
#     # Custom colormap
#     custom_cmap = LinearSegmentedColormap.from_list(
#         "custom_cmap", ["#29749C", "#FEFAEF", "#A63C54"]
#     )

#     # Create a 2x4 subplot layout
#     fig, axes = plt.subplots(4, 2, figsize=(8.3,11.7))  # A4 size in inches: 11.7x8.3
#     axes = axes.flatten()

#     for ax, (input_df, title) in zip(axes, dataframes):
#         # Merge the GeoDataFrame with input DataFrame
#         merged_gdf = filtered_gdf.merge(input_df, on='basin_id', how='inner')

#         # Calculate robust min and max for normalization
#         percentile_5 = np.percentile(merged_gdf['normalized_trend'], 5)
#         percentile_95 = np.percentile(merged_gdf['normalized_trend'], 95)

#         epsilon = 1e-24
#         vmin = min(percentile_5, -epsilon)
#         vmax = max(percentile_95, epsilon)

#         # Define normalization range using robust percentiles
#         norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

#         # Plot the entire basins in light grey first
#         gdf.plot(ax=ax, color='#DDE3E7', edgecolor='white', linewidth=0.5)
#         filtered_gdf.plot(ax=ax, color='#B3C2CA', edgecolor='white', linewidth=0.5)

#         # Overlay the basins with colors according to normalized_trend
#         merged_gdf.plot(
#             ax=ax,
#             column='normalized_trend',
#             cmap=custom_cmap,
#             edgecolor='black',
#             linewidth=0.5,
#             norm=norm
#         )

#         # Add hatched layer for basins with significance of 1
#         basins_significance_1 = merged_gdf[merged_gdf['significant'] == 1]
#         basins_significance_1.plot(
#             ax=ax,
#             color='none',
#             edgecolor='#094749',
#             linewidth=0,
#             hatch='//',
#             zorder=7
#         )

#         # Set the aspect ratio to 'auto'
#         ax.set_aspect('auto')

#         # Limit the plot to the northern hemisphere
#         ax.set_ylim(0, 90)
#         ax.set_xlim(-180, 180)

#         # Add a title to each subplot
#         ax.set_title(title, fontsize=10, fontname="Frutiger")

#         # Remove axes for cleaner presentation
#         ax.axis('off')

#     # Adjust layout to fit on the A4 page
#     fig.tight_layout()

#     # Save the figure
#     plt.savefig("A4_page_plots.pdf", dpi=300)
#     plt.show()


# # List of dataframes and titles for the plots
# dataframes = [
#     (normalized_df_dis, "Discharge"),
#     (normalized_df_snow, "Snow"),
#     (normalized_df_rain, "Rain"),
#     (normalized_df_glacier, "Glacier"),
#     (normalized_df_soilmoisture, "Soil Moisture"),
#     (normalized_df_groundwater, "Groundwater"),
#     (normalized_df_temp, "Temperature"),
#     (normalized_df_evo, "Evaporation")
# ]

# plot_all(dataframes, filtered_gdf, gdf)

