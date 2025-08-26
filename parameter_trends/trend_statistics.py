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


variables_rain = [
    'annual_sum', # Total precipitation per hydrological year
    'annual_max', # Maximum amount of precipitation in a day during hydrological year
    'timing_annual_max', # Day in hydrological year with maximum precipitation
    'annual_min', # Minimum amount of precipitation in a day during hydrological year
    'timing_annual_min', # Day in hydrological year with minimum precipitation
    'max_month',
    'min_month',
    'max_month_sum',
    'min_month_sum',
    'month_sum_difference',
    'month_difference',
    'monthly_cv',
    'pci',
    'DJF_sum', 'DJF_max', 'DJF_min', # Winter metrics
    'MAM_sum', 'MAM_max', 'MAM_min', # Spring metrics
    'JJA_sum', 'JJA_max', 'JJA_min', # Summer metrics
    'SON_sum', 'SON_max', 'SON_min', # Fall metrics
    'month_1_sum', 'month_1_max', 'month_1_min', # January metrics
    'month_2_sum', 'month_2_max', 'month_2_min', # February metrics
    'month_3_sum', 'month_3_max', 'month_3_min', # March metrics
    'month_4_sum', 'month_4_max', 'month_4_min', # April metrics
    'month_5_sum', 'month_5_max', 'month_5_min', # May metrics
    'month_6_sum', 'month_6_max', 'month_6_min', # June metrics
    'month_7_sum', 'month_7_max', 'month_7_min', # July metrics
    'month_8_sum', 'month_8_max', 'month_8_min', # August metrics
    'month_9_sum', 'month_9_max', 'month_9_min', # September metrics
    'month_10_sum', 'month_10_max', 'month_10_min', # October metrics
    'month_11_sum', 'month_11_max', 'month_11_min', # November metrics
    'month_12_sum', 'month_12_max', 'month_12_min' # December metrics
]


variables_riverdischarge = [
    'annual_sum', # Total river discharge per hydrological year
    'max_discharge', # Maximum discharge in a hydrological year
    'timing_annual_max', # Day of maximum discharge in a hydrological year
    'min_discharge', # Minimum discharge in a hydrological year
    'timing_annual_min', # Day of minimum discharge in a hydrological year
    'max_month', # Month with highest discharge in hydrological year
    'max_month_sum', # Sum of maximum discharge in a hydrological year
    'min_month', # Month with lowest discharge in hydrological year
    'min_month_sum', # Sum of minimum discharge in a hydrological year
    'amount_month_diff', # Total difference between max and min discharge months in hydrological year
    'month_difference', # Time lag between max and min discharge months
    'DJF_sum', 'DJF_max', 'timing_DJF_max', 'DJF_min', 'timing_DJF_min', # Winter metrics
    'MAM_sum', 'MAM_max', 'timing_MAM_max', 'MAM_min', 'timing_MAM_min', # Spring metrics
    'JJA_sum', 'JJA_max', 'timing_JJA_max', 'JJA_min', 'timing_JJA_min', # Summer metrics
    'SON_sum', 'SON_max', 'timing_SON_max', 'SON_min', 'timing_SON_min' # Fall metrics
]


input_file = r"C:\Innolab\output\swe\swe_parameter_per_hydro_year\swe_params_all_basins.csv"

output_dir = "output/swe/trend_swe_params"

trend_results = calculate_trends(
    input_file=input_file,
    variables=variables_swe,
    basin_id_col='basin_id',
    year_col='hydro_year',
    output_folder=output_dir,
    significance_level=0.05
)
