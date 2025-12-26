import asyncio
from datetime import datetime
import html

from telegram import Bot

from application import MessageService
from domain.common.alert import Alert
from providers.manager import UserDataManager
from providers.helpers.logger import logger
from firebase_admin import messaging
from providers.manager import firebase_client

class AlertsService:
    def __init__(self, bot: Bot, message_service: MessageService, user_data_manager: UserDataManager, interval: int = 300):
        self.bot = bot
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        self.interval = interval

    def send_push_notification(self, fcm_token: str, title: str, body: str, data: dict = None):
        """
        Envía una notificación push a un dispositivo específico
        
        Args:
            fcm_token: El token FCM del dispositivo
            title: Título de la notificación
            body: Cuerpo de la notificación
            data: Datos adicionales (opcional)
        """
        try:
            title = html.unescape(title)
            body = html.unescape(body)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
            )
            
            response = messaging.send(message)
            print(f"Notificación enviada exitosamente: {response}")
            return response
        except Exception as e:
            print(f"Error enviando notificación: {e}")
            raise

    async def check_new_alerts(self):
        """Comprueba alertas activas y notifica a los usuarios que tengan nuevas alertas."""
        try:
            alerts = await self.user_data_manager.get_alerts()
            users = await self.user_data_manager.get_users()

            logger.debug(f"Total alerts fetched: {len(alerts)} | Total users: {len(users)}")

            sent_alerts_count = 0
            already_notified_count = 0

            for user in [u for u in users if u.receive_notifications]:
                logger.debug(f"Processing user {user.user_id} | {user.username if hasattr(user, 'username') else 'Unknown'}")

                user_favorites = await self.user_data_manager.get_favorites_by_user(user.user_id)
                if not user_favorites:
                    logger.warning(f"User {user.user_id} has no favorite stations. Skipping...")
                    continue

                user_favorites_station_codes = [f.STATION_CODE for f in user_favorites]
                user_favorites_station_names = [f.STATION_NAME for f in user_favorites]
                logger.debug(f"User {user.user_id} favorites: {user_favorites_station_names} ({user_favorites_station_codes})")

                for alert in alerts:
                    a = 2
                    for entity in alert.affected_entities:
                        if (
                            entity.station_code is not None
                            and entity.station_code != "ALL"
                            and entity.station_code in user_favorites_station_codes
                            and entity.station_name in user_favorites_station_names
                        ):
                            if alert.id not in user.already_notified:
                                logger.info(
                                    f"🚨 Sending new alert {alert.id} to user {user.user_id} "
                                    f"({entity.station_name} - code {entity.station_code})"
                                )
                                await self.user_data_manager.update_notified_alerts(user.user_id, alert.id)
                                if user.fcm_token is not None:
                                    self.send_push_notification(
                                        user.fcm_token,
                                        title="BCN Transit | Nueva Alerta",
                                        body=Alert.format_app_alert(alert),
                                        data={"alert_id": str(alert.id)}
                                    )
                                else:
                                    await self.message_service.send_new_message_from_bot(
                                        self.bot, user.user_id, Alert.format_html_alert(alert)
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

    async def remove_duplicated_alerts(self):
        alerts = await self.user_data_manager.get_alerts()
        seen = set()
        duplicated_alerts = []

        # Detectar duplicados por combinación (id, transport_type)
        for alert in alerts:
            key = (alert.id, alert.transport_type)
            if key in seen:
                duplicated_alerts.append(alert)
            else:
                seen.add(key)

        if not duplicated_alerts:
            logger.info("✅ No duplicated alerts found.")
            return

        # 🔍 Buscar índices reales por ID antes de borrar (para evitar desincronización)
        try:
            all_values = self.user_data_manager.alerts_ws.get_all_values()
        except Exception as e:
            logger.error(f"❌ Error reading sheet: {e}")
            return

        # Creamos un mapa {id: row_index}
        # ⚠️ Ajusta el índice inicial si tienes encabezado (fila 1)
        id_to_row = {}
        for idx, row in enumerate(all_values, start=1):
            if len(row) > 0:
                id_to_row[row[0]] = idx  # asume que el ID está en la primera columna

        # Buscamos las filas a eliminar por ID
        rows_to_delete = []
        for dup in duplicated_alerts:
            row_idx = id_to_row.get(str(dup.id))
            if row_idx:
                rows_to_delete.append(row_idx)
            else:
                logger.warning(f"⚠️ Could not find alert ID={dup.id} in sheet.")

        # 🔽 Borramos en orden descendente para evitar el error "row doesn't exist"
        rows_to_delete = sorted(set(rows_to_delete), reverse=True)

        for row_idx in rows_to_delete:
            try:
                self.user_data_manager.alerts_ws.delete_rows(row_idx)
                logger.info(f"🗑️ Removed duplicated alert at row {row_idx}")
            except Exception as e:
                logger.error(f"⚠️ Error deleting row {row_idx}: {e}")

        logger.info(f"🎯 Cleanup complete | Removed {len(rows_to_delete)} duplicated alerts")    


    async def scheduler(self):
        """Función que se ejecuta de manera recurrente."""
        logger.info(f"Starting Alert Scheduler (configured every {self.interval} seconds)")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"🔍 Starting Alert Service scheduler | Interval: {self.interval} seconds")
                await self.remove_duplicated_alerts()
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