import asyncio
import html
import os
import logging

from telegram import Bot
from telegram.error import TelegramError

from application import MessageService
from domain.clients import ClientType
from domain.common.alert import Alert
from providers.manager import UserDataManager
from firebase_admin import messaging

from providers.helpers import logger
from providers.manager.user_data_manager import audit_action

class AlertsService:
    def __init__(self, bot: Bot, message_service: MessageService, user_data_manager: UserDataManager, interval: int = 300):
        self.bot = bot
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        
        env_interval = os.getenv("ALERTS_SERVICE_INTERVAL")
        self.interval = int(env_interval) if env_interval else interval
        
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            logger.warning("⚠️ DEBUG: El servicio YA estaba corriendo. Saliendo sin hacer nada.")
            return

        self._running = True
        
        try:
            self._task = asyncio.create_task(self.scheduler())
            logger.info(f"🚀 Alerts Service started. Interval: {self.interval}s")
        except Exception as e:
            logger.error(f"❌ DEBUG: Error al crear la tarea: {e}")

    async def stop(self):
        """Detiene el servicio correctamente"""
        logger.info("🛑 Stopping Alerts Service...")
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def send_push_notification(self, fcm_token: str, title: str, body: str, data: dict = None):
        """Envía push notification en un hilo separado para no bloquear asyncio."""
        try:
            title = html.unescape(title)
            body = html.unescape(body)
            
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=fcm_token,
            )
            
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, messaging.send, message)
            
            logger.debug(f"Push sent: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending push to {fcm_token[:10]}...: {e}")
            return None

    async def _notify_user(self, client_source: ClientType, user_id: str, fcm_token, alert):
        """Lógica unitaria para notificar a un usuario."""
        try:
            await self.user_data_manager.update_notified_alerts(user_id, alert.id)
            await self.user_data_manager.register_notification(client_source, user_id, alert)

            if fcm_token:
                logger.info(f"Sending new PUSH NOTIFICATION to '{user_id}' with alert {alert.id}...")
                await self.send_push_notification(
                    fcm_token,
                    title="BCN Transit | Nueva Alerta",
                    body=Alert.format_app_alert(alert),
                    data={"alert_id": str(alert.id), "click_action": "FLUTTER_NOTIFICATION_CLICK"}
                )
            else:
                try:
                    logger.info(f"Sending new TELEGRAM NOTIFICATION to '{user_id}' with alert {alert.id}...")
                    await self.message_service.send_new_message_from_bot(
                        self.bot, 
                        user_id, 
                        Alert.format_html_alert(alert)
                    )
                except TelegramError as te:
                    logger.warning(f"Telegram error for user {user_id}: {te}")

            return True
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return False

    async def check_new_alerts(self):
        try:
            alerts = await self.user_data_manager.get_alerts(only_active=True)
            if not alerts:
                return

            users_with_favs = await self.user_data_manager.get_active_users_with_favorites()

            logger.info(f"Checking {len(alerts)} alerts for {len(users_with_favs)} users (with favorites)...")

            notifications_tasks = []

            for user, user_favorites in users_with_favs:        
                fav_codes = {f.STATION_CODE for f in user_favorites}

                for alert in alerts:
                    if alert.id in user.already_notified:
                        continue

                    should_notify = any(
                        entity.station_code
                        and str(entity.station_code) in fav_codes
                        for entity in alert.affected_entities
                    )

                    if should_notify:
                        notifications_tasks.append(
                            self._notify_user(ClientType.SYSTEM.value, user.user_id, user.fcm_token, alert)
                        )

            if notifications_tasks:
                await asyncio.gather(*notifications_tasks, return_exceptions=True)

        except Exception as e:
            logger.exception(f"❌ Critical error checking alerts: {e}")

    async def scheduler(self):
        """Bucle infinito controlado"""
        logger.info(f"Starting Alert Scheduler loop (Interval: {self.interval}s)")
        
        while self._running:
            try:
                await self.check_new_alerts()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
        
        logger.info("Scheduler loop exited.")