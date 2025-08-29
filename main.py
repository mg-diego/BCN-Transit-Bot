import asyncio
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from ui import (
    MenuHandler, MetroHandler, BusHandler, TramHandler, FavoritesHandler, HelpHandler, 
    LanguageHandler, KeyboardFactory, WebAppHandler, RodaliesHandler, ReplyHandler, AdminHandler, SettingsHandler, BicingHandler
)
from application import MessageService, MetroService, BusService, TramService, RodaliesService, BicingService, CacheService, UpdateManager
from providers.manager import SecretsManager, UserDataManager, LanguageManager
from providers.api import TmbApiService, TramApiService, RodaliesApiService, BicingApiService
from providers.helpers import logger


class BotApp:
    """
    BCN Transit Bot main application.
    Initializes services, handlers, runs seeder, and starts Telegram polling.
    """

    def __init__(self):
        self.telegram_token = None
        self.admin_id = None

        # Services
        self.language_manager = None
        self.secrets_manager = None
        self.message_service = None
        self.update_manager = None
        self.user_data_manager = None
        self.cache_service = None
        self.keyboard_factory = None

        # APIs
        self.tmb_api_service = None
        self.tram_api_service = None
        self.rodalies_api_service = None
        self.bicing_api_service = None

        # Domain services
        self.metro_service = None
        self.bus_service = None
        self.tram_service = None
        self.rodalies_service = None
        self.bicing_service = None

        # Handlers
        self.admin_handler = None
        self.menu_handler = None
        self.metro_handler = None
        self.bus_handler = None
        self.tram_handler = None
        self.rodalies_handler = None
        self.favorites_handler = None
        self.help_handler = None
        self.language_handler = None
        self.web_app_handler = None
        self.reply_handler = None

        # Telegram app
        self.application = None

    def init_services(self):
        """Initialize managers, APIs, domain services and handlers."""

        logger.info("Initializing BCN Transit Bot services...")

        # Managers
        self.language_manager = LanguageManager()
        self.secrets_manager = SecretsManager()
        self.message_service = MessageService()
        self.update_manager = UpdateManager(self.message_service)
        self.user_data_manager = UserDataManager()
        self.cache_service = CacheService()
        self.keyboard_factory = KeyboardFactory(self.language_manager)

        # Load secrets
        try:
            self.telegram_token = self.secrets_manager.get('TELEGRAM_TOKEN')
            tmb_app_id = self.secrets_manager.get('TMB_APP_ID')
            tmb_app_key = self.secrets_manager.get('TMB_APP_KEY')
            tram_client_id = self.secrets_manager.get('TRAM_CLIENT_ID')
            tram_client_secret = self.secrets_manager.get('TRAM_CLIENT_SECRET')
            self.admin_id = self.secrets_manager.get('ADMIN_ID')
            logger.info("Secrets loaded successfully")
        except Exception as e:
            logger.critical(f"Error loading secrets: {e}")
            raise

        # APIs
        self.tmb_api_service = TmbApiService(app_id=tmb_app_id, app_key=tmb_app_key)
        self.tram_api_service = TramApiService(client_id=tram_client_id, client_secret=tram_client_secret)
        self.rodalies_api_service = RodaliesApiService()
        self.bicing_api_service = BicingApiService()

        # Domain services
        self.metro_service = MetroService(self.tmb_api_service, self.language_manager, self.cache_service)
        self.bus_service = BusService(self.tmb_api_service, self.cache_service)
        self.tram_service = TramService(self.tram_api_service, self.language_manager, self.cache_service)
        self.rodalies_service = RodaliesService(self.rodalies_api_service, self.language_manager, self.cache_service)
        self.bicing_service = BicingService(self.bicing_api_service, self.cache_service)

        logger.info("Transport services initialized")

        # Handlers
        self.admin_handler = AdminHandler(self.admin_id)
        self.menu_handler = MenuHandler(self.keyboard_factory, self.message_service, self.user_data_manager, self.language_manager, self.update_manager)
        self.metro_handler = MetroHandler(self.keyboard_factory, self.metro_service, self.update_manager, self.user_data_manager, self.message_service, self.language_manager)
        self.bus_handler = BusHandler(self.keyboard_factory, self.bus_service, self.update_manager, self.user_data_manager, self.message_service, self.language_manager)
        self.tram_handler = TramHandler(self.keyboard_factory, self.tram_service, self.update_manager, self.user_data_manager, self.message_service, self.language_manager)
        self.rodalies_handler = RodaliesHandler(self.keyboard_factory, self.rodalies_service, self.update_manager, self.user_data_manager, self.message_service, self.language_manager)
        self.bicing_handler = BicingHandler(self.keyboard_factory, self.bicing_service, self.update_manager, self.user_data_manager, self.message_service, self.language_manager)

        self.favorites_handler = FavoritesHandler(self.message_service, self.user_data_manager, self.keyboard_factory, self.metro_service, self.bus_service, self.tram_service, self.rodalies_service, self.bicing_service, self.language_manager)
        self.help_handler = HelpHandler(self.message_service, self.keyboard_factory, self.language_manager)
        self.language_handler = LanguageHandler(self.keyboard_factory, self.user_data_manager, self.message_service, self.language_manager, self.update_manager)
        self.web_app_handler = WebAppHandler(self.metro_handler, self.bus_handler, self.tram_handler, self.rodalies_handler)
        self.settings_handler = SettingsHandler(self.message_service, self.keyboard_factory, self.language_manager)
        self.reply_handler = ReplyHandler(self.menu_handler, self.metro_handler, self.bus_handler, self.tram_handler, self.rodalies_handler,
                                          self.favorites_handler, self.language_handler, self.help_handler, self.settings_handler, self.bicing_handler)

        logger.info("Handlers initialized")

    async def run_seeder(self):
        logger.info("Initializing Seeder...")
        total_start = datetime.now()

        service_times = []

        try:
            preload_tasks = [
                ("Metro", self.metro_service, ["get_all_lines", "get_all_stations"]),
                ("Bus", self.bus_service, ["get_all_lines", "get_all_stops"]),
                ("Tram", self.tram_service, ["get_all_lines", "get_all_stops"]),
                ("Rodalies", self.rodalies_service, ["get_all_lines", "get_all_stations"]),
                ("Bicing", self.bicing_service, ["get_all_lines", "get_all_stations"]),
            ]

            for name, service, methods in preload_tasks:
                start = datetime.now()
                for method_name in methods:
                    method = getattr(service, method_name)
                    await method()
                elapsed = int((datetime.now() - start).total_seconds())
                service_times.append((name, elapsed))

            # Total elapsed
            total_elapsed = int((datetime.now() - total_start).total_seconds())
            total_minutes, total_seconds = divmod(total_elapsed, 60)
            logger.info(
                f"Seeder completed in {total_minutes}m {total_seconds}s" if total_minutes > 0 else f"Seeder completed in {total_seconds}s"
            )

            # Detailed per-service logs
            for name, elapsed in service_times:
                minutes, seconds = divmod(elapsed, 60)
                logger.info(
                    f"{name} seeder finalized in {minutes}m {seconds}s" if minutes > 0 else f"{name} seeder finalized in {seconds}s"
                )

        except Exception as e:
            logger.error(f"Error running seeder: {e}")
            raise


    def register_handlers(self):
        """Register Telegram handlers."""
        self.application.add_handler(CommandHandler("start", self.menu_handler.show_menu))
        self.application.add_handler(CallbackQueryHandler(self.menu_handler.show_menu, pattern=r"^menu$"))
        self.application.add_handler(CallbackQueryHandler(self.menu_handler.back_to_menu, pattern=r"^back_to_menu"))
        self.application.add_handler(CallbackQueryHandler(self.menu_handler.close_updates, pattern=r"^close_updates:"))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_handler.web_app_data_router))

        # METRO
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_list, pattern=r"^metro_list"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_map, pattern=r"^metro_map"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_station, pattern=r"^metro_station"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_station_access, pattern=r"^metro_access"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_station_connections, pattern=r"^metro_connections"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.ask_search_method, pattern=r"^metro_line"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_list, pattern=r"^metro_page"))
        self.application.add_handler(CallbackQueryHandler(self.metro_handler.show_lines, pattern=r"^metro$"))

        # BUS
        self.application.add_handler(CallbackQueryHandler(self.bus_handler.show_stop, pattern=r"^bus_stop"))
        self.application.add_handler(CallbackQueryHandler(self.bus_handler.show_line_stops, pattern=r"^bus_line"))
        self.application.add_handler(CallbackQueryHandler(self.bus_handler.show_bus_category_lines, pattern=r"^bus_category"))
        self.application.add_handler(CallbackQueryHandler(self.bus_handler.show_lines, pattern=r"^bus$"))

        # TRAM
        self.application.add_handler(CallbackQueryHandler(self.tram_handler.show_list, pattern=r"^tram_list"))
        self.application.add_handler(CallbackQueryHandler(self.tram_handler.show_map, pattern=r"^tram_map"))
        self.application.add_handler(CallbackQueryHandler(self.tram_handler.show_stop, pattern=r"^tram_stop"))
        self.application.add_handler(CallbackQueryHandler(self.tram_handler.ask_search_method, pattern=r"^tram_line"))
        self.application.add_handler(CallbackQueryHandler(self.tram_handler.show_lines, pattern=r"^tram$"))

        # RODALIES
        self.application.add_handler(CallbackQueryHandler(self.rodalies_handler.show_station, pattern=r"^rodalies_station"))
        self.application.add_handler(CallbackQueryHandler(self.rodalies_handler.show_line_stops, pattern=r"^rodalies_line"))
        self.application.add_handler(CallbackQueryHandler(self.rodalies_handler.show_lines, pattern=r"^rodalies$"))

        # BICING
        self.application.add_handler(CallbackQueryHandler(self.bicing_handler.show_station, pattern=r"^bicing_station"))

        # FAVORITES
        self.application.add_handler(CallbackQueryHandler(self.favorites_handler.add_favorite, pattern=r"^add_fav"))
        self.application.add_handler(CallbackQueryHandler(self.favorites_handler.remove_favorite, pattern=r"^remove_fav"))
        self.application.add_handler(CallbackQueryHandler(self.favorites_handler.show_favorites, pattern=r"^favorites$"))

        # SETTINGS
        ### LANGUAGES 
        self.application.add_handler(CallbackQueryHandler(self.language_handler.show_languages, pattern=r"^language"))
        self.application.add_handler(CallbackQueryHandler(self.language_handler.update_language, pattern=r"^set_language"))
        ### HELP
        self.application.add_handler(CommandHandler("help", self.help_handler.show_help))
        self.application.add_handler(CallbackQueryHandler(self.help_handler.show_help, pattern=r"^help$"))

        # SEARCH
        self.application.add_handler(MessageHandler(filters.LOCATION, self.reply_handler.location_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.reply_handler.reply_router))

        # ADMIN
        self.application.add_handler(CommandHandler("commit", self.admin_handler.commit_command))
        self.application.add_handler(CommandHandler("logs", self.admin_handler.tail_log_command))
        self.application.add_handler(CommandHandler("uptime", self.admin_handler.uptime_command))

        logger.info("Handlers registered successfully")

    async def run(self):
        """Main async entrypoint for the bot."""
        # Initialize synchronous services
        self.init_services()
        
        # Run the async seeder
        await self.run_seeder()

        # Telegram application
        self.application = ApplicationBuilder().token(self.telegram_token).build()
        self.register_handlers()

        logger.info("Starting Telegram polling loop...")
        
        try:
            # Initialize and start the application
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep the bot running
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await asyncio.Event().wait()  # Run forever until interrupted
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            # Cleanup
            logger.info("Stopping bot...")
            if self.application.updater.running:
                await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


async def main():
    """Async main function to run the bot."""
    bot = BotApp()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())