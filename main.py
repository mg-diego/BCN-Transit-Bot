from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import logging
import asyncio

from ui import MenuHandler, MetroHandler, BusHandler, TramHandler, FavoritesHandler, HelpHandler, LanguageHandler, KeyboardFactory
from application import MessageService, MetroService, BusService, TramService, CacheService, UpdateManager
from providers import SecretsManager, TransportApiService, TramApiService, UserDataManager, LanguageManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    language_manager = LanguageManager()
    secrets_manager = SecretsManager()
    message_service = MessageService()
    update_manager = UpdateManager()
    user_data_manager = UserDataManager()
    cache_service = CacheService()

    keyboard_factory = KeyboardFactory(language_manager)

    transport_api_service = TransportApiService(app_id=secrets_manager.get('TMB_APP_ID') , app_key=secrets_manager.get('TMB_APP_KEY'))
    tram_api_service = TramApiService(client_id=secrets_manager.get('TRAM_CLIENT_ID'), client_secret=secrets_manager.get('TRAM_CLIENT_SECRET'))
    
    metro_service = MetroService(transport_api_service, language_manager, cache_service)
    bus_service = BusService(transport_api_service, cache_service)
    tram_service = TramService(tram_api_service, language_manager, cache_service)
    
    menu_handler = MenuHandler(keyboard_factory, message_service, user_data_manager, language_manager)
    metro_handler = MetroHandler(keyboard_factory, metro_service, update_manager, user_data_manager, message_service, language_manager)
    bus_handler = BusHandler(keyboard_factory, bus_service, update_manager, user_data_manager, message_service, language_manager)
    tram_handler = TramHandler(keyboard_factory, tram_service, update_manager, user_data_manager, message_service, language_manager)
    favorites_handler = FavoritesHandler(user_data_manager, keyboard_factory, metro_service, bus_service, language_manager)
    help_handler = HelpHandler(message_service, keyboard_factory, language_manager)
    language_handler = LanguageHandler(keyboard_factory, user_data_manager, message_service, language_manager)

    application = ApplicationBuilder().token(secrets_manager.get('TELEGRAM_TOKEN')).build()

    # START / MENU
    application.add_handler(CommandHandler("start", menu_handler.show_menu))    
    application.add_handler(CallbackQueryHandler(menu_handler.show_menu, pattern=r"^menu$"))
    application.add_handler(CallbackQueryHandler(menu_handler.back_to_menu, pattern=r"^back_to_menu"))

    # HELP
    application.add_handler(CommandHandler("help", help_handler.show_help))    
    application.add_handler(CallbackQueryHandler(help_handler.show_help, pattern=r"^help$"))
    
    # METRO
    application.add_handler(CallbackQueryHandler(metro_handler.show_station, pattern=r"^metro_station"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_line_stations, pattern=r"^metro_line"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_lines, pattern=r"^metro$"))

    # BUS
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bus_handler.show_stop))    
    application.add_handler(CallbackQueryHandler(bus_handler.show_stop, pattern=r"^bus_stop"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_line_stops, pattern=r"^bus_line"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_lines, pattern=r"^bus$"))

    # TRAM
    application.add_handler(CallbackQueryHandler(tram_handler.show_stop, pattern=r"^tram_stop"))    
    application.add_handler(CallbackQueryHandler(tram_handler.show_line_stops, pattern=r"^tram_line"))
    application.add_handler(CallbackQueryHandler(tram_handler.show_lines, pattern=r"^tram$"))
    
    # FAVORITES
    application.add_handler(CallbackQueryHandler(favorites_handler.add_favorite, pattern=r"^add_fav"))
    application.add_handler(CallbackQueryHandler(favorites_handler.remove_favorite, pattern=r"^remove_fav"))    
    application.add_handler(CallbackQueryHandler(favorites_handler.show_favorites, pattern=r"^favorites$"))

    # LANGUAGES
    application.add_handler(CallbackQueryHandler(language_handler.show_languages, pattern=r"^language"))
    application.add_handler(CallbackQueryHandler(language_handler.update_language, pattern=r"^set_language"))    

    application.add_handler(CallbackQueryHandler(metro_handler.close_updates, pattern=r"^close_updates:"))

    application.run_polling()

if __name__ == "__main__":
    logger.info('Starting bot...')
    
    main()