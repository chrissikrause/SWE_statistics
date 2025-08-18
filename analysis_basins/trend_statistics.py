import pandas as pd
import os
import numpy as np
from scipy.stats import theilslopes
import pymannkendall as mk


def calculate_trends(
    input_file: str,
    variables: list[str],
    basin_id_col: str = 'basin_id',
    year_col: str = 'hydro_year',
    output_folder: str = 'trend_swe_params',
    significance_level: float = 0.05
) -> dict[str, pd.DataFrame]:
    """
    Calculate Theil-Sen slope, intercept, Mann-Kendall trend and other stats for multiple variables per basin.
    
    Args:
        input_file: Path to the CSV file containing data.
        variables: List of variable column names to analyze.
        basin_id_col: Column name for basin IDs.
        year_col: Column name for the time variable (e.g., year).
        output_folder: Folder to save results CSV files.
        significance_level: p-value cutoff for significance.
    
    Returns:
        Dictionary mapping variable names to their trend results DataFrame.
    """
    df = pd.read_csv(input_file)
    basins = df[basin_id_col].unique()
    
    results = {}
    os.makedirs(output_folder, exist_ok=True)
    
    for var in variables:
        rows = []
        for basin in basins:
            basin_data = df[df[basin_id_col] == basin]
            series = basin_data[var].dropna()
            
            # Require at least 3 values to calculate trend
            if len(series) < 3:
                rows.append({
                    basin_id_col: basin,
                    'theil_sen_slope': np.nan,
                    'theil_sen_intercept': np.nan,
                    'mann_kendall_p': np.nan,
                    'significant': False,
                    'mean': np.nan,
                    'trend_percent': None
                })
                continue
            
            x = basin_data.loc[series.index, year_col].values
            y = series.values
            
            slope, intercept, _, _ = theilslopes(y, x, 0.95)
            mk_result = mk.original_test(y)
            p_value = mk_result.p
            significant = p_value < significance_level
            avg = np.mean(y)
            trend_percent = slope / avg if avg != 0 else None
            
            rows.append({
                basin_id_col: basin,
                'theil_sen_slope': slope,
                'theil_sen_intercept': intercept,
                'mann_kendall_p': p_value,
                'significant': significant,
                'mean': avg,
                'trend_percent': trend_percent
            })
        
        result_df = pd.DataFrame(rows)
        results[var] = result_df
        
        # Save to CSV
        output_path = os.path.join(output_folder, f"trend_results_{var}.csv")
        result_df.to_csv(output_path, index=False)
    
    return results



# Variables for trend analysis
variables_swe = [
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
    'summer_snowfall_days', # Number of days with snowfall during summer months
]


variables_rain = [
    'annual_sum', # Total precipitation per hydrological year
    'annual_max', # Maximum amount of precipitation in a day during hydrological year
    'annual_max_day', # Day in hydrological year with maximum precipitation
    'annual_min', # Minimum amount of precipitation in a day during hydrological year
    'annual_min_day', # Day in hydrological year with minimum precipitation
    'max_month',
    'min_month',
    'max_month_sum',
    'min_month_sum',
    'month_sum_diff',
    'month_distance_hydro',
    'monthly_cv',
    'pci',
    #'DJF_sum', 'DJF_mean', 'DJF_max_val', 'DJF_max_day', 'DJF_min_val', 'DJF_min_day', # Winter metrics
    #'MAM_sum', 'MAM_mean', 'MAM_max_val', 'MAM_max_day', 'MAM_min_val', 'MAM_min_day', # Spring metrics
    #'JJA_sum', 'JJA_mean', 'JJA_max_val', 'JJA_max_day', 'JJA_min_val', 'JJA_min_day', # Summer metrics
    #'SON_sum', 'SON_mean', 'SON_max_val', 'SON_max_day', 'SON_min_val', 'SON_min_day', # Fall metrics
    'month_1_sum', 'month_1_max_val', 'month_1_min_val', # January metrics
    'month_2_sum', 'month_2_max_val', 'month_2_min_val', # February metrics
    'month_3_sum', 'month_3_max_val', 'month_3_min_val', # March metrics
    'month_4_sum', 'month_4_max_val', 'month_4_min_val', # April metrics
    'month_5_sum', 'month_5_max_val', 'month_5_min_val', # May metrics
    'month_6_sum', 'month_6_max_val', 'month_6_min_val', # June metrics
    'month_7_sum', 'month_7_max_val', 'month_7_min_val', # July metrics
    'month_8_sum', 'month_8_max_val', 'month_8_min_val', # August metrics
    'month_9_sum', 'month_9_max_val', 'month_9_min_val', # September metrics
    'month_10_sum', 'month_10_max_val', 'month_10_min_val', # October metrics
    'month_11_sum', 'month_11_max_val', 'month_11_min_val', # November metrics
    'month_12_sum', 'month_12_max_val', 'month_12_min_val', # December metrics
]


variables_riverdischarge = [
    'annual_sum', # Total river discharge per hydrological year
    'max_discharge', # Maximum discharge in a hydrological year
    'day_of_max', # Day of maximum discharge in a hydrological year
    'min_discharge', # Minimum discharge in a hydrological year
    'day_of_min', # Day of minimum discharge in a hydrological year
    'max_discharge_month', # Month with highest discharge in hydrological year
    'min_discharge_month', # Month with lowest discharge in hydrological year
    'discharge_month_diff', # Total difference between max and min discharge months in hydrological year
    'month_distance', # Time lag between max and min discharge months
    'DJF_mean', 'DJF_max', 'DJF_max_day', 'DJF_min', 'DJF_min_day', # Winter metrics
    'MAM_mean', 'MAM_max', 'MAM_max_day', 'MAM_min', 'MAM_min_day', # Spring metrics
    'JJA_mean', 'JJA_max', 'JJA_max_day', 'JJA_min', 'JJA_min_day', # Summer metrics
    'SON_mean', 'SON_max', 'SON_max_day', 'SON_min', 'SON_min_day' # Fall metrics
]


input_file = r"C:\Innolab\output\rain\precipitation_parameter_per_hydro_year\rain_params_all_basins.csv"

output_dir = "output/rain/trend_rain_params"

trend_results = calculate_trends(
    input_file=input_file,
    variables=variables_rain,
    basin_id_col='basin_id',
    year_col='hydro_year',
    output_folder=output_dir,
    significance_level=0.05
)
