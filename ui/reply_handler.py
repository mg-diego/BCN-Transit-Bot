from telegram import Update
from telegram.ext import (
    ContextTypes
)

from application import MetroService, BusService, TramService, RodaliesService, MessageService

class ReplyHandler:
    def __init__(self, message_service: MessageService, keyboard_factory, metro_service: MetroService, bus_service: BusService, tram_service: TramService, rodalies_service: RodaliesService):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.bus_service = bus_service
        self.tram_service = tram_service
        self.rodalies_service = rodalies_service

    # Función que responderá a cualquier mensaje de texto
    async def reply_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user.first_name  
        message = update.message.text  
        
        if len(message) < 3:
            await update.message.reply_text(
                f"⚠️ Usa por lo menos tres letras para buscar."
            )
        else:
            # Respuesta personalizada
            stations = await self.metro_service.get_stations_by_name(message)
            for station in stations:
                line = await self.metro_service.get_line_by_name(station.PICTO)
                if line is not None:
                    station.ID_LINIA = line.ID_LINIA
                    station.CODI_LINIA = line.CODI_LINIA
            await self.message_service.send_new_message(
                update,
                f"🔍 He encontrado las siguientes estaciones:'",
                self.keyboard_factory.reply_keyboard_stations_menu(stations, line.ID_LINIA)
            )
                