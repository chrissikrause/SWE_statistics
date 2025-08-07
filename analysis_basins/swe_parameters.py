# This script ..

# Max/Min SWE per hydrological year with corresponding date

# === Imports ===
import pandas as pd
import os
import glob

# === Paths ===
input_folder = "swe_basins_timeseries"
output_folder = "swe_parameter_per_hydro_year"
os.makedirs(output_folder, exist_ok=True)

# === Loop through all CSVs ===
csv_files = glob.glob(os.path.join(input_folder, "swe_*.csv"))

for file_path in csv_files:
    basin_id = os.path.basename(file_path).split("_")[1].split(".")[0]

    df = pd.read_csv(file_path, parse_dates=['date'])

    if df.empty or 'hydro_year' not in df.columns:
        print(f"{basin_id}: Empty file or missing column")
        continue

    result_rows = []
    for year, group in df.groupby('hydro_year'):
        group = group.sort_values('date')  # sicherstellen, dass Zeitreihen korrekt sortiert
        hydro_year_str = group['hydro_year_str'].iloc[0]

        # === Min/Max SWE ===
        max_idx = group['swe'].idxmax()
        max_row = group.loc[max_idx]
        min_idx = group['swe'].idxmin()
        min_row = group.loc[min_idx]

        # === Summer snowfall (June-August) ===
        summer = group[group['date'].dt.month.isin([6, 7, 8])].copy()
        summer['swe_diff'] = summer['swe'].diff()

        # Only positive changes (snowfall)
        summer_snowfall = summer[summer['swe_diff'] > 0]

        # Accumulated snowfall in summer
        summer_snowfall_acc = summer_snowfall['swe_diff'].sum()

        # Timing: Dates/Periods where snowfall occured during summer
        summer_snowfall_dates = summer_snowfall['date'].dt.strftime('%Y-%m-%d').tolist()

        #hydro_year_str = group['hydro_year_str']


        # === Meltoff ===
        peak_date = max_row['date']
        peak_value = max_row['swe']

        after_peak = group[group['date'] > peak_date]

        swe50_row = after_peak[after_peak['swe'] <= peak_value * 0.5].head(1)
        swe10_row = after_peak[after_peak['swe'] <= peak_value * 0.1].head(1)

        # Date of swe50/swe10 else None
        swe50_date = swe50_row['date'].values[0] if not swe50_row.empty else None
        swe10_date = swe10_row['date'].values[0] if not swe10_row.empty else None

        # Duration in days if swe50 or swe10 are present
        duration_to_swe50 = (pd.to_datetime(swe50_date) - pd.to_datetime(peak_date)).days if swe50_date else None
        duration_to_swe10 = (pd.to_datetime(swe10_date) - pd.to_datetime(peak_date)).days if swe10_date else None


        # === Accumulation ===
        group = group.reset_index(drop=True)
        # Calculate difference from one timestep (row) to the previous timestep (row) 
        group['swe_diff'] = group['swe'].diff()

        # Set accumulation start date if SWE remains the same or increases for 3 consecutive timesteps (rows)
        acc_start_date = None
        for i in range(2, len(group)):
            if all(group.loc[j, 'swe_diff'] >= 0 for j in range(i-2, i+1)):
                acc_start_date = group.loc[i-2, 'date']
                break

        # Duration = Peak SWE - Accumulation Start
        duration_accumulation = (pd.to_datetime(peak_date) - pd.to_datetime(acc_start_date)).days if acc_start_date else None


        result_rows.append({
            'hydro_year': year,
            'hydro_year_str': hydro_year_str,
            'max_swe': peak_value,
            'date_of_max_swe': peak_date,
            'min_swe': min_row['swe'],
            'date_of_min_swe': min_row['date'],
            'duration_to_swe50_days': duration_to_swe50,
            'date_swe50': swe50_date,
            'duration_to_swe10_days': duration_to_swe10,
            'date_swe10': swe10_date,
            'accumulation_start_date': acc_start_date,
            'accumulation_duration_days': duration_accumulation,
            'summer_snowfall_accumulation': summer_snowfall_acc,
            'summer_snowfall_dates': ';'.join(summer_snowfall_dates) if summer_snowfall_dates else None
        })

    result_df = pd.DataFrame(result_rows)
    output_path = os.path.join(output_folder, f"{basin_id}.csv")
    result_df.to_csv(output_path, index=False, date_format='%Y-%m-%d')

    print(f"{basin_id}: SWE parameters saved as csv ({len(result_df)} years)")
