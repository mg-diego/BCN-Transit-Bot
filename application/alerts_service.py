import asyncio
import json
from datetime import datetime

from telegram import Bot

from application import MessageService
from domain.common.alert import Alert
from providers.helpers.logger import logger
from providers.manager import UserDataManager


class AlertsService:
    def __init__(
        self,
        bot: Bot,
        message_service: MessageService,
        user_data_manager: UserDataManager,
        interval: int = 60,
    ):
        self.bot = bot
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        self.interval = interval

    async def check_new_alerts(self):
        """Comprueba alertas activas y notifica a los usuarios que tengan nuevas alertas."""
        try:
            alerts = self.user_data_manager.get_alerts()
            users = self.user_data_manager.get_users()

            logger.debug(
                f"Total alerts fetched: {len(alerts)} | Total users: {len(users)}"
            )

            sent_alerts_count = 0
            already_notified_count = 0

            for user in [u for u in users if u.receive_notifications]:
                logger.debug(
                    f"Processing user {user.user_id} | {user.username if hasattr(user, 'username') else 'Unknown'}"
                )

                user_favorites = self.user_data_manager.get_favorites_by_user(
                    user.user_id
                )
                if not user_favorites:
                    logger.warning(
                        f"User {user.user_id} has no favorite stations. Skipping..."
                    )
                    continue

                user_favorites_station_codes = [f.get("code") for f in user_favorites]
                user_favorites_station_names = [f.get("name") for f in user_favorites]
                logger.debug(
                    f"User {user.user_id} favorites: {user_favorites_station_names} ({user_favorites_station_codes})"
                )

                for alert in alerts:
                    for entity in alert.affected_entities:
                        if (
                            entity.station_code is not None
                            and int(entity.station_code) in user_favorites_station_codes
                            and entity.station_name in user_favorites_station_names
                        ):
                            if alert.id not in user.already_notified:
                                logger.info(
                                    f"🚨 Sending new alert {alert.id} to user {user.user_id} "
                                    f"({entity.station_name} - code {entity.station_code})"
                                )
                                self.user_data_manager.update_notified_alerts(
                                    user.user_id, alert.id
                                )
                                await self.message_service.send_new_message_from_bot(
                                    self.bot, user.user_id, Alert.format_alert(alert)
                                )
                                sent_alerts_count += 1
                            else:
                                logger.debug(
                                    f"Alert {alert.id} already notified to user {user.user_id} "
                                    f"({entity.station_name} - code {entity.station_code})"
                                )
                                already_notified_count += 1

            logger.info(
                f"✅ Alert check completed | New alerts sent: {sent_alerts_count} | "
                f"Already notified: {already_notified_count} | Total alerts processed: {len(alerts)}"
            )

        except Exception as e:
            logger.exception(f"❌ Error while checking alerts: {e}")
        except Exception as e:
            logger.exception(f"Error checking alerts: {e}")

    async def remove_expired_alerts(self):
        alerts = self.user_data_manager.get_alerts()
        users = self.user_data_manager.get_users()
        now = datetime.now()

        logger.debug(f"Loaded {len(alerts)} alerts and {len(users)} users")
        removed_alerts = 0
        removed_notified_references = 0

        for alert in alerts:
            if alert.end_date and alert.end_date < now:
                logger.info(
                    f"🗑️ Alert expired → Removing | ID={alert.id}, Transport={alert.transport_type}, EndDate={alert.end_date}"
                )

                # Eliminar referencias de esta alerta en los usuarios
                for user in users:
                    if alert.id in user.already_notified:
                        self.user_data_manager.remove_deprecated_notified_alert(
                            user.user_id, alert.id
                        )
                        removed_notified_references += 1
                        logger.debug(
                            f"   ↳ Removed alert {alert.id} from user {user.user_id} notified list"
                        )

                # Eliminar la alerta en sí
                self.user_data_manager.remove_alert(alert)
                removed_alerts += 1
                logger.info(f"✅ Alert {alert.id} successfully removed")

        if removed_alerts > 0:
            logger.info(
                f"🎯 Cleanup complete | Removed {removed_alerts} expired alerts and {removed_notified_references} notified references"
            )
        else:
            logger.info("✨ No expired alerts found")

        logger.debug("🧹 Expired alerts cleanup finished")

    async def scheduler(self):
        """Función que se ejecuta de manera recurrente."""
        logger.info(
            f"Starting Alert Scheduler (configured every {self.interval} seconds)"
        )

        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(
                    f"🔍 Starting Alert Service scheduler | Interval: {self.interval} seconds"
                )
                await self.remove_expired_alerts()
                await self.check_new_alerts()
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"PRINT: Error en tarea: {e}")
            logger.error(f"=== Exception in Alerts Service scheduler: {e} ===")
            logger.exception("Stacktrace:")
            raise

    def stop(self):
        """Detiene el scheduler de alertas."""
        self._running = False
