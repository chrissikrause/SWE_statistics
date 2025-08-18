# =====================================================
# This script processes river discharge time series for a list of basins:
#   1) Loads river discharge data from FAO and subbasin datasets
#   2) Creates hydrological year daily time series per basin and saves them as CSV
#   3) Calculates discharge parameters per hydrological year:
#      - max, min with dates and hydrological day
#      - annual mean
#      - seasonal means (DJF, MAM, JJA, SON)
#      - seasonal max/min with dates and hydrological day
#   4) Saves results as per-basin CSVs and a combined file
#
# Author: Christina Krause
# Date: 2025-08-11
# =====================================================

import pandas as pd
import os
import glob
from extract_time_series import extract_trend_data, load_time_series
from hydrological_year import assign_hydrological_year, day_in_hydro_year

# === Function to extract time series data per basin and hydrological year
def process_basins(start_year, end_year, basins, var_name, output_folder_ts,
                   path_fao, path_subbasins):

    os.makedirs(output_folder_ts, exist_ok=True)

    time_series_list_fao = load_time_series(var_name, path_fao)
    time_series_list_subbasins = load_time_series(var_name, path_subbasins)

    basin_ids_fao = {str(item['basin_id']) for item in time_series_list_fao}
    basin_ids_subbasins = {str(item['basin_id']) for item in time_series_list_subbasins}

    for basin_id in basins:
        if basin_id in basin_ids_fao:
            source_list = time_series_list_fao
        elif basin_id in basin_ids_subbasins:
            source_list = time_series_list_subbasins
        else:
            print(f"{basin_id}: Not found in FAO or Subbasin datasets")
            continue

        trend_series = extract_trend_data(source_list, basin_id, start_year, end_year)

        if trend_series is not None and not trend_series.empty:
            df = assign_hydrological_year(trend_series.to_frame(name=var_name))
            df.index.name = 'date'
            output_path = os.path.join(output_folder_ts, f"{var_name}_{basin_id}.csv")
            df.to_csv(output_path, index=True, date_format='%Y-%m-%d')
            print(f"{basin_id}: Time series saved ({len(df)} rows)")
        else:
            print(f"{basin_id}: No data in selected period")


