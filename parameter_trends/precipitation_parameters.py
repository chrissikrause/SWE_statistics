# =====================================================
# This script processes precipitation time series for a list of basins:
#   1) Loads precipitation data from FAO and subbasin datasets
#   2) Creates hydrological year time series per basin and saves them as CSV
#   3) Calculates precipitation parameters per hydrological year:
#      - annual mean and sum
#      - annual max/min with dates and hydrological day
#      - seasonal sum, mean, max/min with dates and hydrological day
#      - monthly sum, mean, max/min with dates and hydrological day
#   4) Saves results as per-basin CSVs and a combined file
#
# Author: [Your Name]
# Date: 2025-08-11
# =====================================================

import pandas as pd
import os
import glob
import numpy as np
from parameter_trends.extract_time_series import load_time_series, extract_trend_data
from parameter_trends.hydrological_year import assign_hydrological_year, day_in_hydro_year


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


# === Function to calculate precipitation parameters from provided time series per basin and hydrological year
def calculate_precip_parameters(input_folder, output_folder, var_name):
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

            # Annual metrics
            annual_sum = group[var_name].sum()
            annual_mean = group[var_name].mean()
            max_row = group.loc[group[var_name].idxmax()]
            min_row = group.loc[group[var_name].idxmin()]

            # Seasonal metrics
            seasons = {
                "DJF": [12, 1, 2],
                "MAM": [3, 4, 5],
                "JJA": [6, 7, 8],
                "SON": [9, 10, 11]
            }
            seasonal_data = {}
            for season, months in seasons.items():
                season_group = group[group['date'].dt.month.isin(months)]
                if not season_group.empty:
                    s_sum = season_group[var_name].sum()
                    s_mean = season_group[var_name].mean()
                    s_max = season_group.loc[season_group[var_name].idxmax()]
                    s_min = season_group.loc[season_group[var_name].idxmin()]
                    seasonal_data[season] = {
                        "sum": s_sum,
                        "max": s_max[var_name],
                        "max_date": s_max['date'],
                        "max_day": day_in_hydro_year(s_max['date']),
                        "min": s_min[var_name],
                        "min_date": s_min['date'],
                        "min_day": day_in_hydro_year(s_min['date']),
                    }
                else:
                    seasonal_data[season] = {
                        "sum": None, "mean": None,
                        "max": None, "max_date": None, "max_day": None,
                        "min": None, "min_date": None, "min_day": None,
                    }

            # Monthly metrics
            monthly_data = {}
            for month, month_group in group.groupby(group['date'].dt.month):
                if not month_group.empty:
                    m_sum = month_group[var_name].sum()
                    m_mean = month_group[var_name].mean()
                    m_max = month_group.loc[month_group[var_name].idxmax()]
                    m_min = month_group.loc[month_group[var_name].idxmin()]
                    monthly_data[month] = {
                        "sum": m_sum,
                        "max": m_max[var_name],
                        "max_date": m_max['date'],
                        "max_day": day_in_hydro_year(m_max['date']),
                        "min": m_min[var_name],
                        "min_date": m_min['date'],
                        "min_day": day_in_hydro_year(m_min['date']),
                    }
                else:
                    monthly_data[month] = {
                        "sum": None, 
                        "max": None, 
                        "max_date": None, 
                        "max_day": None,
                        "min": None, 
                        "min_date": None, 
                        "min_day": None,
                    }
            

            # Collect results
            row = {
                "basin_id": basin_id,
                "hydro_year": year,
                "hydro_year_str": hydro_year_str,
                "annual_sum": annual_sum,
                "annual_mean": annual_mean,
                "annual_max": max_row[var_name],
                "annual_max_date": max_row['date'],
                "timing_annual_max": day_in_hydro_year(max_row['date']),
                "annual_min": min_row[var_name],
                "annual_min_date": min_row['date'],
                "timing_annual_min": day_in_hydro_year(min_row['date']),
            }

            # Add seasonal to row
            for season in seasons:
                for metric in ["sum", "max", "min"]:
                    row[f"{season}_{metric}"] = seasonal_data[season][metric]

            # Add monthly to row
            for month in range(1, 13):
                for metric in ["sum", "max", "min"]:
                    row[f"month_{month}_{metric}"] = monthly_data.get(month, {}).get(metric, None)

            valid_month_sums = {m: monthly_data[m]["sum"] for m in monthly_data if monthly_data[m]["sum"] is not None}
            if valid_month_sums:
                max_month = max(valid_month_sums, key=valid_month_sums.get)
                min_month = min(valid_month_sums, key=valid_month_sums.get)
                max_month_sum = valid_month_sums[max_month]
                min_month_sum = valid_month_sums[min_month]
                diff_month_sum = max_month_sum - min_month_sum

                def calc_month_distance(month1, month2):
                    hydro_month1 = month1 - 8 if month1 >= 9 else month1 + 4
                    hydro_month2 = month2 - 8 if month2 >= 9 else month2 + 4
                    return abs(hydro_month2 - hydro_month1)

                month_distance = calc_month_distance(max_month, min_month)

                # Liste aller Monatsniederschläge (Summe) als Array
                arr = np.array(list(valid_month_sums.values()))

                # Variationskoeffizient
                row["monthly_cv"] = arr.std() / arr.mean()
               

                # Precipitation Concentration Index (PCI, Oliver 1980)
                row["pci"] = 100 * (np.sum((arr*1000)**2) / (np.sum((arr*1000)**2))) # zuerst m-> mm


                row["max_month"] = max_month
                row["min_month"] = min_month
                row["max_month_sum"] = max_month_sum
                row["min_month_sum"] = min_month_sum
                row["month_sum_difference"] = diff_month_sum
                row["month_difference"] = month_distance
            else:
                row["max_month"] = None
                row["min_month"] = None
                row["max_month_sum"] = None
                row["min_month_sum"] = None
                row["month_sum_difference"] = None
                row["month_difference"] = None
                row["monthly_cv"] = None
                row["pci"] = None
            result_rows.append(row)

        result_df = pd.DataFrame(result_rows)
        if not result_df.empty:
            all_results.append(result_df)

        output_path = os.path.join(output_folder, f"{basin_id}.csv")
        result_df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
        print(f"{basin_id}: Precipitation parameters saved ({len(result_df)} years)")

    if all_results:
        big_df = pd.concat(all_results, ignore_index=True)
        big_df.to_csv(os.path.join(output_folder, f"{var_name}_params_all_basins.csv"),
                      index=False, date_format='%Y-%m-%d')
        print(f"Combined results saved ({len(big_df)} rows)")


