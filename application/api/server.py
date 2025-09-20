from fastapi import FastAPI
from application.api.api import get_metro_router, get_bus_router, get_tram_router, get_rodalies_router, get_bicing_router, get_fgc_router, get_near_router, get_user_router

def create_app(
    metro_service,
    bus_service,
    tram_service,
    rodalies_service,
    bicing_service,
    fgc_service,
    user_data_manager
):
    app = FastAPI(title="BCN Transit API")

    # Monta el router pasando los servicios ya inicializados
    app.include_router(get_metro_router(metro_service), prefix="/api/metro", tags=["Metro"])
    app.include_router(get_bus_router(bus_service), prefix="/api/bus", tags=["Bus"])
    app.include_router(get_tram_router(tram_service), prefix="/api/tram", tags=["Tram"])
    app.include_router(get_fgc_router(fgc_service), prefix="/api/fgc", tags=["FGC"])
    app.include_router(get_rodalies_router(rodalies_service), prefix="/api/rodalies", tags=["Rodalies"])
    app.include_router(get_bicing_router(bicing_service), prefix="/api/bicing", tags=["Bicing"])

    app.include_router(get_near_router(metro_service, bus_service, tram_service, rodalies_service, bicing_service, fgc_service), prefix="/api", tags=["Near Stations"])

    app.include_router(get_user_router(user_data_manager), prefix="/api/users", tags=["Users"])

    return app