# === Function to calculate discharge parameters from provided time series per basin and hydrological year
def calculate_discharge_parameters(input_folder, output_folder, var_name):

    os.makedirs(output_folder, exist_ok=True)
    csv_files = glob.glob(os.path.join(input_folder, f"{var_name}_*.csv"))

    all_results = []
    for file_path in csv_files:
        basin_id = os.path.basename(file_path).split("_")[1].split(".")[0]
        df = pd.read_csv(file_path, parse_dates=['date'])

        if df.empty or 'hydro_year' not in df.columns:
            print(f"{basin_id}: Empty file or missing hydro_year column")
            continue

        result_rows = []
        for year, group in df.groupby('hydro_year'):
            group = group.sort_values('date')
            hydro_year_str = group['hydro_year_str'].iloc[0]

            # === Annual max/min ===
            max_row = group.loc[group[var_name].idxmax()]
            min_row = group.loc[group[var_name].idxmin()]
            annual_mean = group[var_name].mean()
            annual_sum = group[var_name].sum()

            # === Seasonal stats ===
            seasons = {
                "DJF": [12, 1, 2],
                "MAM": [3, 4, 5],
                "JJA": [6, 7, 8],
                "SON": [9, 10, 11]
            }

            seasonal_means, seasonal_max, seasonal_min = {}, {}, {}
            for season, months in seasons.items():
                season_data = group[group['date'].dt.month.isin(months)]
                if not season_data.empty:
                    seasonal_means[season] = season_data[var_name].mean()

                    s_max_row = season_data.loc[season_data[var_name].idxmax()]
                    s_min_row = season_data.loc[season_data[var_name].idxmin()]
                    seasonal_max[season] = {
                        "value": s_max_row[var_name],
                        "date": s_max_row['date'],
                        "day": day_in_hydro_year(s_max_row['date'])
                    }
                    seasonal_min[season] = {
                        "value": s_min_row[var_name],
                        "date": s_min_row['date'],
                        "day": day_in_hydro_year(s_min_row['date'])
                    }
                else:
                    seasonal_means[season] = None
                    seasonal_max[season] = {"value": None, "date": None, "day": None}
                    seasonal_min[season] = {"value": None, "date": None, "day": None}

            
            # === Monthly stats ===
            monthly_sums = group.groupby(group['date'].dt.month)[var_name].sum()
            
            if not monthly_sums.empty:
                # Month with highest discharge
                max_discharge_month = monthly_sums.idxmax()
                max_discharge_sum = monthly_sums.max()

                # Month with lowest discharge
                min_discharge_month = monthly_sums.idxmin()
                min_discharge_sum = monthly_sums.min()

                # Difference between max and min month
                discharge_month_diff = max_discharge_sum - min_discharge_sum

                # Time distance between max and min month (in months)
                # Considers that the hydrological year runs from September to August
                def calc_month_distance(month1, month2):
                    # Convert to hydrological year (Sep=1, Oct=2, ..., Aug=12)
                    hydro_month1 = month1 - 8 if month1 >= 9 else month1 + 4
                    hydro_month2 = month2 - 8 if month2 >= 9 else month2 + 4

                    return abs(hydro_month2 - hydro_month1)
                
                month_distance = calc_month_distance(max_discharge_month, min_discharge_month)
            else:
                max_discharge_month = None
                max_discharge_sum = None
                min_discharge_month = None
                min_discharge_sum = None
                discharge_month_diff = None
                month_distance = None

            result_rows.append({
                "basin_id": basin_id,
                "hydro_year": year,
                "hydro_year_str": hydro_year_str,
                "max_discharge": max_row[var_name],
                "date_of_max": max_row['date'],
                "day_of_max": day_in_hydro_year(max_row['date']),
                "min_discharge": min_row[var_name],
                "date_of_min": min_row['date'],
                "day_of_min": day_in_hydro_year(min_row['date']),
                "annual_mean": annual_mean,
                "annual_sum": annual_sum,

                # Monthly parameters
                "max_discharge_month": max_discharge_month,
                "max_discharge_month_sum": max_discharge_sum,
                "min_discharge_month": min_discharge_month, 
                "min_discharge_month_sum": min_discharge_sum,
                "discharge_month_diff": discharge_month_diff,
                "month_distance": month_distance,

                # Seasonal parameters
                **{f"{season}_mean": seasonal_means[season] for season in seasons},
                **{f"{season}_max": seasonal_max[season]["value"] for season in seasons},
                **{f"{season}_max_date": seasonal_max[season]["date"] for season in seasons},
                **{f"{season}_max_day": seasonal_max[season]["day"] for season in seasons},
                **{f"{season}_min": seasonal_min[season]["value"] for season in seasons},
                **{f"{season}_min_date": seasonal_min[season]["date"] for season in seasons},
                **{f"{season}_min_day": seasonal_min[season]["day"] for season in seasons},
            })

        result_df = pd.DataFrame(result_rows)
        if not result_df.empty:
            all_results.append(result_df)

        output_path = os.path.join(output_folder, f"{basin_id}.csv")
        result_df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
        print(f"{basin_id}: Discharge parameters saved ({len(result_df)} years)")

    if all_results:
        big_df = pd.concat(all_results, ignore_index=True)
        big_df.to_csv(os.path.join(output_folder, f"river{var_name}_params_all_basins.csv"),
                      index=False, date_format='%Y-%m-%d')
        print(f"Combined results saved ({len(big_df)} rows)")


def main():
    start_year = 1980
    end_year = 2024
    var_name = "discharge"

    basins = [
    "4025", "4018", "4021", "4012",
    "2050013010", "2050477000", "2060491760", "2060536370", "2060548650", "2060551020", "2060551820", "2060552470",
    "2050465610", "2050540100",
    "2050008490", "2050483250", "2050488080", "2050488190", "2050514730", "2050524800", "2050539930", "2050543160",
    "2050548500", "2050548700", "2050555600", "2050557390", "2050557720", "2050569550", "2050571930", "2050575490",
    "2060016510", "2060023010", "2060420340", "2060429770", "2060441280", "2060548430", "2060548920", "2060551110",
    "2060552460", "2060536360",
    "2050008450", "2050465720", "2050476910", "2050478420", "2050478430", "2050483240", "2050487990", "2050488360",
    "2050514740", "2050525040", "2050543090", "2050555780", "2050557340", "2050557800", "2050569470", "2050575400",
    "2060023020", "2060023320", "2060023330", "2060420240", "2060429670", "2060441290", "2060491750", "2060510560",
    "2060510690", "2060548280", "2060551950"
    ]

    output_folder_ts = "output/discharge/riverdischarge_basins_timeseries"
    output_folder_params = "output/discharge/riverdischarge_parameter_per_hydro_year"

    path_fao = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\FAO_Basins\riverdischarge_series_all_additive_no_pad.pkl"
    path_subbasins = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\subbasins\riverdischarge_series_all_additive_no_pad.pkl"

    process_basins(start_year, end_year, basins, var_name, output_folder_ts,
                   path_fao, path_subbasins)

    calculate_discharge_parameters(output_folder_ts, output_folder_params, var_name)


if __name__ == "__main__":
    main()
