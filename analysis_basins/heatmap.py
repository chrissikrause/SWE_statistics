import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load the CSV
rain = r"C:\Innolab\output\rain\precipitation_parameter_per_hydro_year\rain_params_all_basins.csv"
df = pd.read_csv(rain)

# Original month columns (1=Jan, ... 12=Dec)
month_cols = [f"month_{i}_sum" for i in range(1, 13)]

# Reorder for hydrological year (Sep -> Aug)
hydro_month_order = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]
hydro_month_cols = [f"month_{i}_sum" for i in hydro_month_order]

# Labels for the X-axis (Sep -> Aug)
month_labels = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", 
                "Mar", "Apr", "May", "Jun", "Jul", "Aug"]

# Plot heatmaps per basin
basin_ids = df['basin_id'].unique()

for basin in basin_ids:
    df_basin = df[df['basin_id'] == basin].sort_values('hydro_year')
    plt.figure(figsize=(12, 6))
    sns.heatmap(df_basin[hydro_month_cols]*1000, annot=False, cmap="YlGnBu",
                yticklabels=df_basin['hydro_year'], xticklabels=month_labels) # nach annot: fmt=".1f"
    plt.title(f"Monthly Rainfall Sums for Basin {basin}")
    plt.xlabel("Hydrological Month (Sep → Aug)")
    plt.ylabel("Hydrological Year")
    plt.tight_layout()
    plt.savefig(rf"C:\Innolab\output\rain\heatmaps_monthly\basin_{basin}_monthly_rainfall_heatmap.png", dpi=300)
    plt.close()
