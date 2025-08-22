from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from ui import MenuHandler, MetroHandler, BusHandler, TramHandler, FavoritesHandler, HelpHandler, LanguageHandler, KeyboardFactory, WebAppHandler, RodaliesHandler, ReplyHandler

from application import MessageService, MetroService, BusService, TramService, RodaliesService, CacheService, UpdateManager

from providers.manager import SecretsManager, UserDataManager, LanguageManager
from providers.api import TmbApiService, TramApiService, RodaliesApiService
from providers.helpers import logger

import asyncio



def main():    
    logger.info("Starting BCN Transit Bot (v1.2)")
    logger.info("Initializing services...")

    # Managers y servicios base
    language_manager = LanguageManager()
    secrets_manager = SecretsManager()
    message_service = MessageService()
    update_manager = UpdateManager()
    user_data_manager = UserDataManager()
    cache_service = CacheService()
    keyboard_factory = KeyboardFactory(language_manager)

    # Tokens y credenciales
    try:
        telegram_token = secrets_manager.get('TELEGRAM_TOKEN')
        tmb_app_id = secrets_manager.get('TMB_APP_ID')
        tmb_app_key = secrets_manager.get('TMB_APP_KEY')
        tram_client_id = secrets_manager.get('TRAM_CLIENT_ID')
        tram_client_secret = secrets_manager.get('TRAM_CLIENT_SECRET')

        logger.info("Secrets loaded successfully")
    except Exception as e:
        logger.critical(f"Error loading secrets: {e}")
        raise

    # APIs externas
    tmb_api_service = TmbApiService(app_id=tmb_app_id, app_key=tmb_app_key)
    tram_api_service = TramApiService(client_id=tram_client_id, client_secret=tram_client_secret)
    rodalies_api_service = RodaliesApiService()

    # Servicios del dominio
    metro_service = MetroService(tmb_api_service, language_manager, cache_service)
    bus_service = BusService(tmb_api_service, cache_service)
    tram_service = TramService(tram_api_service, language_manager, cache_service)
    rodalies_service = RodaliesService(rodalies_api_service, language_manager,cache_service)

    logger.info("Transport services initialized")

    # Handlers
    menu_handler = MenuHandler(keyboard_factory, message_service, user_data_manager, language_manager)
    metro_handler = MetroHandler(keyboard_factory, metro_service, update_manager, user_data_manager, message_service, language_manager)
    bus_handler = BusHandler(keyboard_factory, bus_service, update_manager, user_data_manager, message_service, language_manager)
    tram_handler = TramHandler(keyboard_factory, tram_service, update_manager, user_data_manager, message_service, language_manager)
    rodalies_handler = RodaliesHandler(keyboard_factory, rodalies_service, update_manager, user_data_manager, message_service, language_manager)
    favorites_handler = FavoritesHandler(user_data_manager, keyboard_factory, metro_service, bus_service, tram_service, rodalies_service, language_manager)
    help_handler = HelpHandler(message_service, keyboard_factory, language_manager)
    language_handler = LanguageHandler(keyboard_factory, user_data_manager, message_service, language_manager)
    web_app_handler = WebAppHandler(metro_handler, bus_handler, tram_handler, rodalies_handler)
    reply_handler = ReplyHandler(message_service, keyboard_factory, metro_service)

    logger.info("Handlers initialized")

    # Telegram app
    application = ApplicationBuilder().token(telegram_token).build()
    logger.info("Telegram application created")

    # START / MENU
    application.add_handler(CommandHandler("start", menu_handler.show_menu))    
    application.add_handler(CallbackQueryHandler(menu_handler.show_menu, pattern=r"^menu$"))
    application.add_handler(CallbackQueryHandler(menu_handler.back_to_menu, pattern=r"^back_to_menu"))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_handler.web_app_data_router)) 

    # HELP
    application.add_handler(CommandHandler("help", help_handler.show_help))    
    application.add_handler(CallbackQueryHandler(help_handler.show_help, pattern=r"^help$"))

    # METRO
    application.add_handler(CallbackQueryHandler(metro_handler.show_map, pattern=r"^metro_map"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_station, pattern=r"^metro_station"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_line_stations, pattern=r"^metro_line"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_lines, pattern=r"^metro$"))

    # BUS   
    application.add_handler(CallbackQueryHandler(bus_handler.show_stop, pattern=r"^bus_stop"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_line_stops, pattern=r"^bus_line"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_lines, pattern=r"^bus_page"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_lines, pattern=r"^bus$"))

    # TRAM
    application.add_handler(CallbackQueryHandler(tram_handler.show_map, pattern=r"^tram_map"))
    application.add_handler(CallbackQueryHandler(tram_handler.show_stop, pattern=r"^tram_stop"))    
    application.add_handler(CallbackQueryHandler(tram_handler.show_line_stops, pattern=r"^tram_line"))
    application.add_handler(CallbackQueryHandler(tram_handler.show_lines, pattern=r"^tram$"))

    # RODALIES
    application.add_handler(CallbackQueryHandler(rodalies_handler.show_station, pattern=r"^rodalies_station"))  
    application.add_handler(CallbackQueryHandler(rodalies_handler.show_line_stops, pattern=r"^rodalies_line"))
    application.add_handler(CallbackQueryHandler(rodalies_handler.show_lines, pattern=r"^rodalies$"))

    # FAVORITES
    application.add_handler(CallbackQueryHandler(favorites_handler.add_favorite, pattern=r"^add_fav"))
    application.add_handler(CallbackQueryHandler(favorites_handler.remove_favorite, pattern=r"^remove_fav"))
    application.add_handler(CallbackQueryHandler(favorites_handler.show_favorites, pattern=r"^favorites$"))

    # LANGUAGES
    application.add_handler(CallbackQueryHandler(language_handler.show_languages, pattern=r"^language"))
    application.add_handler(CallbackQueryHandler(language_handler.update_language, pattern=r"^set_language"))    

    application.add_handler(CallbackQueryHandler(metro_handler.close_updates, pattern=r"^close_updates:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_handler.reply_to_user))

    logger.info("Handlers registered successfully")
    logger.info("Starting Telegram polling loop...")

    try:
        application.run_polling()
    except Exception as e:
        logger.critical(f"Application crashed: {e}")
        raise

if __name__ == "__main__":
    main()
