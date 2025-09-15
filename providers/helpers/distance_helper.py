import math
from typing import List, Optional, Tuple, Dict
import time

from domain.bus import BusStop
from domain.metro import MetroStation
from domain.tram import TramStation
from domain.rodalies import RodaliesStation
from domain.bicing import BicingStation
from domain.fgc import FgcStation

from helpers import logger

class DistanceHelper:
    """
    Helper class to calculate geographical distances and find nearby locations.
    Uses the Haversine formula for accurate distance calculations.
    """

    EARTH_RADIUS_KM = 6371.0  # Average Earth radius in kilometers

    @staticmethod
    def build_stops_list(
        metro_stations: List[MetroStation],
        bus_stops: List[BusStop],
        tram_stops: List[TramStation],
        rodalies_stations: List[RodaliesStation],
        bicing_stations: List[BicingStation],
        fgc_stations: List[FgcStation],
        user_location: Optional[object] = None,
        results_to_return: int = 50
    ) -> List[Dict]:
        start = time.perf_counter()  # START LOG TIMER

        stops = []
        if user_location is not None and results_to_return == 50:
            results_to_return = 10

        # --- Metro ---
        for m in metro_stations:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    m.latitude, m.longitude,
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "metro",
                "line_name": m.line_name_with_emoji,
                "line_code": m.line_code,        
                "station_name": m.name,
                "station_code": m.code,
                "coordinates": (m.latitude, m.longitude),
                "distance_km": distance_km
            })

        # --- Tram ---
        for t in tram_stops:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    t.latitude, t.longitude,
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "tram",
                "line_name": t.line_name_with_emoji,
                "line_code": t.line_id,
                "station_name": t.name,
                "station_code": t.id,
                "coordinates": (t.latitude, t.longitude),
                "distance_km": distance_km
            })
            
        # --- Rodalies ---
        for t in rodalies_stations:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    t.latitude, t.longitude,
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "rodalies",
                "line_name": t.line_name_with_emoji,
                "line_code": t.line_id,
                "station_name": t.name,
                "station_code": t.id,
                "coordinates": (t.latitude, t.longitude),
                "distance_km": distance_km
            }) 
            
        # --- Bicing ---
        for b in bicing_stations:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    b.latitude, b.longitude,
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "bicing",
                "line_name": '',
                "line_code": '',
                "station_name": b.streetName,
                "station_code": b.id,
                "coordinates": (b.latitude, b.longitude),
                "slots": b.slots,
                "mechanical": b.mechanical_bikes,
                "electrical": b.electrical_bikes,
                "availability": b.disponibilidad,
                "distance_km": distance_km
            })

        # --- FGC ---
        for t in fgc_stations:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    t.latitude, t.longitude,
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "fgc",
                "line_name": t.line_name_with_emoji,
                "line_code": t.line_id,
                "station_name": t.name,
                "station_code": t.id,
                "coordinates": (t.latitude, t.longitude),
                "distance_km": distance_km
            }) 

        # --- Bus ---
        for b in bus_stops:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    b.latitude, b.longitude,
                    user_location.latitude, user_location.longitude
                )
            new_stop = {
                "type": "bus",
                "line_code": b.line_code,
                "station_name": b.name,
                "station_code": b.code,
                "coordinates": (b.latitude, b.longitude),
                "distance_km": distance_km
            }
            if not any(stop.get("station_code") == new_stop["station_code"] and stop.get("type") == new_stop["type"] for stop in stops):
                stops.append(new_stop)

        stops.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"]))
        result = stops[:results_to_return]

        elapsed = time.perf_counter() - start
        logger.info(f"[DistanceHelper] build_stops_list executed in {elapsed:.4f} s")

        return result

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return DistanceHelper.EARTH_RADIUS_KM * c

    @staticmethod
    def get_closest_locations(
        user_lat: float,
        user_lon: float,
        locations: List[Dict],
        top_n: int = 5
    ) -> List[Tuple[Dict, float]]:
        start = time.perf_counter()
        distances = []

        for location in locations:
            distance = DistanceHelper.haversine_distance(
                user_lat, user_lon,
                location["lat"], location["lon"]
            )
            distances.append((location, distance))

        distances.sort(key=lambda x: x[1])
        result = distances[:top_n]

        elapsed = time.perf_counter() - start
        logger.info(f"[DistanceHelper] get_closest_locations executed in {elapsed:.4f} s")

        return result
