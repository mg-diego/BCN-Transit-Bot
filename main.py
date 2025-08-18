from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import logging
import asyncio

from ui.menu_handler import MenuHandler
from ui.metro_handler import MetroHandler
from ui.bus_handler import BusHandler
from ui.favorites_handler import FavoritesHandler
from ui.help_handler import HelpHandler
from ui.keyboard_factory import KeyboardFactory

from application.message_service import MessageService
from application.metro_service import MetroService
from application.bus_service import BusService
from application.cache_service import CacheService
from application.update_manager import UpdateManager

from providers.secrets_manager import SecretsManager
from providers.transport_api_service import TransportApiService
from providers.user_data_manager import UserDataManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    keyboard_factory = KeyboardFactory()
    secrets_manager = SecretsManager()
    message_service = MessageService()
    update_manager = UpdateManager()
    user_data_manager = UserDataManager()

    transport_api_service = TransportApiService(app_id=secrets_manager.get('APP_ID') , app_key=secrets_manager.get('APP_KEY'))
    cache_service = CacheService()
    metro_service = MetroService(transport_api_service, cache_service)
    bus_service = BusService(transport_api_service, cache_service)
    
    menu_handler = MenuHandler(keyboard_factory, message_service, user_data_manager)
    metro_handler = MetroHandler(keyboard_factory, metro_service, update_manager, user_data_manager, message_service)
    bus_handler = BusHandler(keyboard_factory, bus_service, update_manager, user_data_manager, message_service)
    favorites_handler = FavoritesHandler(user_data_manager, keyboard_factory, metro_service, bus_service)
    help_handler = HelpHandler(message_service, keyboard_factory)

    application = ApplicationBuilder().token(secrets_manager.get('TELEGRAM_TOKEN')).build()

    application.add_handler(CommandHandler("start", menu_handler.show_menu))    
    application.add_handler(CallbackQueryHandler(menu_handler.show_menu, pattern=r"^menu$"))

    application.add_handler(CommandHandler("help", help_handler.show_help))    
    application.add_handler(CallbackQueryHandler(help_handler.show_help, pattern=r"^help$"))
    
    application.add_handler(CallbackQueryHandler(metro_handler.show_station, pattern=r"^metro_station"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_line_stations, pattern=r"^metro_line"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_lines, pattern=r"^metro$"))

    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bus_handler.show_stop))
    
    application.add_handler(CallbackQueryHandler(bus_handler.show_stop, pattern=r"^bus_stop"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_line_stops, pattern=r"^bus_line"))
    application.add_handler(CallbackQueryHandler(bus_handler.show_lines, pattern=r"^bus$"))   
    
    application.add_handler(CallbackQueryHandler(favorites_handler.add_favorite, pattern=r"^add_fav"))
    application.add_handler(CallbackQueryHandler(favorites_handler.remove_favorite, pattern=r"^remove_fav"))    
    application.add_handler(CallbackQueryHandler(favorites_handler.show_favorites, pattern=r"^favorites$"))

    application.add_handler(CallbackQueryHandler(metro_handler.close_updates, pattern=r"^close_updates:"))


    application.run_polling()

def test():
    user_data_manager = UserDataManager("TMB")
    #users = await fav_manager.get_users()
    #print(users)
    uses = user_data_manager.register_user(user_id="123", username="diego")
    print("Veces usado:", uses)

if __name__ == "__main__":
    logger.info('Starting bot...')
    main()
    #test()