# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from ui.menu_handler import MenuHandler
from ui.metro_handler import MetroHandler
from ui.help_handler import HelpHandler
from ui.keyboard_factory import KeyboardFactory

from application.message_service import MessageService
from application.navigation_history import NavigationHistory
from application.metro_service import MetroService
from application.cache_service import CacheService
from application.update_manager import UpdateManager

from providers.secrets_manager import SecretsManager
from providers.transport_api_service import TransportApiService

def main():
    keyboard_factory = KeyboardFactory()
    secrets_manager = SecretsManager()
    message_service = MessageService()
    navigation_history = NavigationHistory()
    update_manager = UpdateManager()

    transport_api_service = TransportApiService(app_id=secrets_manager.get('APP_ID') , app_key=secrets_manager.get('APP_KEY'))
    cache_service = CacheService()
    metro_service = MetroService(transport_api_service, cache_service)
    
    menu_handler = MenuHandler(keyboard_factory, message_service, navigation_history)
    metro_handler = MetroHandler(keyboard_factory, metro_service, update_manager)
    help_handler = HelpHandler(message_service, keyboard_factory)

    application = ApplicationBuilder().token(secrets_manager.get('TELEGRAM_TOKEN')).build()

    application.add_handler(CommandHandler("start", menu_handler.show_menu))    
    application.add_handler(CallbackQueryHandler(menu_handler.show_menu, pattern=r"^menu$"))

    application.add_handler(CommandHandler("help", help_handler.show_help))    
    application.add_handler(CallbackQueryHandler(help_handler.show_help, pattern=r"^help$"))
    
    
    application.add_handler(CallbackQueryHandler(metro_handler.show_station, pattern=r"^metro_station"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_line_stations, pattern=r"^metro_line"))
    application.add_handler(CallbackQueryHandler(metro_handler.show_lines, pattern=r"^metro$"))
    application.add_handler(CallbackQueryHandler(metro_handler.close_updates, pattern=r"^close_updates:"))


    application.run_polling()

if __name__ == "__main__":
    main()
