# This script ..

# Max/Min SWE per hydrological year with corresponding date

# === Imports ===
import pandas as pd
import os
import glob
from hydrological_year import day_in_hydro_year

# === Paths ===

input_folder = "swe_basins_timeseries"
output_folder = "swe_parameter_per_hydro_year"
os.makedirs(output_folder, exist_ok=True)

# === Loop through all CSVs ===
csv_files = glob.glob(os.path.join(input_folder, "swe_*.csv"))

all_results=[]
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

        # Count days with summer snowfall
        summer_snowfall_count = len(summer_snowfall)


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

        # Set accumulation start date for the first date in hydrolog. year where SWE_diff > 0
        acc_start_date = None
        for i in range(1, len(group)):
            if group.loc[i, 'swe_diff'] > 0:
                acc_start_date = group.loc[i, 'date']
                break

        """
        # Set accumulation start date if SWE remains the same or increases for 3 consecutive timesteps (rows)
        acc_start_date = None
        for i in range(2, len(group)):
            if all(group.loc[j, 'swe_diff'] >= 0 for j in range(i-2, i+1)):
                acc_start_date = group.loc[i-2, 'date']
                break
        """

        # Duration = Peak SWE - Accumulation Start
        duration_accumulation = (pd.to_datetime(peak_date) - pd.to_datetime(acc_start_date)).days if acc_start_date else None

        if acc_start_date is not None:
            # Daten innerhalb Akkumulationsperiode: vom acc_start_date bis zum peak_date (inklusive)
            accum_period = group[(group['date'] >= acc_start_date) & (group['date'] <= peak_date)]

            # Anzahl Schneefall-Tage in Akkumulationsperiode (swe_diff > 0)
            snowfall_days_accum = (accum_period['swe_diff'] > 0).sum()

            # Prozentualer Anteil Schneetage an allen Tagen in Akkumulationsperiode
            perc_snowfall_accum = snowfall_days_accum / len(accum_period) if len(accum_period) > 0 else None

            # Suche nach erstem Tag in Akkumulationsperiode mit konstant positiven swe_diff für mindestens 3 Tage
            constant_snowfall_date = None
            for i in range(len(accum_period) - 2):
                window = accum_period['swe_diff'].iloc[i:i+3]
                if (window > 0).all():
                    constant_snowfall_date = accum_period['date'].iloc[i]
                    break
        else:
            snowfall_days_accum = None
            perc_snowfall_accum = None
            constant_snowfall_date = None

        # === Write all metrics to df/file
        result_rows.append({
            'basin_id': basin_id,
            'hydro_year': year,
            'hydro_year_str': hydro_year_str,
            'max_swe': peak_value,
            'date_of_max_swe': peak_date,
            'day_of_max_swe': day_in_hydro_year(peak_date),
            'min_swe': min_row['swe'],
            'date_of_min_swe': min_row['date'],
            'day_of_min_swe': day_in_hydro_year(min_row['date']),
            'duration_to_swe50_days': duration_to_swe50,
            'date_swe50': swe50_date,
            'day_swe50': day_in_hydro_year(pd.to_datetime(swe50_date)) if swe50_date is not None else None,
            'duration_to_swe10_days': duration_to_swe10,
            'date_swe10': swe10_date,
            'day_swe10': day_in_hydro_year(pd.to_datetime(swe10_date)) if swe10_date is not None else None,
            'accumulation_start_date': acc_start_date,
            'day_accumulation_start': day_in_hydro_year(acc_start_date) if acc_start_date is not None else None,
            'accumulation_duration_days': duration_accumulation,
            'snowfall_days_accumulation': snowfall_days_accum,
            'snowfall_percent_accumulation': perc_snowfall_accum,
            'constant_snowfall_start_date': constant_snowfall_date,
            'constant_snowfall_start_day': day_in_hydro_year(constant_snowfall_date) if constant_snowfall_date is not None else None,
            'summer_snowfall_accumulation': summer_snowfall_acc,
            #'summer_snowfall_dates': ';'.join(summer_snowfall_dates) if summer_snowfall_dates else None,
            #'summer_snowfall_days': ';'.join(str(day_in_hydro_year(pd.to_datetime(d))) for d in summer_snowfall['date']) if not summer_snowfall.empty else None,
            'summer_snowfall_count': summer_snowfall_count,
        })

    result_df = pd.DataFrame(result_rows)
    if not result_df.empty:
        all_results.append(result_df)

    output_path = os.path.join(output_folder, f"{basin_id}.csv")
    result_df.to_csv(output_path, index=False, date_format='%Y-%m-%d')

    print(f"{basin_id}: SWE parameters saved as csv ({len(result_df)} years)")

if all_results:
    big_df = pd.concat(all_results, ignore_index=True)
    big_df.to_csv(os.path.join(output_folder, "swe_params_all_basins.csv"), index=False, date_format='%Y-%m-%d')
    print(f"Saved long csv with {len(big_df)} rows")