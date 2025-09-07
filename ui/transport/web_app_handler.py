import json
from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes
from providers.helpers.logger import logger

from ui import MetroHandler, BusHandler, TramHandler, RodaliesHandler, BicingHandler, FgcHandler

class WebAppHandler:
    """
    Handler for routing web app data from Telegram updates
    to the appropriate transport handler (Metro, Bus, Tram).
    """

    def __init__(self, metro_handler: MetroHandler, bus_handler: BusHandler, tram_handler: TramHandler, rodalies_handler: RodaliesHandler, bicing_handler: BicingHandler, fgc_handler: FgcHandler):
        self.metro_handler = metro_handler
        self.bus_handler = bus_handler
        self.tram_handler = tram_handler
        self.rodalies_handler = rodalies_handler
        self.bicing_handler = bicing_handler
        self.fgc_handler = fgc_handler
        logger.info(f"[{self.__class__.__name__}] WebAppHandler initialized")

    def web_app_data_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Route the web app data to the corresponding handler based on the payload type.
        """
        try:
            data = update.message.web_app_data.data
            payload = json.loads(data)
            logger.info(f"[{self.__class__.__name__}] Received WebApp payload: {payload}")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Error parsing WebApp data: {e}")
            return

        data_type = payload.get("type")
        logger.info(f"[{self.__class__.__name__}] Routing WebApp data of type: {data_type}")

        if data_type == TransportType.BUS.value:
            logger.info(f"[{self.__class__.__name__}] Routing to BusHandler")
            return self.bus_handler.show_stop(update, context)
        elif data_type == TransportType.METRO.value:
            logger.info(f"[{self.__class__.__name__}] Routing to MetroHandler")
            return self.metro_handler.show_station(update, context)
        elif data_type == TransportType.TRAM.value:
            logger.info(f"[{self.__class__.__name__}] Routing to TramHandler")
            return self.tram_handler.show_stop(update, context)
        elif data_type == TransportType.RODALIES.value:        
            logger.info(f"[{self.__class__.__name__}] Routing to RodaliesHandler")
            return self.rodalies_handler.show_station(update, context)
        elif data_type == TransportType.BICING.value:        
            logger.info(f"[{self.__class__.__name__}] Routing to BicingHandler")
            return self.bicing_handler.show_station(update, context)
        elif data_type == TransportType.FGC.value:        
            logger.info(f"[{self.__class__.__name__}] Routing to FgcHandler")
            return self.fgc_handler.show_station(update, context)
        else:
            logger.warning(f"[{self.__class__.__name__}] Unrecognized WebApp data type: {data_type}")
            return update.message.reply_text("Unrecognized data type.")
