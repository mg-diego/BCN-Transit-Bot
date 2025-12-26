
import math
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Body
from pydantic import BaseModel

from application.services.transport.bicing_service import BicingService
from application.services.transport.bus_service import BusService
from application.services.transport.fgc_service import FgcService
from application.services.transport.metro_service import MetroService
from application.services.transport.rodalies_service import RodaliesService
from application.services.transport.tram_service import TramService
from domain.api.favorite_model import FavoriteItem
from domain.clients import ClientType
from domain.common.location import Location
from providers.helpers.distance_helper import DistanceHelper
from providers.helpers.utils import Utils
from providers.manager.user_data_manager import UserDataManager



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
    
    @router.get("/stations/{station_code}")
    async def get_metro_station(station_code: str):
        return await metro_service.get_station_by_code(station_code)
    
    @router.get("/stations/{station_code}/connections")
    async def get_metro_station_connections(station_code: str):
        return await metro_service.get_station_connections(station_code)
    
    @router.get("/stations/{station_code}/accesses")
    async def get_metro_station_accesses(station_code: str):
        station = await metro_service.get_station_by_code(station_code)
        if station:
            return await metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)
        else:
            return []

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
    
    @router.get("/stops/{stop_code}/connections")
    async def get_bus_stop_connections(stop_code: str):
        return await bus_service.get_stop_connections(stop_code)
    
    @router.get("/stops/{stop_code}")
    async def get_bus_stop(stop_code: str):
        return await bus_service.get_stop_by_code(stop_code)
    
    @router.get("/stops/{stop_code}/accesses")
    async def get_bus_stop_accesses(stop_code: str):
        return []

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
    
    @router.get("/stops/{stop_code}")
    async def get_tram_stop(stop_code: str):
        return await tram_service.get_stop_by_code(stop_code)
    
    @router.get("/stops/{stop_code}/connections")
    async def get_tram_stop_connections(stop_code: str):
        return await tram_service.get_tram_stop_connections(stop_code)
    
    @router.get("/stops/{stop_code}/accesses")
    async def get_tram_stop_accesses(stop_code: str):
        return []

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
    
    @router.get("/stations/{station_code}")
    async def get_rodalies_station(station_code: str):
        return await rodalies_service.get_station_by_code(station_code)
    
    @router.get("/stations/{station_code}/connections")
    async def get_rodalies_station_connections(station_code: str):
        return await rodalies_service.get_rodalies_station_connections(station_code)

    @router.get("/stations/{station_code}/accesses")
    async def get_rodalies_station_accesses(station_code: str):
        return []

    return router

def get_bicing_router(
    bicing_service: BicingService
) -> APIRouter:
    router = APIRouter()

    @router.get("/stations")
    async def list_bicing_stations():
        return await bicing_service.get_all_stations()
    
    @router.get("/stations/{station_id}")
    async def get_bicing_station(station_id: str):
        return await bicing_service.get_station_by_id(station_id)

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
    
    @router.get("/stations/{station_code}")
    async def get_fgc_station(station_code: str):
        return await fgc_service.get_station_by_code(station_code)
    
    @router.get("/stations/{station_code}/connections")
    async def get_fgc_station_connections(station_code: str):
        return await fgc_service.get_fgc_station_connections(station_code)

    @router.get("/stations/{station_code}/accesses")
    async def get_fgc_station_accesses(station_code: str):
        return []

    return router

import asyncio
from fastapi import APIRouter

