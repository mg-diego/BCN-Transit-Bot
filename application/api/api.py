from fastapi import APIRouter

from application.services.transport.bicing_service import BicingService
from application.services.transport.bus_service import BusService
from application.services.transport.fgc_service import FgcService
from application.services.transport.metro_service import MetroService
from application.services.transport.rodalies_service import RodaliesService
from application.services.transport.tram_service import TramService
from providers.helpers.utils import Utils

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
    
    @router.get("/stations/{line_id}")
    async def list_metro_stations_by_line(line_id: str):
        return await metro_service.get_stations_by_line(line_id)

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
        return await fgc_service.get_all_stations()

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
    async def list_near_stations(lat: float, lon: float, radius: int = 500):
        results = {
            "metro": await metro_service.get_stations_by_name(''),
            "bus": await bus_service.get_stops_by_name(''),
            "tram": await tram_service.get_stops_by_name(''),
            "fgc": await fgc_service.get_stations_by_name(''),
            "rodalies": await rodalies_service.get_stations_by_name(''),
            "bicing": await bicing_service.get_stations_by_name('')
        }
        return results

    return router