def main():
    start_year = 1980
    end_year = 2024
    var_name = "rain"

    basins = [
    "4025", "4018", "4021", "4012",
    "2050477000", "2060491760", "2060536370", "2060548650", "2060551020", "2060551820", "2060552470",
    "2050465610", "2050540100",
    "2050008490", "2050483250", "2050488080", "2050488190", "2050514730", "2050524800", "2050539930", "2050543160",
    "2050548500", "2050548700", "2050555600", "2050557390", "2050557720", "2050569550", "2050575490",
    "2060016510", "2060023010", "2060420340", "2060429770", "2060441280", "2060548430", "2060548920", "2060551110",
    "2060552460", "2060536360",
    "2050008450", "2050465720", "2050476910", "2050478420", "2050478430", "2050483240", "2050487990", "2050488360",
    "2050514740", "2050525040", "2050543090", "2050555780", "2050557340", "2050557800", "2050569470", "2050575400",
    "2060023020", "2060023320", "2060023330", "2060420240", "2060429670", "2060441290", "2060491750", "2060510560",
    "2060510690", "2060548280", "2060551950", "2060571930", "2060572030", "2060013010"
    ]

    output_folder_ts = "output/rain/precipitation_basins_timeseries"
    output_folder_params = "output/rain/precipitation_parameter_per_hydro_year"

    path_fao = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\FAO_Basins\rain_series_all_additive_no_pad.pkl"
    path_subbasins = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\subbasins\rain_series_all_additive_no_pad.pkl"

    process_basins(start_year, end_year, basins, var_name, output_folder_ts,
                    path_fao, path_subbasins)


    calculate_precip_parameters(output_folder_ts, output_folder_params, var_name)


if __name__ == "__main__":
    main()
