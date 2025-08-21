import pandas as pd
from zipfile import ZipFile

# Ruta al ZIP descargado
gtfs_zip = "google_transit.zip"
#https://www.fgc.cat/google/google_transit.zip

# Leemos los archivos necesarios desde el ZIP
with ZipFile(gtfs_zip, 'r') as z:
    routes = pd.read_csv(z.open("routes.txt"))
    trips = pd.read_csv(z.open("trips.txt"))
    stop_times = pd.read_csv(z.open("stop_times.txt"))
    stops = pd.read_csv(z.open("stops.txt"))

# Unimos trips con routes para saber a qué línea pertenece cada viaje
trips_routes = trips.merge(routes, on="route_id", how="left")

# Unimos stop_times para asociar las paradas a cada viaje
trip_stops = stop_times.merge(trips_routes, on="trip_id", how="left")

# Unimos con stops para obtener nombres y coordenadas
trip_stops = trip_stops.merge(stops, on="stop_id", how="left")

# Ahora agrupamos por línea y ordenamos por la secuencia de parada
stops_by_route = trip_stops.sort_values(["route_id", "stop_sequence"])
stops_by_route = stops_by_route[["route_short_name", "stop_sequence", "stop_name", "stop_lat", "stop_lon"]].drop_duplicates()

# Mostramos un ejemplo: las primeras 30 filas
print(stops_by_route.head(30))

# Si quieres exportar todo el listado:
stops_by_route.to_csv("stops_by_route.csv", index=False)
