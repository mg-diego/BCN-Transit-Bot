import asyncio
import json

from telegram import Bot

from application import MessageService
from domain.common.alert import Alert
from providers.manager import UserDataManager
from providers.helpers.logger import logger

class AlertsService:
    def __init__(self, bot: Bot, message_service: MessageService, user_data_manager: UserDataManager, interval: int = 300):
        self.bot = bot
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        self.interval = interval

    async def check_alerts(self):
        """Comprueba alertas activas y notifica a los usuarios que tengan nuevas alertas."""
        try:
            logger.info(f"Checking alerts | {self.interval} seconds.")
            alerts = self.user_data_manager.get_alerts()
            users = self.user_data_manager.get_users()
            
            for user in [u for u in users if u.receive_alerts]:
                user_favorites = self.user_data_manager.get_favorites_by_user(user.user_id)
                user_favorites_station_codes = [f.get('code') for f in user_favorites]
                user_favorites_station_name = [f.get('name') for f in user_favorites]
                for alert in alerts:
                    for entity in alert.affected_entities:
                        if int(entity.station_code) in user_favorites_station_codes and entity.station_name in user_favorites_station_name:
                            if alert.id not in user.already_notified:
                                logger.info(f'SEND ALERT TO USER: {alert}')
                                self.user_data_manager.update_notified_alerts(user.user_id, alert.id)                                
                                await self.message_service.send_new_message_from_bot(self.bot, user.user_id, Alert.format_alert(alert))
                            else:
                                logger.info(f'ALERT ALREADY NOTIFIED: {alert.id}')

        except Exception as e:
            logger.exception(f"Error checking alerts: {e}")

    async def scheduler(self):
        """Función que se ejecuta de manera recurrente."""
        logger.info(f"Starting Alert Scheduler (configured every {self.interval} seconds)")
        
        try:
            iteration = 0
            while True:
                iteration += 1                
                await self.check_alerts()
                await asyncio.sleep(self.interval)
                
        except asyncio.CancelledError:
            print("PRINT: Tarea cancelada")
            logger.info("=== TAREA RECURRENTE CANCELADA ===")
            raise
        except Exception as e:
            print(f"PRINT: Error en tarea: {e}")
            logger.error(f"=== ERROR EN TAREA RECURRENTE: {e} ===")
            logger.exception("Stacktrace:")
            raise
        finally:
            print("PRINT: Función terminada")
            logger.info("=== FUNCIÓN RECURRENTE TERMINADA ===")

    def stop(self):
        """Detiene el scheduler de alertas."""
        self._running = False


    def build_favorites_indices(self):
        """Construye índices para búsquedas rápidas de favoritos."""
        self.favorites_by_station = {}  # {station_code: [favorites]}
        self.favorites_by_line = {}     # {line_code: [favorites]}
        self.favorites_by_user = {}     # {user_id: [favorites]}
        
        for favorite in self.all_favorites:
            user_id = favorite['user_id']
            station_code = str(favorite.get('code', ''))
            line_code = str(favorite.get('codi_linia', ''))
            
            # Índice por usuario
            if user_id not in self.favorites_by_user:
                self.favorites_by_user[user_id] = []
            self.favorites_by_user[user_id].append(favorite)
            
            # Índice por estación
            if station_code:
                if station_code not in self.favorites_by_station:
                    self.favorites_by_station[station_code] = []
                self.favorites_by_station[station_code].append(favorite)
            
            # Índice por línea
            if line_code:
                if line_code not in self.favorites_by_line:
                    self.favorites_by_line[line_code] = []
                self.favorites_by_line[line_code].append(favorite)

    def find_users_for_alert_optimized(self, alert):
        """Versión optimizada usando índices."""
        try:
            if isinstance(alert['affected_entities'], str):
                affected_entities = json.loads(alert['affected_entities'])
            else:
                affected_entities = alert['affected_entities']
            
            affected_users = set()  # Usar set para evitar duplicados
            
            for entity in affected_entities:
                # Buscar favoritos potencialmente afectados usando índices
                candidate_favorites = set()
                
                # Buscar por estación
                if entity.get('station_code') and entity.get('station_code') != 'ALL':
                    station_favorites = self.favorites_by_station.get(entity['station_code'], [])
                    candidate_favorites.update(station_favorites)
                
                # Buscar por línea si no hay estación específica
                elif entity.get('line_code') and entity.get('line_code') != 'ALL':
                    line_favorites = self.favorites_by_line.get(entity['line_code'], [])
                    candidate_favorites.update(line_favorites)
                
                # Si es "ALL", necesitamos verificar todos los favoritos del tipo
                else:
                    candidate_favorites = [f for f in self.all_favorites if f.get('type') == alert.get('type')]
                
                # Verificar coincidencias exactas
                for favorite in candidate_favorites:
                    if self._matches_entity(favorite, entity):
                        affected_users.add(favorite['user_id'])
            
            # Convertir user_ids a objetos user completos
            result = []
            for user_id in affected_users:
                user = self.get_user_by_id(user_id)
                if user:
                    affected_favorites = self.get_affected_favorites_by_alert(alert, self.favorites_by_user.get(user_id, []))
                    result.append({
                        'user': user,
                        'affected_favorites': affected_favorites
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding users for alert {alert.get('id')}: {e}")
            return []
