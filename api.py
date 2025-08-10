import requests
import re
import logging

from data.metro_line import MetroLine
from data.metro_station import create_metro_station
from data.next_metro import MetroLineRoute, NextMetro
from data.metro_access import create_metro_access
from data.metro_connection import MetroConnection

from data.bus_stop import BusStop, create_bus_stop
from data.bus_line import BusLine
from data.next_bus import BusLineRoute, NextBus


# Configura el logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# https://developer.tmb.cat/api-docs/v1

APP_ID = ''
APP_KEY = ''

# Endpoint base de TMB
BASE_URL_TRANSIT = 'https://api.tmb.cat/v1/transit'
BASE_URL_ITRANSIT = "https://api.tmb.cat/v1/itransit"

def natural_key(line):
    name = line.ORIGINAL_NOM_LINIA.strip().upper()

    # Si es puramente numérica: agrupar todas con prefijo "" y ordenar por número
    if name.isdigit():
        return ("", int(name))

    # Si es alfanumérica tipo H1, X23, etc.
    match = re.match(r'^([A-Z]+)(\d+)$', name)
    if match:
        prefix, number = match.groups()
        return (prefix, int(number))

    # Si no encaja en ninguna, lo ponemos al final
    return (name, float('inf'))

def fetch_transit_items(url: str, model_class, *, filter_fn=None, sort_key=None, factory_fn=None):
    data = api_request(url)
    features = data['features']

    items = []
    for feature in features:
        props = feature['properties']
        if filter_fn is None or filter_fn(props):
            if factory_fn:
                item = factory_fn(feature)
            else:
                item = model_class(**props)
            items.append(item)

    if sort_key:
        items.sort(key=sort_key)
    return items, data


def get_bus_lines():
    url = f'{BASE_URL_TRANSIT}/linies/bus'
    items, _ = fetch_transit_items(url, BusLine, sort_key=natural_key)
    return items

def get_bus_line_stops(line_code):
    url = f'{BASE_URL_TRANSIT}/linies/bus/{line_code}/parades'

    from_origin, _ = fetch_transit_items(
        url,
        BusStop,
        filter_fn=lambda props: props['ID_SENTIT'] == 1,
        sort_key=lambda x: x.ORDRE,
        factory_fn=create_bus_stop
    )

    from_destination, _ = fetch_transit_items(
        url,
        BusStop,
        filter_fn=lambda props: props['ID_SENTIT'] == 2,
        sort_key=lambda x: x.ORDRE,
        factory_fn=create_bus_stop
    )

    return [from_origin, from_destination]


def get_metro_lines():
    url = f'{BASE_URL_TRANSIT}/linies/metro'
    items, _ = fetch_transit_items(url, MetroLine, sort_key=lambda x: x.NOM_LINIA)
    return items

def get_stations_by_metro_line(line):
    url = f'{BASE_URL_TRANSIT}/linies/metro/{line}/estacions'
    data = api_request(url)
    features = data['features']

    stations = []
    for feature in features:
        stations.append(create_metro_station(feature))

    stations.sort(key=lambda x: x.ORDRE_ESTACIO)
    return stations

# WIP
def get_next_scheduled_metro_at_station(station_id):
    url = f'{BASE_URL_ITRANSIT}/metro/estacions?estacions={station_id}&temps_teoric=true'
    data = api_request(url)

    scheduled_routes = []
    for line in data.get("linies", []):
        for station in line.get("estacions", []):
            for route_data in station.get("linies_trajectes", []):
                next_scheduled_metros = [
                   # NextMetro(**metro) for metro in route_data.get("propers_trens", [])
                ]

def get_next_metro_at_station(station_id):
    url = f'{BASE_URL_ITRANSIT}/metro/estacions?estacions={station_id}'
    data = api_request(url)

    routes = []
    for line in data.get("linies", []):
        for station in line.get("estacions", []):
            for route_data in station.get("linies_trajectes", []):
                next_metros = [
                    NextMetro(**metro) for metro in route_data.get("propers_trens", [])
                ]
                route = MetroLineRoute(
                    codi_linia=route_data["codi_linia"],
                    nom_linia=route_data["nom_linia"],
                    color_linia=route_data["color_linia"],
                    codi_trajecte=route_data["codi_trajecte"],
                    desti_trajecte=route_data["desti_trajecte"],
                    propers_trens=next_metros
                )
                routes.append(route)
    return routes

def get_next_bus_at_stop(station_id):
    url = f"{BASE_URL_ITRANSIT}/bus/parades/{station_id}"
    data = api_request(url)

    routes = []
    for stop in data.get("parades", []):
        for route_data in stop.get("linies_trajectes", []):
            next_buses = [
                NextBus(**bus) for bus in route_data.get("propers_busos", [])
            ]
            route = BusLineRoute(
                id_operador=route_data["id_operador"],
                transit_namespace=route_data["transit_namespace"],
                codi_linia=route_data["codi_linia"],
                nom_linia=route_data["nom_linia"],
                codi_trajecte=route_data["codi_trajecte"],
                desti_trajecte=route_data["desti_trajecte"],
                id_sentit=route_data["id_sentit"],
                propers_busos=next_buses
            )
            routes.append(route)
    return routes

def get_metro_station_accesses(group_station_code):
    url = f"https://api.tmb.cat/v1/transit/estacions/{group_station_code}/accessos"
    data = api_request(url)
    features = data['features']

    accesses = []
    for feature in features:
        access = create_metro_access(feature)
        accesses.append(access)

    return accesses

def get_metro_station_connections(metro_station_id):
    url = f"https://api.tmb.cat/v1/transit/linies/metro/estacions/{metro_station_id}/corresp"
    data = api_request(url)
    features = data['features']

    connections = []
    for feature in features:
        props = feature["properties"]
        if props['NOM_OPERADOR'] == "Metro":
            connection = MetroConnection(**props)
            connections.append(connection) 

    return connections

def get_metro_station_alerts(metro_line, metro_station_id):
    url = f"https://api.tmb.cat/v1/alerts/metro/channels/WEB/routes/{metro_line}"
    data = api_request(url)
    alerts = data['data']['alerts']

    station_alerts = []
    for alert in alerts:
        for entity in alert['entities']:
            if entity['station_code'] == str(metro_station_id):
                for publication in alert['publications']:
                    station_alerts.append(publication['textEs'])

    return station_alerts

def api_request(endpoint):
    headers = {
        'Accept': 'application/json'
    }
    params = {
        'app_id': APP_ID,
        'app_key': APP_KEY
    }

    response = requests.get(endpoint, headers=headers, params=params)    

    if response.status_code == 200:
        return response.json()
    else:
        logger.info(f"[{response.status_code}] - API Request: {endpoint}")
        logger.error(response.json())
        logger.error(response.text)
        return {}

