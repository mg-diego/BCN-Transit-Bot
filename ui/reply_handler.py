import re
import copy
from telegram import Update
from telegram.ext import (
    ContextTypes
)

from application import MetroService, BusService, TramService, RodaliesService, MessageService
from ui import KeyboardFactory
from providers.manager import LanguageManager 

class ReplyHandler:
    def __init__(self, message_service: MessageService, keyboard_factory: KeyboardFactory, language_manager: LanguageManager, metro_service: MetroService, bus_service: BusService, tram_service: TramService, rodalies_service: RodaliesService):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory
        self.language_manager = language_manager
        self.metro_service = metro_service
        self.bus_service = bus_service
        self.tram_service = tram_service
        self.rodalies_service = rodalies_service


    async def reply_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_text = str(update.message.text)
        self.message_service.set_bot_instance(context.bot)

        if len(search_text) < 3:
            await update.message.reply_text(
                "⚠️ Usa por lo menos tres letras para buscar."
            )
            return
        
        message = await self.message_service.send_new_message(update, self.language_manager.t('common.loading', type="metro"))
        chat_id = self.message_service.get_chat_id(update)

        if search_text.isdigit(): # BUS STATIONS
            
            pass

        else: # METRO STATIONS
            stations = await self.metro_service.get_stations_by_name(search_text)

            unique_stations = {}
            line_cache = {}

            for station in stations:
                lines = re.findall(r"L\d+[A-Z]?(?=L|$)", station.PICTO)

                for line_code in lines:
                    if line_code not in line_cache:
                        line_cache[line_code] = await self.metro_service.get_line_by_name(line_code)
                    line = line_cache[line_code]
                    if line is None:
                        continue

                    line_stations = await self.metro_service.get_stations_by_line(line.CODI_LINIA)
                    line_station = next(
                        (s for s in line_stations if str(s.NOM_ESTACIO) == str(station.NOM_ESTACIO)),
                        None
                    )

                    station_copy = copy.deepcopy(station)
                    station_copy.ID_LINIA = line.ID_LINIA
                    station_copy.CODI_LINIA = line.CODI_LINIA
                    station_copy.NOM_LINIA = line.NOM_LINIA
                    station_copy.CODI_ESTACIO = line_station.CODI_ESTACIO if line_station else None

                    key = (station_copy.NOM_ESTACIO, station_copy.CODI_LINIA)
                    unique_stations[key] = station_copy

            final_stations = list(unique_stations.values())

            await self.message_service.edit_message_by_id(
                chat_id,
                message.message_id,
                self.language_manager.t("results_found", count=len(final_stations)),
                self.keyboard_factory.reply_keyboard_stations_menu(final_stations)
            )
                