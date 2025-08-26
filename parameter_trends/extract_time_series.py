"""
Trend Extraction from Time Series Data
--------------------------------------

This script loads time series data from a `.pkl` file and extracts a specified trend
series for a given basin and time period. The data is assumed to be pre-processed 
and stored in a structured format. This tool is useful for trend analyses such as 
climate studies or hydrological assessments.

Functions:
- `load_time_series`: Loads the full time series dataset from a fixed pickle path.
- `extract_trend_data`: Extracts the original (non-detrended) time series for a 
  specific basin and period.
- `assign_hydrological_year`: Converts extracted pandas series to df and assigns 
  hydrological years (starting in September by default)

Authors: Samuel Schilling (DLR/DFD/LAX/POMO)
Date: 04.08.2025

"""

# === Imports ===
import os
import pandas as pd
import pickle


# === Load Time Series Function ===
def load_time_series(folder_name, timeseries_path):
    """
    Loads time series data from a specified folder.

    Parameters
    ----------
    folder_name : str
        The name of the folder containing the time series data.

    Returns
    -------
    dict
        The loaded time series data from the pickle file.
    """

    # Fixed path to the time series pickle file
    timeseries_path = timeseries_path
    
    with open(timeseries_path, 'rb') as f:
        return pickle.load(f)


# === Extract Trend Data Function ===
def extract_trend_data(time_series_list, basin_id, start_year, end_year):
    """
    Extracts a specified array of data for a given basin and time period 
    from the provided time series list.

    Parameters
    ----------
    time_series_list : list
        A list of dictionaries containing time series data.
    basin_id : str
        The ID of the basin for which trend data should be extracted.
    start_year : int
        The starting year for the trend extraction.
    end_year : int
        The ending year for the trend extraction.

    Returns
    -------
    pandas.Series
        A time series of the trend data for the specified basin and period, 
        or None if the basin is not found.
    """

    for item in time_series_list:
        if item['basin_id'] == basin_id:
            trend_series = item['time_series_original_data']  # for trend+residuals: use 'trend_noise'
            
            # Ensure index is a DateTimeIndex
            if not isinstance(trend_series.index, pd.DatetimeIndex):
                trend_series.index = pd.to_datetime(trend_series.index)
                trend_series.index = trend_series.index.normalize()
                trend_series = trend_series.sort_index()
                

            #print(trend_series.index)
            #print(type(trend_series.index))
            # Define date range for hydrological year (starting 01.09./ending 31.08.) and filter series
            start_date = pd.Timestamp(f"{start_year}-09-01")
            end_date = pd.Timestamp(f"{end_year}-08-31")
            # trend_series = trend_series[start_date:end_date] Slicing produces outliers outside the specific date range

            trend_series = trend_series.loc[
                (trend_series.index >= start_date) & 
                (trend_series.index <= end_date)
            ]       
        
            outside = trend_series[(trend_series.index < start_date) | (trend_series.index > end_date)]
            if not outside.empty:
                print("Values outside defined date range!")
            
            return trend_series

    return None






