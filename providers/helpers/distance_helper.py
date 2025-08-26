import math
from typing import List, Optional, Tuple, Dict

from domain.bus import BusStop
from domain.metro import MetroStation
from domain.tram import TramStop

class DistanceHelper:
    """
    Helper class to calculate geographical distances and find nearby locations.
    Uses the Haversine formula for accurate distance calculations.
    """

    EARTH_RADIUS_KM = 6371.0  # Average Earth radius in kilometers

    def build_stops_list(
        metro_stations: List[MetroStation],
        bus_stops: List[BusStop],
        tram_stops: List[TramStop],
        user_location: Optional[object] = None
    ) -> List[Dict]:
        """
        Generates a unified list of stops (metro, bus, tram) with distances to user_location.

        Args:
            metro_stations (List): List of MetroStation objects.
            bus_stops (List): List of BusStop objects.
            tram_stops (List): List of TramStop objects.
            user_location (Optional[object]): Object with latitude and longitude attributes.

        Returns:
            List[Dict]: List of dictionaries containing stop info and distance.
        """
        stops = []
        results_to_return = 10 if user_location is not None else 50

        # --- Metro ---
        for m in metro_stations:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    m.coordinates[1], m.coordinates[0],
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "metro",
                "line": m.NOM_LINIA,
                "name": m.NOM_ESTACIO,
                "code_line": m.CODI_LINIA,
                "code_station": m.CODI_ESTACIO,
                "coordinates": m.coordinates,
                "distance_km": distance_km
            })

        # --- Bus ---
        for b in bus_stops:
            distance_km = None
            if user_location:
                distance_km = DistanceHelper.haversine_distance(
                    b.coordinates[1], b.coordinates[0],
                    user_location.latitude, user_location.longitude
                )
            stops.append({
                "type": "bus",
                "line": b.CODI_LINIA,
                "name": b.NOM_PARADA,
                "code_stop": b.CODI_PARADA,
                "coordinates": b.coordinates,
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
                "line": t.lineId,
                "name": t.name,
                "code_stop": t.id,
                "coordinates": (t.latitude, t.longitude),
                "distance_km": distance_km
            })

        stops.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"]))
        return stops[:results_to_return]

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the great-circle distance between two points on Earth.

        Args:
            lat1 (float): Latitude of the first point.
            lon1 (float): Longitude of the first point.
            lat2 (float): Latitude of the second point.
            lon2 (float): Longitude of the second point.

        Returns:
            float: Distance between the two points in kilometers.
        """
        # Convert degrees to radians
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        # Haversine formula
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return DistanceHelper.EARTH_RADIUS_KM * c
    
    @staticmethod
    def format_distance(distance_km: float) -> str:
        """
        Converts a distance in kilometers to a human-readable string.
        If distance < 1 km, shows in meters; otherwise, shows in km with 1 decimal.

        Args:
            distance_km (float): Distance in kilometers.

        Returns:
            str: Formatted distance string.
        """
        if distance_km < 1:
            return f"{int(distance_km * 1000)}m"
        else:
            return f"{distance_km:.1f}km"

    @staticmethod
    def get_closest_locations(
        user_lat: float,
        user_lon: float,
        locations: List[Dict],
        top_n: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Returns the N closest locations to the user's coordinates.

        Args:
            user_lat (float): User's latitude.
            user_lon (float): User's longitude.
            locations (List[Dict]): List of locations, each containing 'lat' and 'lon' keys.
            top_n (int): Number of closest locations to return.

        Returns:
            List[Tuple[Dict, float]]: A sorted list of tuples (location, distance_km).
        """
        distances = []

        # Calculate the distance for each location
        for location in locations:
            distance = DistanceHelper.haversine_distance(
                user_lat, user_lon,
                location["lat"], location["lon"]
            )
            distances.append((location, distance))

        # Sort locations by distance in ascending order
        distances.sort(key=lambda x: x[1])

        return distances[:top_n]
