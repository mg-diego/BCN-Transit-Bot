import math
from fastapi import APIRouter

from application.services.transport.bicing_service import BicingService
from application.services.transport.bus_service import BusService
from application.services.transport.fgc_service import FgcService
from application.services.transport.metro_service import MetroService
from application.services.transport.rodalies_service import RodaliesService
from application.services.transport.tram_service import TramService
from domain.common.location import Location
from providers.helpers.distance_helper import DistanceHelper
from providers.helpers.utils import Utils

def clean_floats(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_floats(v) for v in obj]
    return obj

def get_metro_router(
    metro_service: MetroService
) -> APIRouter:
    router = APIRouter()

    @router.get("/lines")
    async def list_metro_lines():
        return sorted(await metro_service.get_all_lines(), key=Utils.sort_lines)
    
    @router.get("/stations")
    async def list_metro_stations():
        return await metro_service.get_all_stations()
    
    @router.get("/lines/{line_id}/stations")
    async def list_metro_stations_by_line(line_id: str):
        return await metro_service.get_stations_by_line(line_id)
    
    @router.get("/stations/{station_code}/routes")
    async def list_metro_station_routes(station_code: str):
        return await metro_service.get_station_routes(station_code)

    return router

def get_bus_router(
    bus_service: BusService
) -> APIRouter:
    router = APIRouter()

    @router.get("/lines")
    async def list_bus_lines():
        return await bus_service.get_all_lines()
    
    @router.get("/stops")
    async def list_bus_stops():
        return await bus_service.get_all_stops()
    
    @router.get("/lines/{line_id}/stops")
    async def list_tram_stations_by_line(line_id: str):
        return await bus_service.get_stops_by_line(line_id)
    
    @router.get("/stops/{stop_code}/routes")
    async def list_bus_stop_routes(stop_code: str):
        return await bus_service.get_stop_routes(stop_code)

    return router

def get_tram_router(
    tram_service: TramService
) -> APIRouter:
    router = APIRouter()

    @router.get("/lines")
    async def list_tram_lines():
        return sorted(await tram_service.get_all_lines(), key=Utils.sort_lines)
    
    @router.get("/stops")
    async def list_tram_stops():
        return await tram_service.get_all_stops()
    
    @router.get("/lines/{line_id}/stops")
    async def list_tram_stops_by_line(line_id: str):
        return await tram_service.get_stops_by_line(line_id)
    
    @router.get("/stops/{stop_code}/routes")
    async def list_tram_stop_routes(stop_code: str):
        return await tram_service.get_stop_routes(stop_code)

    return router

def get_rodalies_router(
    rodalies_service: RodaliesService
) -> APIRouter:
    router = APIRouter()

    @router.get("/lines")
    async def list_rodalies_lines():
        return sorted(await rodalies_service.get_all_lines(), key=Utils.sort_lines)
    
    @router.get("/stations")
    async def list_rodalies_stops():
        return await rodalies_service.get_all_stations()
    
    @router.get("/lines/{line_id}/stations")
    async def list_rodalies_stations_by_line(line_id: str):
        return await rodalies_service.get_stations_by_line(line_id)
    
    @router.get("/stations/{station_code}/routes")
    async def list_rodalies_station_routes(station_code: str):
        return await rodalies_service.get_station_routes(station_code)

    return router

def get_bicing_router(
    bicing_service: BicingService
) -> APIRouter:
    router = APIRouter()

    @router.get("/stations")
    async def list_bicing_stations():
        return await bicing_service.get_all_stations()

    return router

def get_fgc_router(
    fgc_service: FgcService
) -> APIRouter:
    router = APIRouter()

    @router.get("/lines")
    async def list_fgc_lines():
        return sorted(await fgc_service.get_all_lines(), key=Utils.sort_lines)
    
    @router.get("/stations")
    async def list_fgc_stations():
        data = await fgc_service.get_all_stations()
        return clean_floats(data)
    
    @router.get("/lines/{line_id}/stations")
    async def list_fgc_stations_by_line(line_id: str):
        return await fgc_service.get_stations_by_line(line_id)
    
    @router.get("/stations/{station_code}/routes")
    async def list_fgc_station_routes(station_code: str):
        return await fgc_service.get_station_routes(station_code)

    return router

def get_near_router(
    metro_service: MetroService,
    bus_service: BusService,
    tram_service: TramService,
    rodalies_service: RodaliesService,
    bicing_service: BicingService,
    fgc_service: FgcService
) -> APIRouter:
    router = APIRouter()

    @router.get("/near")
    async def list_near_stations(lat: float, lon: float, radius: float = 0.5):
        results = {
            "metro": await metro_service.get_stations_by_name(''),
            "bus": await bus_service.get_stops_by_name(''),
            "tram": await tram_service.get_stops_by_name(''),
            "fgc": await fgc_service.get_stations_by_name(''),
            "rodalies": await rodalies_service.get_stations_by_name(''),
            "bicing": await bicing_service.get_stations_by_name('')
        }
        near_results = DistanceHelper.build_stops_list(
            metro_stations=results.get('metro'),
            bus_stops=results.get('bus'),
            tram_stops=results.get('tram'),
            rodalies_stations=results.get('rodalies'),
            bicing_stations=results.get('bicing'),
            fgc_stations=results.get('fgc'),
            user_location=Location(latitude=lat, longitude=lon),
            results_to_return=999999,
            max_distance_km=radius
        )
        return near_results

    return router
