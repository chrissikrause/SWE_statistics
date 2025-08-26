# =====================================================
# This script processes SWE (Snow Water Equivalent) time series
# for a list of basins:
#   1) Loads SWE data from FAO and subbasin datasets
#   2) Creates hydrological year daily time series per basin and saves them as CSV
#   3) Calculates SWE parameters per hydrological year:
#      - max/min SWE + date
#      - melt-off durations (50% / 10% of peak)
#      - accumulation period characteristics
#      - summer snowfall events
#   4) Saves results as per-basin CSVs and a combined file
#
# Author: Christina Krause
# Date: 2025-08-11
# =====================================================

# === Imports ===
import pandas as pd
import os
import glob
from extract_time_series import load_time_series, extract_trend_data
from hydrological_year import assign_hydrological_year, day_in_hydro_year


# === Function to extract time series data per basin and hydrological year
def process_basins(start_year, end_year, basins, var_name, output_folder,
                   path_fao, path_subbasins):
    os.makedirs(output_folder, exist_ok=True)

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
            output_path = os.path.join(output_folder, f"{var_name}_{basin_id}.csv")
            df.to_csv(output_path, index=True, date_format='%Y-%m-%d')
            print(f"{basin_id}: Time series saved ({len(df)} rows)")
        else:
            print(f"{basin_id}: No data in selected period")


