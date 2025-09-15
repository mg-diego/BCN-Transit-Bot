import aiohttp
import inspect

from domain.bicing.bicing_station import BicingStation
from providers.helpers import logger

class BicingApiService:
    BASE_URL = "https://www.bicing.barcelona"
    # https://barcelona-sp.publicbikesystem.net/customer/ube/gbfs/v1/

    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
        
    async def _post(self, endpoint: str, data: dict = None):
        """Realiza una petición POST a la API de Bicing."""
        url = f"{self.BASE_URL}{endpoint}"
        current_method = inspect.currentframe().f_code.co_name
        self.logger.debug(f"[{current_method}] POST → {url} | Data → {data}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_stations(self):
        """Obtiene la lista de estaciones de Bicing."""
        data = await self._post('/get-stations')
        stations = [BicingStation(**station) for station in data.get('stations', [])]
        return stations