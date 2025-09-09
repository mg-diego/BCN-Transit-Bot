import json
from typing import Dict, List
import uuid
from domain.common.alert import AffectedEntity, Alert, Publication
from domain.common.user import User
from domain.transport_type import TransportType
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from providers.helpers import logger
import ast
from functools import wraps

from providers.manager.audit_logger import AuditLogger

def audit_action(action_type: str, command_or_button: str = "", params_args: list = None):
    """
    Decorador para registrar auditoría de acciones de usuario.

    :param action_type: Tipo de acción, ej. "SEARCH", "START", etc.
    :param command_or_button: Nombre del comando o botón.
    :param params_args: Lista de nombres de argumentos de la función que se guardarán en params.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                # Ejecutar la función original primero
                result = func(self, *args, **kwargs)

                # Intentar extraer audit_logger
                audit_logger = getattr(self, "audit_logger", None)
                if not audit_logger:
                    return result

                # Extraer user_id, username, chat_id si existen
                update = args[0] if args else None
                user_id = update.effective_user.id
                username = update.effective_user.first_name
                chat_type = update.effective_chat.type.value
                callback = update.callback_query.data if update.callback_query else None

                # Construir params automáticamente
                params = {}
                if params_args:
                    func_params = func.__code__.co_varnames
                    for name in params_args:
                        if name in kwargs:
                            if isinstance(kwargs[name], TransportType):
                                params[name] = kwargs[name].value
                            else:
                                params[name] = kwargs[name]
                        elif name in func_params:
                            idx = func_params.index(name)
                            if idx < len(args):
                                params[name] = args[idx]

                # Añadir evento a la caché del logger
                audit_logger.add_event(
                    user_id=user_id,
                    username=username,
                    chat_type=chat_type,
                    action_type=action_type,
                    command_or_button=command_or_button,
                    callback=callback,
                    params=params
                )

                return result
            except Exception as e:
                logger.warning(f"[audit_action] Error registrando auditoría en {func.__name__}: {e}")
                return func(self, *args, **kwargs)
        return wrapper
    return decorator

class UserDataManager:
    CACHE_TTL = 300

    FAVORITE_TYPE_ORDER = {
        TransportType.METRO.value: 0,
        TransportType.BUS.value: 1,
        TransportType.TRAM.value: 2,
        TransportType.RODALIES.value: 3
    }

    def __init__(self, spreadsheet_name: str = "TMB", credentials_file: str = "credentials.json"):
        logger.info("Initializing UserDataManager...")
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)

            # Abrir spreadsheet y pestañas
            self.sheet = client.open(spreadsheet_name)
            self.users_ws = self.sheet.worksheet("users")
            self.favorites_ws = self.sheet.worksheet("favorites")
            self.searches_ws = self.sheet.worksheet("searches")
            self.alerts_ws = self.sheet.worksheet("alerts")
            self.audit_ws = self.sheet.worksheet("audit")
            self.audit_logger = AuditLogger(self.audit_ws, max_buffer_size=50)

            self.USERS_LAST_START_COLUMN_INDEX = 4
            self.USERS_USES_COLUMN_INDEX = 5
            self.USERS_LANGUAGE_INDEX = 6
            self.USERS_RECEIVE_NOTIFICATIONS_INDEX = 7
            self.USERS_ALREADY_NOTIFIED = 8

            self.SEARCHES_LAST_SEARCH_COLUMN_INDEX = 6
            self.SEARCHES_USES_COLUMN_INDEX = 7

            # Inicializar cachés
            self._users_cache = {"data": None, "timestamp": None}
            self._favorites_cache = {"data": None, "timestamp": None}
            self._searches_cache = {"data": None, "timestamp": None}
            self._alerts_cache = {"data": None, "timestamp": None}
            self._audit_cache = {"data": None, "timestamp": None}

            logger.info(f"Connected to Google Spreadsheet '{spreadsheet_name}' successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize UserDataManager: {e}")
            raise

    # ---------------------------
    # MÉTODOS DE CARGA CON CACHÉ
    # ---------------------------

    def _load_users(self, force_refresh=False):
        if not force_refresh and self._users_cache["data"] is not None:
            if datetime.now() - self._users_cache["timestamp"] < timedelta(seconds=self.CACHE_TTL):
                return self._users_cache["data"]

        users = self.users_ws.get_all_records()

        # Conversión explícita de campos booleanos conocidos
        for user in users:
            if "receive_notifications" in user:
                user["receive_notifications"] = str(user["receive_notifications"]).strip().lower() in ("true", "1", "yes", "y")

        self._users_cache = {"data": users, "timestamp": datetime.now()}
        return users

    def _load_favorites(self, force_refresh=False):
        if not force_refresh and self._favorites_cache["data"] is not None:
            if datetime.now() - self._favorites_cache["timestamp"] < timedelta(seconds=self.CACHE_TTL):
                return self._favorites_cache["data"]
        favorites = self.favorites_ws.get_all_records()
        self._favorites_cache = {"data": favorites, "timestamp": datetime.now()}
        return favorites

    def _load_searches(self, force_refresh=False):
        if not force_refresh and self._searches_cache["data"] is not None:
            if datetime.now() - self._searches_cache["timestamp"] < timedelta(seconds=self.CACHE_TTL):
                return self._searches_cache["data"]
        searches = self.searches_ws.get_all_records()
        self._searches_cache = {"data": searches, "timestamp": datetime.now()}
        return searches
    
    def _load_alerts(self, force_refresh=False):
        if not force_refresh and self._alerts_cache["data"] is not None:
            if datetime.now() - self._alerts_cache["timestamp"] < timedelta(seconds=self.CACHE_TTL):
                return self._alerts_cache["data"]
        alerts = self.alerts_ws.get_all_records()
        self._alerts_cache = {"data": alerts, "timestamp": datetime.now()}
        return alerts

    def _invalidate_favorites_cache(self):
        self._favorites_cache = {"data": None, "timestamp": None}

    # ---------------------------
    # USERS
    # ---------------------------

    def register_user(self, user_id: int, username: str):
        """Registra usuario en 'users' o incrementa usos si ya existe"""
        logger.debug(f"Registering user_id={user_id}, username={username}")
        users = self._load_users()
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                new_uses = int(user["uses"]) + 1
                self.users_ws.update_cell(idx, self.USERS_LAST_START_COLUMN_INDEX, now)
                self.users_ws.update_cell(idx, self.USERS_USES_COLUMN_INDEX, new_uses)
                self._users_cache["data"][idx - 2]["uses"] = new_uses
                return new_uses

        self.users_ws.append_row([user_id, username, now, now, 1, 'en', True, json.dumps([])])
        self._users_cache["data"].append({
            "user_id": user_id,
            "username": username,
            "last_start": now,
            "created_at": now,
            "uses": 1,
            "language": "en",
            "receive_notifications": True,
            "already_notified": json.dumps([e.__dict__ for e in []], ensure_ascii=False)
        })
        return 1

    def update_user_language(self, user_id: int, new_language: str):
        logger.debug(f"Updating language for user_id={user_id} to '{new_language}'")
        users = self._load_users()
        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                self.users_ws.update_cell(idx, self.USERS_LANGUAGE_INDEX, new_language)
                self._users_cache["data"][idx - 2]["language"] = new_language
                return True
        return False

    def get_user_language(self, user_id: int):
        logger.debug(f"Fetching language for user_id={user_id}")
        users = self._load_users()
        for user in users:
            if str(user["user_id"]) == str(user_id):
                return user["language"]
        return "en"
    
    def get_users(self) -> List[User]:
        ws_users = self._load_users()
        return [self.row_to_user(ws_user) for ws_user in ws_users]
    
    def update_notified_alerts(self, user_id, alert_id):
        logger.debug(f"Updating notified alerts for user_id={user_id} -> '{alert_id}'")
        users = self._load_users()
        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                already_notified = self.safe_str_to_list(user.get('already_notified'))
                already_notified.append(alert_id)
                self.users_ws.update_cell(idx, self.USERS_ALREADY_NOTIFIED, json.dumps(already_notified))
                self._users_cache["data"][idx - 2]["already_notified"] = already_notified
                return True
        return False
    
    def remove_deprecated_notified_alert(self, user_id, alert_id):
        logger.debug(f"Removing deprecated notified alerts for user_id={user_id} -> '{alert_id}'")
        users = self._load_users()
        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                already_notified = self.safe_str_to_list(user.get('already_notified'))
                already_notified.remove(alert_id)
                self.users_ws.update_cell(idx, self.USERS_ALREADY_NOTIFIED, json.dumps(already_notified))
                self._users_cache["data"][idx - 2]["already_notified"] = already_notified
                return True
        return False

    def get_user_receive_notifications(self, user_id) -> bool:
        logger.debug(f"Fetching receive_notifications for user_id={user_id}")
        users = self._load_users()
        for user in users:
            if str(user["user_id"]) == str(user_id):
                return user["receive_notifications"]
        return False
    
    def update_user_receive_notifications(self, user_id, value: bool):
        bool_value = value.lower() == "true" if isinstance(value, str) else value
        logger.debug(f"Updating receive_notifications for user_id={user_id} to '{value}'")
        users = self._load_users()
        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                self.users_ws.update_cell(idx, self.USERS_RECEIVE_NOTIFICATIONS_INDEX, bool_value)                
                self._users_cache["data"][idx - 2]["receive_notifications"] = bool_value
                return True
        return False
    
    def row_to_user(self, row: List[str]) -> User:
        """
        row: [
            user_id, username, initial_start, last_start, uses,
            language, receive_notifications, already_notified
        ]
        """
        return User(
            user_id=int(row.get('user_id')),
            username=row.get('username'),
            initial_start=datetime.strptime(row.get('initial_start'), "%Y:%m:%d %H:%M:%S"),
            last_start=datetime.strptime(row.get('last_start'), "%Y:%m:%d %H:%M:%S"),
            uses=int(row.get('uses')),
            language=row.get('language'),
            receive_notifications=row.get('receive_notifications'),
            already_notified=self.safe_str_to_list(row.get('already_notified'))
        )
    
    def safe_str_to_list(self, value):
    # Si ya es lista, la devolvemos tal cual
        if isinstance(value, list):
            return value
        
        # Si es None o vacío, devolvemos lista vacía
        if value in (None, "", "[]"):
            return []

        # Aseguramos que es str
        if not isinstance(value, str):
            value = str(value)

        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            # Si falla, devolvemos lista vacía como fallback
            return []

    # ---------------------------
    # FAVORITES
    # ---------------------------

    def add_favorite(self, user_id: int, type: str, item):
        """Añade una estación/parada favorita"""
        logger.debug(f"Adding favorite for user_id={user_id}, type={type}, item={item}")
        coordinates = item.get('coordinates')
        try:
            if type.lower() == TransportType.METRO.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STATION_CODE'), item.get('STATION_NAME'),
                    item.get('STATION_GROUP_CODE'), item.get('LINE_NAME'),
                    item.get('LINE_CODE'), coordinates[1], coordinates[0]
                ])
            elif type.lower() == TransportType.BUS.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STOP_CODE'), item.get('STOP_NAME'),
                    '', '', item.get('LINE_CODE'), coordinates[1], coordinates[0]
                ])
            elif type.lower() == TransportType.TRAM.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STOP_CODE'), item.get('STOP_NAME'),
                    '', item.get('LINE_NAME'), item.get('LINE_CODE'),
                    coordinates[1], coordinates[0]
                ])
            elif type.lower() == TransportType.RODALIES.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STOP_CODE'), item.get('STOP_NAME'),
                    '', item.get('LINE_NAME'), item.get('LINE_CODE'),
                    coordinates[1], coordinates[0]
                ])
            elif type.lower() == TransportType.BICING.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STATION_CODE'), item.get('STATION_NAME'),
                    '', item.get('LINE_NAME'), item.get('LINE_CODE'),
                    coordinates[1], coordinates[0]
                ])
            elif type.lower() == TransportType.FGC.value:
                self.favorites_ws.append_row([
                    user_id, type.lower(),
                    item.get('STATION_CODE'), item.get('STATION_NAME'),
                    '', item.get('LINE_NAME'), item.get('LINE_CODE'),
                    coordinates[1], coordinates[0]
                ])

            logger.info(f"Added {type} favorite for user_id={user_id}")
            self._invalidate_favorites_cache()
        except Exception as e:
            logger.error(f"Failed to add favorite for user_id={user_id}: {e}")
            raise

    def remove_favorite(self, user_id: int, type: str, item_id: str):
        """Elimina una estación/parada favorita por user_id + stop_id"""
        logger.debug(f"Removing favorite: user_id={user_id}, type={type}, item_id={item_id}")
        favorites = self._load_favorites()
        for idx, fav in enumerate(favorites, start=2):
            if str(fav["type"]) == str(type) and str(fav["code"]) == str(item_id):
                self.favorites_ws.delete_rows(idx)
                self._invalidate_favorites_cache()
                return True
        return False

    def get_favorites_by_user(self, user_id: int):
        logger.debug(f"Fetching favorites for user_id={user_id}")
        favorites = self._load_favorites()
        user_fav = [f for f in favorites if str(f["user_id"]) == str(user_id)]
    
        return sorted(
            user_fav,
            key=lambda f: self.FAVORITE_TYPE_ORDER.get(f.get("type"), 999)
        )

    def has_favorite(self, user_id, type, item_id):
        logger.debug(f"Checking if user_id={user_id} has favorite {type}:{item_id}")
        favorites = self.get_favorites_by_user(user_id)
        return any(
            f.get('type') == str(type) and str(f.get('code')) == str(item_id)
            for f in favorites
        )

    # ---------------------------
    # SEARCHES
    # ---------------------------

    def register_search(self, type: str, line: str, code: str, name: str):
        """Registra búsqueda o incrementa usos si ya existe"""
        logger.debug(f"Registering search: type={type}, line={line}, code={code}, name={name}")
        searches = self._load_searches()
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        for idx, search in enumerate(searches, start=2):
            if (str(search.get("type")) == str(type) and
                    str(search.get("code")) == str(code) and
                    str(search.get("line")) == str(line)):
                new_uses = int(search.get("searches", 0)) + 1
                self.searches_ws.update_cell(idx, self.SEARCHES_LAST_SEARCH_COLUMN_INDEX, now)
                self.searches_ws.update_cell(idx, self.SEARCHES_USES_COLUMN_INDEX, new_uses)
                self._searches_cache["data"][idx - 2]["searches"] = new_uses
                return new_uses

        self.searches_ws.append_row([type, line, code, name, now, now, 1])
        self._searches_cache["data"].append({
            "type": type,
            "line": line,
            "code": code,
            "name": name,
            "created_at": now,
            "last_search": now,
            "searches": 1
        })
        return 1
    

    # ---------------------------
    # ALERTS
    # ---------------------------

    def register_alert(self, transport_type: TransportType, api_alert: Alert):
        logger.debug(f"Registering alert: type={transport_type}, alert={api_alert}")
        ws_alerts = self._load_alerts()
        
        for idx, ws_alert in enumerate(ws_alerts, start=2):
            if str(ws_alert.get("type")) == str(transport_type.value) and str(ws_alert.get("id")) == str(api_alert.id):
                logger.debug(f"Alert already registered: type={transport_type}, alert_id={api_alert.id}")
                return False
            
        self.alerts_ws.append_row([api_alert.id, transport_type.value, api_alert.begin_date.isoformat() if api_alert.begin_date else "", api_alert.end_date.isoformat() if api_alert.end_date else "", api_alert.status, api_alert.cause, json.dumps([pub.__dict__ for pub in api_alert.publications], ensure_ascii=False), json.dumps([ent.__dict__ for ent in api_alert.affected_entities], ensure_ascii=False)])
        self._alerts_cache["data"].append({
            "id": api_alert.id,
            "transport_type": transport_type,
            "begin_date": api_alert.begin_date.isoformat() if api_alert.begin_date else "",
            "end_date": api_alert.end_date.isoformat() if api_alert.end_date else "",
            "status": api_alert.status,
            "cause": api_alert.cause,
            "publications": json.dumps([pub.__dict__ for pub in api_alert.publications], ensure_ascii=False),
            "affected_entitites": json.dumps([ent.__dict__ for ent in api_alert.affected_entities], ensure_ascii=False)
        })        

        logger.info(f"New alert registered: type={transport_type}, alert_id={api_alert.id}")
        return True
    
    def remove_alert(self, alert: Alert) -> bool:
        """
        Elimina una alerta de la hoja de cálculo y de la caché según ID y tipo de transporte.
        
        :param transport_type: Tipo de transporte de la alerta.
        :param alert_id: ID de la alerta a eliminar.
        :return: True si la alerta fue eliminada, False si no se encontró.
        """
        logger.debug(f"Removing alert: type={alert.transport_type}, alert_id={alert.id}")
        
        ws_alerts = self._load_alerts()
        
        for idx, ws_alert in enumerate(ws_alerts, start=2):  # start=2 porque la fila 1 es encabezado
            if ws_alert.get("type") and str(ws_alert.get("type")) == str(alert.transport_type.value) and str(ws_alert.get("id")) == str(alert.id):
                self.alerts_ws.delete_rows(idx)
                logger.info(f"Alert removed from spreadsheet: type={alert.transport_type}, alert_id={alert.id}")
                
                if self._alerts_cache["data"] is not None:
                    self._alerts_cache["data"] = [
                        a for a in self._alerts_cache["data"]
                        if not (str(a.get("transport_type")) == str(alert.transport_type) and str(a.get("id")) == str(alert.id))
                    ]
                return True
        
        logger.warning(f"Alert not found: type={alert.transport_type}, alert_id={alert.id}")
        return False

    
    def get_alerts(self) -> List[Alert]:
        ws_alerts = self._load_alerts()
        return [self.row_to_alert(ws_alert) for ws_alert in ws_alerts]

    def row_to_alert(self, row: Dict[str, str]) -> Alert:
        """
        Convierte una fila de Google Sheets en un objeto Alert.

        :param row: Diccionario con los datos de la fila.
        :return: Instancia de Alert.
        """
        try:
            publications = [
                Publication(**pub) for pub in json.loads(row.get("publications", "[]"))
            ]

            affected_entities = [
                AffectedEntity(**ent) for ent in json.loads(row.get("affected_entities", "[]"))
            ]

            begin_date = datetime.fromisoformat(row.get("begin_date")) if row.get("begin_date") else None
            end_date = datetime.fromisoformat(row.get("end_date")) if row.get("end_date") else None

            return Alert(
                id=row.get("id"),
                transport_type=TransportType(str(row.get('type').lower())) if row.get('type') else None,
                begin_date=begin_date,
                end_date=end_date,
                status=row.get("status") if row.get("status") else None,
                cause=row.get("cause") if row.get("cause") else None,
                publications=publications,
                affected_entities=affected_entities
            )
        except Exception as e:
            raise ValueError(f"Error parsing row into Alert: {e}")
