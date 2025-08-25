from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes

from application import MetroService, BusService, TramService, RodaliesService, MessageService
from providers.manager import UserDataManager, LanguageManager
from ui.keyboard_factory import KeyboardFactory

class FavoritesHandler:

    def __init__(self, message_service: MessageService, user_data_manager: UserDataManager, keyboard_factory: KeyboardFactory, metro_service: MetroService, bus_service: BusService, tram_service: TramService, rodalies_service: RodaliesService, language_manager: LanguageManager):
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.bus_service = bus_service
        self.tram_service = tram_service
        self.rodalies_servie = rodalies_service
        self.language_manager = language_manager

    async def show_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_user_id(update)
        favs = self.user_data_manager.get_favorites_by_user(user_id)

        await self.message_service.send_new_message(
            update,
            self.language_manager.t('common.loading.favorites'),
            reply_markup=self.keyboard_factory._back_reply_button()
        )

        if favs == []:
            await self.message_service.send_new_message(
                update,
                self.language_manager.t('favorites.empty'),
                reply_markup=self.keyboard_factory.help_menu()
            )

        else:
            await self.message_service.send_new_message(
                update,
                self.language_manager.t('favorites.message'),
                reply_markup=self.keyboard_factory.favorites_menu(favs)
            )

    async def add_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data
        _, item_type, line_id, item_id = data.split(":")

        # Añadir favorito
        if item_type == TransportType.METRO.value:
            item = await self.metro_service.get_station_by_id(item_id, line_id)
            
            new_fav_item = {
                "STATION_CODE": item_id,
                "STATION_NAME": item.NOM_ESTACIO,
                "STATION_GROUP_CODE": item.CODI_GRUP_ESTACIO,
                "LINE_NAME": item.EMOJI_NOM_LINIA,
                "LINE_CODE": line_id,
                "coordinates": item.coordinates
            }
        elif item_type == TransportType.BUS.value:
            item = await self.bus_service.get_stop_by_id(item_id)

            new_fav_item = {
                "STOP_CODE": item_id,
                "STOP_NAME": item.NOM_PARADA,
                "LINE_CODE": line_id,
                "coordinates": item.coordinates
            }
        elif item_type == TransportType.TRAM.value:
            item = await self.tram_service.get_stop_by_id(item_id, line_id)
            line = await self.tram_service.get_line_by_id(line_id)

            new_fav_item = {
                "STOP_CODE": item.id,
                "STOP_NAME": item.name,
                "LINE_NAME": line.name,
                "LINE_CODE": line_id,
                "coordinates": [item.latitude, item.longitude]
            }        
        elif item_type == TransportType.RODALIES.value:
            item = await self.rodalies_servie.get_station_by_id(item_id, line_id)
            line = await self.rodalies_servie.get_line_by_id(line_id)

            new_fav_item = {
                "STOP_CODE": item.id,
                "STOP_NAME": item.name,
                "LINE_NAME": line.name,
                "LINE_CODE": line_id,
                "coordinates": [item.latitude, item.longitude]
            }

        self.user_data_manager.add_favorite(user_id, item_type, new_fav_item)
        keyboard = self.keyboard_factory.update_menu(is_favorite=True, item_type=item_type, item_id=item_id, line_id=line_id, user_id=user_id, previous_callback=self.message_service.get_callback_query(update))

        await query.edit_message_reply_markup(reply_markup=keyboard)

    async def remove_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data
        _, item_type, line_id, item_id = data.split(":")

        self.user_data_manager.remove_favorite(user_id, item_type, item_id)
        keyboard = self.keyboard_factory.update_menu(is_favorite=False, item_type=item_type, item_id=item_id, line_id=line_id, user_id=user_id, previous_callback=self.message_service.get_callback_query(update))

        await query.edit_message_reply_markup(reply_markup=keyboard)