from telegram import Update
from telegram.ext import ContextTypes

class FavoritesHandler:

    def __init__(self, user_data_manager, keyboard_factory, metro_service, bus_service):
        self.user_data_manager = user_data_manager
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.bus_service = bus_service

    async def show_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        favs = self.user_data_manager.get_favorites_by_user(user_id)

        if favs == []:
            await query.edit_message_text(
                f"Hola {query.from_user.first_name} 👋\nAún no tienes nada en tu lista de favoritos. ¡Empieza a añadir algunos para encontrarlos más rápido!",
                reply_markup=self.keyboard_factory.help_menu()
            )

        else:
            await query.edit_message_text(
                "📌 Tus favoritos:",
                reply_markup=self.keyboard_factory.favorites_menu(favs)
            )

    async def add_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data
        _, item_type, line_id, item_id = data.split(":")

        # Añadir favorito
        if item_type == "metro":
            item = await self.metro_service.get_station_by_id(item_id, line_id)
            
            new_fav_item = {
                "CODI_ESTACIO": item_id,
                "NOM_ESTACIO": item.NOM_ESTACIO,
                "CODI_GRUP_ESTACIO": item.CODI_GRUP_ESTACIO,
                "NOM_LINIA": item.EMOJI_NOM_LINIA,
                "CODI_LINIA": line_id,
                "coordinates": item.coordinates
            }
        elif item_type == "bus":
            item = await self.bus_service.get_stop_by_id(item_id, line_id)

            new_fav_item = {
                "CODI_PARADA": item_id,
                "NOM_PARADA": item.NOM_PARADA,
                "CODI_LINIA": line_id,
                "coordinates": item.coordinates
            }

        self.user_data_manager.add_favorite(user_id, item_type, new_fav_item)
        keyboard = self.keyboard_factory.update_menu(is_favorite=True, item_type=item_type, item_id=item_id, line_id=line_id, user_id=user_id)

        await query.edit_message_reply_markup(reply_markup=keyboard)
        await query.answer(text="Añadido a favoritos ❤️", show_alert=True)

    async def remove_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data
        _, item_type, line_id, item_id = data.split(":")

        self.user_data_manager.remove_favorite(user_id, item_type, item_id)
        keyboard = self.keyboard_factory.update_menu(is_favorite=False, item_type=item_type, item_id=item_id, line_id=line_id, user_id=user_id)

        await query.edit_message_reply_markup(reply_markup=keyboard)
        await query.answer(text="Eliminado de favoritos 💔", show_alert=True)