from domain.transport_type import TransportType
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from providers.helpers import logger


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

            self.USERS_LAST_START_COLUMN_INDEX = 4
            self.USERS_USES_COLUMN_INDEX = 5
            self.USERS_LANGUAGE_INDEX = 6

            self.SEARCHES_LAST_SEARCH_COLUMN_INDEX = 6
            self.SEARCHES_USES_COLUMN_INDEX = 7

            # Inicializar cachés
            self._users_cache = {"data": None, "timestamp": None}
            self._favorites_cache = {"data": None, "timestamp": None}
            self._searches_cache = {"data": None, "timestamp": None}

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

        self.users_ws.append_row([user_id, username, now, now, 1, 'en'])
        self._users_cache["data"].append({
            "user_id": user_id,
            "username": username,
            "last_start": now,
            "created_at": now,
            "uses": 1,
            "language": "en"
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