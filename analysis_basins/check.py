'''
With this script one can check for which basin_ids the timeseries data is available.
Additionally, one can define basin_ids to check whether they are contained in the timeseries data.
'''

import pickle
import numpy as np

path_fao = r"C:\Innolab\Daten_fuer_Christina\Data\Snow\subbasins\rain_series_all_additive_no_pad.pkl"


with open(path_fao, 'rb') as f:
    data = pickle.load(f)

basin_id_to_check = '2060548920'

# Basin-Datensatz suchen
basin_data = next((item for item in data if str(item['basin_id']) == basin_id_to_check), None)

if basin_data is not None:
    print(f"Keys im Basin-Datensatz: {basin_data.keys()}")
    
    # Angenommen, Niederschlag ist unter 'rainfall' gespeichert
    if 'time_series_original_data' in basin_data:
        rainfall = np.array(basin_data['time_series_original_data'])
        print(f"Anzahl Werte: {len(rainfall)}")
        print(f"Min: {rainfall.min()}")
        print(f"Max: {rainfall.max()}")
        print(f"Mittel: {rainfall.mean()}")
        print(f"Standardabweichung: {rainfall.std()}")
    else:
        print("Kein Key 'rainfall' gefunden. Mögliche Keys:", basin_data.keys())
else:
    print(f"Basin {basin_id_to_check} nicht gefunden")


basin_ids = set(str(item['basin_id']) for item in data)

print("Alle Basin IDs in der Datei:")
print(basin_ids)

check_ids = ['4012', '4018', '4021', '4025']
for bid in check_ids:
    print(f"Basin ID {bid} ist {'vorhanden' if bid in basin_ids else 'nicht vorhanden'}")
