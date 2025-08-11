import pandas as pd
import os
import numpy as np
from scipy.stats import theilslopes
import pymannkendall as mk

# Define input file
input_file = "swe_parameter_per_hydro_year/swe_params_all_basins.csv"

# Variables for trend analysis
variables = [
    'max_swe', # SWE Maximum
    'day_of_max_swe', # Day of SWEmax in hydrological year
    'min_swe', # SWE Minimum
    'day_of_min_swe', # Day of SWEmin in hydrological year
    'duration_to_swe50_days', # Melt duration from SWEmax to SWE50
    'day_swe50', # Day of SWE50 in hydrological year
    'duration_to_swe10_days', # Melt duration from SWEmax to SWE10
    'day_swe10', # Day of SWE10 in hydrological year
    'day_accumulation_start', # Day of accumulation start in hydrological year
    'accumulation_duration_days', # Duration from accumulation start until SWEmax
    'snowfall_days_accumulation', # Number of days where SWE_diff > 0 during accumulation
    'snowfall_percent_accumulation', # Percentage of data points with SWE_diff > 0 during accumulation
    'constant_snowfall_start_day', # Data point where SWE_diff doesn't decrease until SWEmax (?)
    'summer_snowfall_accumulation', # Total snowfall during summer months
    'summer_snowfall_count', # Number of days with snowfall during summer months
]

# Read in Parameter table
df = pd.read_csv(input_file, parse_dates=['date_of_max_swe', 'date_of_min_swe', 'date_swe50', 'date_swe10', 'accumulation_start_date'])

basins = df['basin_id'].unique()

# Initialize dictionary to save dataframe results for each variable
results = {}

for var in variables:
    rows = []
    for basin in basins:
        basin_data = df[df['basin_id'] == basin]
        series = basin_data[var].dropna()

        # MAt least 3 values to calculate trend
        if len(series) < 3:
            rows.append({
                'basin_id': basin,
                'theil_sen_slope': np.nan,
                'theil_sen_intercept': np.nan,
                'mann_kendall_trend': None,
                'mann_kendall_p': np.nan,
                'significant': False,
                'mean': np.nan
            })
            continue

        # Calculate Theil-Sen Slope and Intercept 
        # x = Jahre (hydro_year), y = variable
        x = basin_data.loc[series.index, 'hydro_year'].values
        y = series.values

        slope, intercept, lower, upper = theilslopes(y, x, 0.95)

        # Mann-Kendall Test
        mk_result = mk.original_test(y)
        p_value = mk_result.p
        significant = p_value < 0.05
        avg=np.mean(y)
        trend_percent=slope/avg if avg!=0 else None

        rows.append({
            'basin_id': basin,
            'theil_sen_slope': slope,
            'theil_sen_intercept': intercept,
            'mann_kendall_p': p_value,
            'significant': significant,
            'mean': avg,
            'trend_percent': trend_percent
        })

    results[var] = pd.DataFrame(rows)


# === Save trend analysis results
output_folder = "trend_swe_params"
os.makedirs(output_folder, exist_ok=True)
for var, res_df in results.items():
    res_df.to_csv(os.path.join(output_folder, f"trend_results_{var}.csv"), index=False)