def get_results_router(
    metro_service: MetroService,
    bus_service: BusService,
    tram_service: TramService,
    rodalies_service: RodaliesService,
    bicing_service: BicingService,
    fgc_service: FgcService,
    user_data_manager: UserDataManager
) -> APIRouter:
    router = APIRouter()

    @router.get("/near")
    async def list_near_stations(lat: float, lon: float, radius: float = 0.5):
        metro_task = metro_service.get_stations_by_name('')
        bus_task = bus_service.get_stops_by_name('')
        tram_task = tram_service.get_stops_by_name('')
        fgc_task = fgc_service.get_stations_by_name('')
        rodalies_task = rodalies_service.get_stations_by_name('')
        bicing_task = bicing_service.get_stations_by_name('')

        metro, bus, tram, fgc, rodalies, bicing = await asyncio.gather(
            metro_task, bus_task, tram_task, fgc_task, rodalies_task, bicing_task
        )

        near_results = DistanceHelper.build_stops_list(
            metro_stations=metro,
            bus_stops=bus,
            tram_stops=tram,
            rodalies_stations=rodalies,
            bicing_stations=bicing,
            fgc_stations=fgc,
            user_location=Location(latitude=lat, longitude=lon),
            results_to_return=999999,
            max_distance_km=radius
        )
        return near_results

    @router.get("/search")
    async def search_stations(name: str, user_id: str = None):
        # 1. Registrar auditoría (Fire and Forget)
        # Aunque search espera (type, line, code), aquí es una búsqueda genérica de texto.
        # Puedes adaptar register_search o crear uno nuevo log_generic_search
        if user_id:
             # Lanzamos la tarea sin await para no frenar la búsqueda
             asyncio.create_task(
                 user_data_manager.register_search(
                     type="GLOBAL", 
                     line="", 
                     code="", 
                     name=name, 
                     user_id_ext=user_id
                 )
             )

        tasks = [
            metro_service.get_stations_by_name(name),
            bus_service.get_stops_by_name(name),
            tram_service.get_stops_by_name(name),
            fgc_service.get_stations_by_name(name),
            rodalies_service.get_stations_by_name(name),
            bicing_service.get_stations_by_name(name),
        ]
        metro, bus, tram, fgc, rodalies, bicing = await asyncio.gather(*tasks)

        search_results = DistanceHelper.build_stops_list(
            metro_stations=metro,
            bus_stops=bus,
            tram_stops=tram,
            rodalies_stations=rodalies,
            bicing_stations=bicing,
            fgc_stations=fgc
        )
        return search_results

    return router


def get_user_router(
    user_data_manager: UserDataManager
) -> APIRouter:
    router = APIRouter()

    @router.post("/{user_id}/register", status_code=status.HTTP_201_CREATED)
    async def register_user(user_id: str, request: RegisterRequest = Body(...)):
        try:
            result = await user_data_manager.register_user(
                client_source=ClientType.ANDROID.value,
                user_id=user_id,
                username='android_user',
                fcm_token=request.fcmToken
            )
            return result
        except Exception as e:
            # MEJORA: HTTPException en lugar de devolver dict
            raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")
        
    @router.post("/{user_id}/notifications/toggle/{status}")
    async def toggle_user_notifications(user_id: str, status: bool):
        try:
            result = await user_data_manager.update_user_receive_notifications(
                ClientType.ANDROID.value,
                user_id,
                status
            )
            if not result:
                raise HTTPException(status_code=404, detail="User not found")
            return result
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.get("/{user_id}/notifications/configuration")
    async def get_user_notifications_configuration(user_id: str) -> bool:
        try:
            return await user_data_manager.get_user_receive_notifications(ClientType.ANDROID.value, user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.get("/{user_id}/favorites", response_model=List[FavoriteItem])
    async def get_favorites(user_id: str):
        try:
            return await user_data_manager.get_favorites_by_user(ClientType.ANDROID.value, user_id)
        except Exception as e:
            # El frontend espera una lista, si devolvemos un dict con "error" la app crasheará al parsear
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.get("/{user_id}/favorites/exists")
    async def has_favorite(
        user_id: str,
        type: str = Query(..., description="Tipo de favorito, ej: metro, bus"),
        item_id: str = Query(..., description="Código del item a buscar")
    ) -> bool:
        try:
            return await user_data_manager.has_favorite(user_id, type=type, item_id=item_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.post("/{user_id}/favorites", status_code=status.HTTP_201_CREATED)
    async def add_favorite(user_id: str, body: FavoriteItem = Body(...)) -> bool:
        try:
            return await user_data_manager.add_favorite(ClientType.ANDROID.value, user_id, type=body.TYPE, item=body)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @router.delete("/{user_id}/favorites")
    async def delete_favorite(
        user_id: str,
        type: str = Query(..., description="Tipo de favorito, ej: metro, bus"),
        item_id: str = Query(..., description="Código del item a eliminar")
    ) -> bool:
        try:
            return await user_data_manager.remove_favorite(ClientType.ANDROID.value, user_id, type=type, item_id=item_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    return router


class RegisterRequest(BaseModel):
    fcmToken: str