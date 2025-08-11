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
import pandas as pd
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

def day_in_hydro_year(date, start_month=9):
    if pd.isna(date):
        return None
    # Startdatum des Hydrologischen Jahres ermitteln
    hydro_year_start = pd.Timestamp(
        year=date.year if date.month >= start_month else date.year - 1,
        month=start_month,
        day=1
    )
    return (date - hydro_year_start).days + 1





