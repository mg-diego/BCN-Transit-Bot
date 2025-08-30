import json
import html
import lzstring
import unicodedata

from typing import List, Dict, Any

from domain.bus import BusStop
from domain.metro import MetroStation
from domain.rodalies import RodaliesLine, RodaliesStation
from domain.tram import TramStop
from domain.bicing import BicingStation
from domain.transport_type import TransportType

from .logger import logger


class TransportDataCompressor:
    """
    Mapper is responsible for converting transport stop data (metro, bus, tram)
    into a compressed JSON format that can be easily shared or stored.
    """

    def __init__(self):
        self.lz = lzstring.LZString()

    def _normalize_name(self, name: str) -> str:
        """
        Removes accents and normalizes special characters from station or stop names.

        Args:
            name (str): Original name.

        Returns:
            str: Normalized name without accents.
        """
        normalized = ''.join(
            c for c in unicodedata.normalize('NFKD', name)
            if not unicodedata.combining(c)
        )
        logger.debug(f"[{self.__class__.__name__}] Normalized name '{name}' -> '{normalized}'")
        return normalized

    def _compress_data(self, data: Dict[str, Any]) -> str:
        """
        Serializes the provided data into JSON and compresses it using LZString.

        Args:
            data (dict): Data to compress.

        Returns:
            str: Compressed JSON string.
        """
        json_str = json.dumps(data)
        compressed = self.lz.compressToEncodedURIComponent(json_str)
        logger.debug(f"[{self.__class__.__name__}] Compressed data: \n{compressed}")
        return compressed

    def _log_mapping_start(self, transport_type: str, count: int, line_id: str, line_name: str):
        """
        Logs the start of the mapping process for a given transport type.

        Args:
            transport_type (str): Type of transport ("metro", "bus", "tram").
            count (int): Number of stops or stations.
            line_id (str): ID of the transport line.
            line_name (str): Name of the transport line.
        """
        logger.info(
            f"[{self.__class__.__name__}] Mapping {count} {transport_type} stops for line {line_id} ({line_name})..."
        )

    def _log_mapping_end(self, transport_type: str, line_id: str):
        """
        Logs the successful completion of the mapping process.

        Args:
            transport_type (str): Type of transport ("metro", "bus", "tram").
            line_id (str): ID of the transport line.
        """
        logger.info(
            f"[{self.__class__.__name__}] {transport_type.capitalize()} stops mapped and compressed successfully for line {line_id}."
        )

    def _map_stops_bidirectional(
        self,
        stops: List[Dict[str, Any]],
        direction_forward: str,
        direction_reverse: str
    ) -> List[Dict[str, Any]]:
        """
        Creates a list of stops in both forward and reverse directions.

        Args:
            stops (list): Base stop data without direction.
            direction_forward (str): Destination direction for the forward route.
            direction_reverse (str): Origin direction for the reverse route.

        Returns:
            list: Stops duplicated for both directions.
        """
        forward = [
            {**stop, "direction": direction_forward} for stop in stops
        ]
        reverse = [
            {**stop, "direction": direction_reverse} for stop in reversed(stops)
        ]
        return forward + reverse

    def map_metro_stations(self, stations: List[MetroStation], line_id: str, line_name: str) -> str:
        """
        Maps a list of metro stations into a compressed JSON format.

        Args:
            stations (list): List of MetroStation objects.
            line_id (str): Metro line ID.
            line_name (str): Metro line name.

        Returns:
            str: Compressed JSON string representing mapped metro stations.
        """
        self._log_mapping_start(TransportType.METRO.value, len(stations), line_id, line_name)

        stops_base = [
            {
                "lat": station.coordinates[1],
                "lon": station.coordinates[0],
                "name": f"{station.CODI_ESTACIO} - {self._normalize_name(station.NOM_ESTACIO)}",
                "color": station.COLOR_LINIA,
                "alert": '⚠️' if station.has_alerts else ''
            }
            for station in stations
        ]

        stops = self._map_stops_bidirectional(
            stops_base,
            direction_forward=stations[0].DESTI_SERVEI,
            direction_reverse=stations[0].ORIGEN_SERVEI
        )

        data = {
            "type": TransportType.METRO.value,
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": stops
        }

        compressed = self._compress_data(data)
        self._log_mapping_end(TransportType.METRO.value, line_id)
        return compressed

    def map_bus_stops(self, stops: List[BusStop], line_id: str, line_name: str) -> str:
        """
        Maps a list of bus stops into a compressed JSON format.

        Args:
            stops (list): List of BusStop objects.
            line_id (str): Bus line ID.
            line_name (str): Bus line name.

        Returns:
            str: Compressed JSON string representing mapped bus stops.
        """
        self._log_mapping_start(TransportType.BUS.value, len(stops), line_id, line_name)

        data = {
            "type": TransportType.BUS.value,
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": [
                {
                    "lat": stop.coordinates[1],
                    "lon": stop.coordinates[0],
                    "name": f"{stop.CODI_PARADA} - {self._normalize_name(stop.NOM_PARADA)}",
                    "color": stop.COLOR_REC,
                    "alert": '⚠️' if stop.has_alerts else '',
                    "direction": stop.DESTI_SENTIT
                }
                for stop in stops
            ]
        }

        compressed = self._compress_data(data)
        self._log_mapping_end(TransportType.BUS.value, line_id)
        return compressed

    def map_tram_stops(self, stops: List[TramStop], line_id: str, line_name: str) -> str:
        """
        Maps a list of tram stops into a compressed JSON format.

        Args:
            stops (list): List of TramStop objects.
            line_id (str): Tram line ID.
            line_name (str): Tram line name.

        Returns:
            str: Compressed JSON string representing mapped tram stops.
        """
        self._log_mapping_start(TransportType.TRAM.value, len(stops), line_id, line_name)

        origin = stops[0].name
        destination = stops[-1].name

        stops_base = [
            {
                "lat": stop.latitude,
                "lon": stop.longitude,
                "name": f"{stop.id} - {self._normalize_name(stop.name)}",
                "alert": '',
                "color": "008E78",
            }
            for stop in stops
        ]

        tram_stops = self._map_stops_bidirectional(
            stops_base,
            direction_forward=destination,
            direction_reverse=origin
        )

        data = {
            "type": TransportType.TRAM.value,
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": tram_stops
        }

        compressed = self._compress_data(data)
        self._log_mapping_end(TransportType.TRAM.value, line_id)
        return compressed
    
    def map_rodalies_stations(self, stations: List[RodaliesStation], line: RodaliesLine):
        """
        Maps a list of rodalies stations into a compressed JSON format.

        Args:
            stations (list): List of RodaliesStation objects.
            line_id (str): Rodalies line ID.
            line_name (str): Rodalies line name.

        Returns:
            str: Compressed JSON string representing mapped rodalies stations.
        """
        self._log_mapping_start(TransportType.RODALIES.value, len(stations), line.id, line.name)

        stops_base = [
            {
                "lat": station.latitude,
                "lon": station.longitude,
                "name": f"{station.id} - {self._normalize_name(station.name)}",
                "alert": '',
                "color": line.color,
            }
            for station in stations
        ]

        stops = self._map_stops_bidirectional(
            stops_base,
            direction_forward=line.origin_station_name,
            direction_reverse=line.destination_station_name
        )

        data = {
            "type": TransportType.RODALIES.value,
            "line_id": line.id,
            "line_name": html.escape(line.name),
            "stops": stops
        }

        compressed = self._compress_data(data)
        self._log_mapping_end(TransportType.RODALIES.value, line.id)
        return compressed
    
    def map_bicing_stations(self, stations: List[BicingStation]):
        """
        Maps a list of bus stops into a compressed JSON format.

        Args:
            stops (list): List of BusStop objects.
            line_id (str): Bus line ID.
            line_name (str): Bus line name.

        Returns:
            str: Compressed JSON string representing mapped bus stops.
        """
        self._log_mapping_start(TransportType.BICING.value, len(stations), '', '')

        data = {
            "type": TransportType.BICING.value,
            "stops": [
                {
                    "lat": station.latitude,
                    "lon": station.longitude,
                    "name": f"{station.id} - {self._normalize_name(html.escape(station.streetName))}",
                    "slots": station.slots,
                    "electrical_bikes": station.electrical_bikes,
                    "mechanical_bikes": station.mechanical_bikes,
                    "availability": station.disponibilidad
                }
                for station in stations
            ]
        }

        compressed = self._compress_data(data)
        self._log_mapping_end(TransportType.BICING.value, '')
        return compressed