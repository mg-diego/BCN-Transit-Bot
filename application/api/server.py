from fastapi import FastAPI
from application.api.api import get_metro_router, get_bus_router, get_tram_router, get_rodalies_router, get_bicing_router, get_fgc_router, get_near_router

def create_app(
    metro_service,
    bus_service,
    tram_service,
    rodalies_service,
    bicing_service,
    fgc_service
):
    app = FastAPI(title="BCN Transit API")

    # Monta el router pasando los servicios ya inicializados
    app.include_router(get_metro_router(metro_service), prefix="/api/metro")
    app.include_router(get_bus_router(bus_service), prefix="/api/bus")
    app.include_router(get_tram_router(tram_service), prefix="/api/tram")
    app.include_router(get_fgc_router(fgc_service), prefix="/api/fgc")
    app.include_router(get_rodalies_router(rodalies_service), prefix="/api/rodalies")
    app.include_router(get_bicing_router(bicing_service), prefix="/api/bicing")

    app.include_router(get_near_router(metro_service, bus_service, tram_service, rodalies_service, bicing_service, fgc_service), prefix="/api")

    return app