# === Function to calculate snow parameters from provided time series per basin and hydrological year
def calculate_swe_parameters(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    csv_files = glob.glob(os.path.join(input_folder, "swe_*.csv"))

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

            # === Max/Min SWE ===
            max_row = group.loc[group['swe'].idxmax()]
            min_row = group.loc[group['swe'].idxmin()]

            # === Summer snowfall ===
            summer = group[group['date'].dt.month.isin([6, 7, 8])].copy()
            summer['swe_diff'] = summer['swe'].diff()
            summer_snowfall = summer[summer['swe_diff'] > 0]
            summer_snowfall_acc = summer_snowfall['swe_diff'].sum()
            summer_snowfall_count = len(summer_snowfall)

            # === Melt-off ===
            peak_date, peak_value = max_row['date'], max_row['swe']
            after_peak = group[group['date'] > peak_date]
            swe50_row = after_peak[after_peak['swe'] <= peak_value * 0.5].head(1)
            swe10_row = after_peak[after_peak['swe'] <= peak_value * 0.1].head(1)

            swe50_date = swe50_row['date'].values[0] if not swe50_row.empty else None
            swe10_date = swe10_row['date'].values[0] if not swe10_row.empty else None
            duration_to_swe50 = (pd.to_datetime(swe50_date) - pd.to_datetime(peak_date)).days if swe50_date else None
            duration_to_swe10 = (pd.to_datetime(swe10_date) - pd.to_datetime(peak_date)).days if swe10_date else None

            # === Accumulation ===
            group = group.reset_index(drop=True)
            group['swe_diff'] = group['swe'].diff()
            acc_start_date = None
            for i in range(1, len(group)):
                if group.loc[i, 'swe_diff'] > 0:
                    acc_start_date = group.loc[i, 'date']
                    break

            duration_accumulation = (pd.to_datetime(peak_date) - pd.to_datetime(acc_start_date)).days if acc_start_date else None
            if acc_start_date is not None:
                accum_period = group[(group['date'] >= acc_start_date) & (group['date'] <= peak_date)]
                snowfall_days_accum = (accum_period['swe_diff'] > 0).sum()
                perc_snowfall_accum = snowfall_days_accum / len(accum_period) if len(accum_period) > 0 else None

                constant_snowfall_date = None
                swe_values = accum_period['swe'].values
                swe_diff = accum_period['swe_diff'].values
                dates = accum_period['date']

                imax = swe_values.argmax()  # Index of SWE max in accumulation period

                for i in range(len(swe_diff)):
                    if swe_diff[i] > 0:
                        swe_start = swe_values[i]
                        # Condition: no value smaller than swe_start until the peak
                        if (swe_values[i:imax+1] >= swe_start).all():
                            constant_snowfall_date = dates.iloc[i]
                            break
            else:
                snowfall_days_accum = None
                perc_snowfall_accum = None
                constant_snowfall_date = None
            
            def assign_season(month):
                if month in [12, 1, 2]:
                    return "DJF"
                elif month in [3, 4, 5]:
                    return "MAM"
                elif month in [6, 7, 8]:
                    return "JJA"
                else:
                    return "SON"

            group['season'] = group['date'].dt.month.map(assign_season)

            season_stats = group.groupby('season')['swe'].agg(['min', 'max']).reset_index()

            # Um die Ergebnisse pro Jahr und Becken zu den Parametern hinzuzufügen:
            season_dict = {}
            for _, row in season_stats.iterrows():
                season = row['season']
                season_dict[f"{season}_min_swe"] = row['min']
                season_dict[f"{season}_max_swe"] = row['max']
                season_dict[f"{season}_timing_max_swe"] = day_in_hydro_year(group.loc[group['swe'].idxmax(), 'date'])
                season_dict[f"{season}_timing_min_swe"] = day_in_hydro_year(group.loc[group['swe'].idxmin(), 'date'])

            # === Append results ===
            result_rows.append({
                'basin_id': basin_id,
                'hydro_year': year,
                'hydro_year_str': hydro_year_str,
                'max_swe': peak_value,
                'date_of_max_swe': peak_date,
                'timing_of_max_swe': day_in_hydro_year(peak_date),
                'min_swe': min_row['swe'],
                'date_of_min_swe': min_row['date'],
                'timing_of_min_swe': day_in_hydro_year(min_row['date']),
                'melt_duration_to_swe50': duration_to_swe50,
                'date_swe50': swe50_date,
                'timing_swe50': day_in_hydro_year(pd.to_datetime(swe50_date)) if swe50_date else None,
                'melt_duration_to_swe10': duration_to_swe10,
                'date_swe10': swe10_date,
                'timing_swe10': day_in_hydro_year(pd.to_datetime(swe10_date)) if swe10_date else None,
                'accumulation_start_date': acc_start_date,
                'timing_accumulation_start': day_in_hydro_year(acc_start_date) if acc_start_date else None,
                'accumulation_duration': duration_accumulation,
                'snowfall_days_accumulation': snowfall_days_accum,
                'snowfall_percent_accumulation': perc_snowfall_accum,
                'constant_snowfall_start_date': constant_snowfall_date,
                'timing_constant_snowfall_start': day_in_hydro_year(constant_snowfall_date) if constant_snowfall_date else None,
                'summer_snowfall_accumulation': summer_snowfall_acc,
                'number_of_days_summer_snowfall': summer_snowfall_count,
                **season_dict
            })

        result_df = pd.DataFrame(result_rows)
        if not result_df.empty:
            all_results.append(result_df)
        result_df.to_csv(os.path.join(output_folder, f"{basin_id}.csv"),
                         index=False, date_format='%Y-%m-%d')
        print(f"{basin_id}: SWE parameters saved ({len(result_df)} years)")

    if all_results:
        big_df = pd.concat(all_results, ignore_index=True)
        big_df.to_csv(os.path.join(output_folder, "swe_params_all_basins.csv"),
                      index=False, date_format='%Y-%m-%d')
        print(f"Combined results saved ({len(big_df)} rows)")


def main():
    start_year = 1980
    end_year = 2024
    var_name = "swe" 

 
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

    output_timeseries_folder = "output/swe/swe_basins_timeseries"
    swe_params_folder = "output/swe/swe_parameter_per_hydro_year"

    path_fao = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\FAO_Basins\swe_era_series_all_additive_no_pad.pkl"
    path_subbasins = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\subbasins\swe_era_series_all_additive_no_pad.pkl"

    process_basins(start_year, end_year, basins, var_name, output_timeseries_folder,
                   path_fao, path_subbasins)

    calculate_swe_parameters(output_timeseries_folder, swe_params_folder)


if __name__ == "__main__":
    main()