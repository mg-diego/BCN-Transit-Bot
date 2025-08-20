from providers.transport_api_service import TransportApiService
from application.cache_service import CacheService

from domain.bus.bus_stop import BusStop

class BusService:
    def __init__(self, transport_api_service: TransportApiService, cache_service: CacheService = None):
        """
        transport_api_service: servicio de infraestructura para consultar la API de transporte
        cache_service: servicio opcional para cachear respuestas
        """
        self.transport_api_service = transport_api_service
        self.cache_service = cache_service

    async def get_all_lines(self):
        """
        Devuelve todas las líneas de bus disponibles.
        Si hay cache_service, primero intenta recuperar de cache.
        """
        cache_key = "bus_lines"
        if self.cache_service:
            lines = await self.cache_service.get(cache_key)
            if lines:
                print(f"get cache: lines")
                return lines

        lines = await self.transport_api_service.get_bus_lines()

        if self.cache_service:            
            print(f"set cache: lines")
            await self.cache_service.set(cache_key, lines, ttl=3600)  # Cache por 1 hora

        return lines

    async def get_stops_by_line(self, line_id):
        """
        Devuelve las paradas de una línea de bus específica.
        """
        cache_key = f"bus_line_{line_id}_stops"
        if self.cache_service:
            stops = await self.cache_service.get(cache_key)
            if stops:                
                print(f"get cache: stops")
                return stops

        stops = await self.transport_api_service.get_bus_line_stops(line_id)

        if self.cache_service:
            print(f"set cache: stops")
            await self.cache_service.set(cache_key, stops, ttl=3600)

        return stops
    
    async def get_stop_by_id(self, stop_id, line_id) -> BusStop:
        """
        Devuelve una parada en base a su CODI_PARADA
        """
        stops = await self.get_stops_by_line(line_id)
        stop = next((s for s in stops if str(s.CODI_PARADA) == str(stop_id)), None)
        return stop
    
    async def get_stop_routes(self, stop_id):
        routes = await self.transport_api_service.get_next_bus_at_stop(stop_id)
        return "\n\n".join(str(route) for route in routes)