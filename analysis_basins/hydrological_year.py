"""
Hydrological year 
----------------------

This script/function assigns a new column to a time series dataframe
containing the hydrological year (starting in September by default)

Function:
- `assign_hydrological_year`: Converts pandas series to df and adds
   a column 'hydro_year' that defines the hydrological year (starting in September by default)

Author: Christina Krause (University of Wuerzburg/DLR)
Date: 06.08.2025
"""

# === Imports ===
import pandas
import os
import pickle
from extract_time_series import load_time_series, extract_trend_data

def assign_hydrological_year(df, start_month=9):
    """
    Convert pandas series to df.
    Adds columns
    - 'hydro_year': defines the hydrological year (starting in September by default) as int
    - 'hydro_year_str: hydro_year as string (e.g. 1980/81)
    """
    df = df.copy()
    # For months from September hydro Jahr = current year + 1, other: current year
    df['hydro_year'] = df.index.year + (df.index.month >= start_month).astype(int) # everything after + is either 1 (true) or 0 (false)
    # Get start and end year of each hydrological year
    start_year = df['hydro_year'] - 1
    end_year_short = df['hydro_year'].astype(str).str[-2:]  # z.B. '82'

    # String-Spalte: '1981/82'
    df['hydro_year_str'] = start_year.astype(str) + '/' + end_year_short
    return df


# ===========
# Creating SWE dfs with corresponding hydrological year from all basins
# and saving to CSVs
# ===========


# === Parameter ===
start_year = 1980
end_year = 2024
var_name = "swe"

output_folder = "swe_basins_timeseries"

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


# === Create Output Directory ===
os.makedirs(output_folder, exist_ok=True)

# === Load swe time series data for FAO and subbasins ===
time_series_list_fao = load_time_series("swe", "C:\Innolab\Daten_fuer_Christina\Data\Snow\FAO_Basins\swe_era_series_all_additive_no_pad.pkl") 
time_series_list_subbasins = load_time_series("swe", "C:\Innolab\Daten_fuer_Christina\Data\Snow\subbasins\swe_era_series_all_additive_no_pad.pkl") 

basin_ids_fao = set(str(item['basin_id']) for item in time_series_list_fao)
basin_ids_subbasins = set(str(item['basin_id']) for item in time_series_list_subbasins)

# === Process all basins ===
for basin_id in basins:
    source_list = None

    if basin_id in basin_ids_fao:
        source_list = time_series_list_fao
    elif basin_id in basin_ids_subbasins:
        source_list = time_series_list_subbasins
    else:
        print(f"{basin_id}: Nicht in FAO- oder Subbasin-Daten gefunden")
        continue

    trend_series = extract_trend_data(source_list, basin_id, start_year, end_year)

    if trend_series is not None and not trend_series.empty:
        df = assign_hydrological_year(trend_series.to_frame(name=var_name))

        # Index in Spalte 'date' umwandeln
        df.index.name = 'date'
        df.reset_index()

        output_path = os.path.join(output_folder, f"swe_{basin_id}.csv")
        df.to_csv(output_path, index=True, date_format='%Y-%m-%d')
        print(f"{basin_id}: CSV gespeichert ({len(df)} Zeilen)")
    else:
        print(f"{basin_id}: Keine Daten im gewählten Zeitraum")