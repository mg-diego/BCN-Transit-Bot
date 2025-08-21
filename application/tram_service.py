from typing import List
from providers.tram_api_service import TramApiService
from application.cache_service import CacheService
from providers.language_manager import LanguageManager

from domain.tram.tram_line import TramLine
from domain.tram.tram_stop import TramStop
from domain.tram.tram_connection import TramConnection
from domain.tram.next_tram import TramLineRoute

class TramService:

    def __init__(self, tram_api_service: TramApiService, language_manager: LanguageManager ,cache_service: CacheService):
        self.tram_api_service = tram_api_service
        self.language_manager = language_manager
        self.cache_service = cache_service

    async def get_all_lines(self) -> List[TramLine]:
        """
        Devuelve todas las líneas de tram disponibles.
        Si hay cache_service, primero intenta recuperar de cache.
        """
        cache_key = "tram_lines"
        if self.cache_service:
            lines = await self.cache_service.get(cache_key)
            if lines:
                print(f"get cache: lines")
                return lines

        lines = await self.tram_api_service.get_lines()

        if self.cache_service:            
            print(f"set cache: lines")
            await self.cache_service.set(cache_key, lines, ttl=3600)  # Cache por 1 hora

        return lines
    
    async def get_line_by_id(self, line_id) -> TramLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.code) == str(line_id)), None)
        return line
    
    async def get_stops_by_line(self, line_id: str) -> List[TramStop]:
        """
        Devuelve las paradas de una línea de tram específica.
        """
        cache_key = f"tram_line_{line_id}_stops"
        if self.cache_service:
            stops = await self.cache_service.get(cache_key)
            if stops:                
                print(f"get cache: stops")
                return stops

        stops = await self.tram_api_service.get_stops_on_line(line_id)

        if self.cache_service:
            print(f"set cache: stops")
            await self.cache_service.set(cache_key, stops, ttl=3600)

        return stops
    
    async def get_stop_by_id(self, stop_id, line_id) -> TramStop:
        stops = await self.get_stops_by_line(line_id)
        stop = next((s for s in stops if str(s.id) == str(stop_id)), None)
        return stop
    
    async def get_tram_stop_connections(self, stop_id) -> List[TramConnection]:
        """
        Devuelve la lista de conexiones de una parada de tram.
        """
        cache_key = f"tram_stop_connections_{stop_id}"
        if self.cache_service:
            connections = await self.cache_service.get(cache_key)
            if connections:                
                print(f"get cache: _connections")
            else:                
                print(f"set cache: _connections")
                connections = await self.tram_api_service.get_connections_at_stop(stop_id)
                await self.cache_service.set(cache_key, connections, ttl=3600)
        else:
            connections = await self.tram_api_service.get_connections_at_stop(stop_id)

        formatted_connections = (
            "\n".join(str(c) for c in connections)
            or self.language_manager.t('tram.stop.no.connections')
        )

        return formatted_connections
    
    async def get_stop_routes(
        self, network_id: int, outbound_id: int, return_id: int
    ) -> str:
        cache_key = f"tram_routes_{outbound_id}_{return_id}"

        if self.cache_service:
            routes = await self.cache_service.get(cache_key)
            if routes:
                print("get cache: routes")
            else:
                print("set cache: routes")
                routes = await self.tram_api_service.get_next_trams_at_stop(outbound_id, return_id)
                await self.cache_service.set(cache_key, routes, ttl=10)
        else:
            routes = await self.tram_api_service.get_next_trams_at_stop(network_id)

        return "\n\n".join(str(route) for route in routes)