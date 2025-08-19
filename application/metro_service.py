from typing import List
from domain.metro_line import MetroLine
from domain.metro_station import MetroStation
from domain.metro_access import MetroAccess
from domain.metro_connection import MetroConnection

class MetroService:
    def __init__(self, transport_api_service, language_manager, cache_service=None):
        """
        transport_api_service: servicio de infraestructura para consultar la API de transporte
        cache_service: servicio opcional para cachear respuestas
        """
        self.transport_api_service = transport_api_service
        self.language_manager = language_manager
        self.cache_service = cache_service

    async def get_all_lines(self) -> List[MetroLine]:
        """
        Devuelve todas las líneas de metro disponibles.
        Si hay cache_service, primero intenta recuperar de cache.
        """
        cache_key = "metro_lines"
        if self.cache_service:
            lines = await self.cache_service.get(cache_key)
            if lines:
                print(f"get cache: lines")
                return lines

        lines = await self.transport_api_service.get_metro_lines()

        if self.cache_service:            
            print(f"set cache: lines")
            await self.cache_service.set(cache_key, lines, ttl=3600)  # Cache por 1 hora

        return lines
    
    async def get_line_by_id(self, line_id) -> MetroLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        return line

    async def get_stations_by_line(self, line_id) -> List[MetroStation]:
        """
        Devuelve las estaciones de una línea de metro específica.
        """
        cache_key = f"metro_line_{line_id}_stations"
        if self.cache_service:
            stations = await self.cache_service.get(cache_key)
            if stations:                
                print(f"get cache: stations")
                return stations

        stations = await self.transport_api_service.get_stations_by_metro_line(line_id)

        if self.cache_service:
            print(f"set cache: stations")
            await self.cache_service.set(cache_key, stations, ttl=3600)

        return stations
    
    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        """
        Devuelve las entradas de una estación de metro
        """
        cache_key = f"metro_station_{group_code_id}_accesses"
        if self.cache_service:
            accesses = await self.cache_service.get(cache_key)
            if accesses:                
                print(f"get cache: accesses")
                return accesses

        accesses = await self.transport_api_service.get_metro_station_accesses(group_code_id)

        if self.cache_service:
            print(f"set cache: accesses")
            await self.cache_service.set(cache_key, accesses, ttl=3600)

        return accesses

    async def get_station_by_id(self, station_id, line_id) -> MetroStation:
        """
        Devuelve una estación en base a su CODI_ESTACIó
        """
        stations = await self.get_stations_by_line(line_id)
        station = next((s for s in stations if str(s.CODI_ESTACIO) == str(station_id)), None)
        return station

    async def get_metro_station_connections(self, station_id) -> List[MetroConnection]:
        """
        Devuelve la lista de conexiones de una estación de metro.
        """
        cache_key = f"metro_station_connections_{station_id}"
        if self.cache_service:
            connections = await self.cache_service.get(cache_key)
            if connections:                
                print(f"get cache: _connections")
            else:                
                print(f"set cache: _connections")
                connections = await self.transport_api_service.get_metro_station_connections(station_id)
                await self.cache_service.set(cache_key, connections, ttl=3600)
        else:
            connections = await self.transport_api_service.get_metro_station_connections(station_id)

        formatted_connections = (
            "\n".join(str(c) for c in connections)
            or self.language_manager.t('metro.station.no.connections')
        )

        return formatted_connections
    
    async def get_metro_station_alerts(self, metro_line_id, station_id):
        """
        Devuelve la lista de alertas de una estación de metro.
        """
        cache_key = f"metro_station_alerts_{station_id}"
        if self.cache_service:
            alerts = await self.cache_service.get(cache_key)
            if alerts:                
                print(f"get cache: alerts")
            else:                
                print(f"set cache: alerts")
                line = next((l for l in await self.get_all_lines() if str(l.CODI_LINIA) == str(metro_line_id)), None)
                alerts = await self.transport_api_service.get_metro_station_alerts(line.ORIGINAL_NOM_LINIA, station_id)
                await self.cache_service.set(cache_key, alerts, ttl=3600)
        else:            
            line = next((l for l in await self.get_all_lines() if str(l.CODI_LINIA) == str(metro_line_id)), None)
            alerts = await self.transport_api_service.get_metro_station_alerts(line.ORIGINAL_NOM_LINIA, station_id)

        formatted_alerts = (
            "\n".join(f"<pre>{c}</pre>" for c in alerts)
            or self.language_manager.t('metro.station.no.alerts')
        )

        return formatted_alerts
    
    async def get_station_routes(self, metro_station_id):
        routes = await self.transport_api_service.get_next_metro_at_station(metro_station_id)
        return "\n\n".join(str(route) for route in routes)