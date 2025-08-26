# This script should create functions for:
# scatterplots from all variables in the var list
# and iterate through all variable trend files and create scatterplots 
# for each basin where then all variables are correlated with each other per basin

# the problem is that the files in trend_folder are per variable and contain a row with trend_percent for each basin
# but for the scatterplot the data must be grouped to basin and then all variables from the different files per basin correlated
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


params = r"C:\Innolab\output\swe\swe_parameter_per_hydro_year\swe_params_all_basins.csv"


variables_swe = [
    'max_swe', # SWE Maximum
    'timing_of_max_swe', # Day of SWEmax in hydrological year
    'min_swe', # SWE Minimum
    'timing_of_min_swe', # Day of SWEmin in hydrological year
    'melt_duration_to_swe50', # Melt duration from SWEmax to SWE50
    'timing_swe50', # Day of SWE50 in hydrological year
    'melt_duration_to_swe10', # Melt duration from SWEmax to SWE10
    'timing_swe10', # Day of SWE10 in hydrological year
    'timing_accumulation_start', # Day of accumulation start in hydrological year
    'accumulation_duration', # Duration from accumulation start until SWEmax
    'snowfall_days_accumulation', # Number of days where SWE_diff > 0 during accumulation
    'snowfall_percent_accumulation', # Percentage of data points with SWE_diff > 0 during accumulation
    'timing_constant_snowfall_start', # Data point where SWE_diff doesn't decrease until SWEmax (?)
    'summer_snowfall_accumulation', # Total snowfall during summer months
    'number_of_days_summer_snowfall', # Number of days with snowfall during summer months
    'DJF_min_swe', 'DJF_max_swe', 'DJF_timing_max_swe', 'DJF_timing_min_swe', # Winter metrics
    'MAM_min_swe', 'MAM_max_swe', 'MAM_timing_max_swe', 'MAM_timing_min_swe', # Spring metrics
    'JJA_min_swe', 'JJA_max_swe', 'JJA_timing_max_swe', 'JJA_timing_min_swe', # Summer metrics
    'SON_min_swe', 'SON_max_swe', 'SON_timing_max_swe', 'SON_timing_min_swe' # Fall metrics
]


# Step 1: Daten einlesen
df = pd.read_csv(params)

# erwartet: Spalten [basin_id, hydro_year, ...variablen...]

# Step 2: Scatterplots pro Becken
output_folder = os.path.join(r"C:\Innolab\output\swe", "swe_scatterplots")
os.makedirs(output_folder, exist_ok=True)

for basin_id, basin_df in df.groupby("basin_id"):
    basin_subset = basin_df[variables_swe]

    # Pairplot (alle Variablen gegeneinander)
    g = sns.pairplot(basin_subset, diag_kind="kde", plot_kws={"alpha":0.5, "s":20})
    g.fig.suptitle(f"Basin {basin_id} – Scatterplots aller Variablen", y=1.02)

    # speichern
    g.savefig(os.path.join(output_folder, f"basin_{basin_id}_pairplot.png"), dpi=150)
    plt.close()

    # Korrelationsmatrix als Heatmap
    corr = basin_subset.corr()
    plt.figure(figsize=(10,8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True, cbar=True)
    plt.title(f"Basin {basin_id} – Korrelationsmatrix")
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"basin_{basin_id}_correlation.png"), dpi=150)
    plt.close()

print("✅ Scatterplots + Korrelationsmatrizen erstellt in:", output_folder)
