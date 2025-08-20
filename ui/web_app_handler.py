import json
from telegram import Update
from telegram.ext import ContextTypes

from ui import MetroHandler, BusHandler, TramHandler

class WebAppHandler:

    def __init__(self, metro_handler: MetroHandler, bus_handler: BusHandler, tram_handler: TramHandler):
        self.metro_handler = metro_handler
        self.bus_handler = bus_handler
        self.tram_handler = tram_handler

    def web_app_data_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        data = update.message.web_app_data.data

        try:
            payload = json.loads(data)
        except Exception as e:
            print(f"Error al parsear los datos de la WebApp: {e}")
            return

        print(payload)
        data_type = payload.get("type")

        if data_type == "bus":
            return self.bus_handler.show_stop(update, context)
        elif data_type == "metro":
            return self.metro_handler.show_station(update, context)
        elif data_type == "tram":
            pass
        else:
            update.message.reply_text("Tipo de dato no reconocido.")