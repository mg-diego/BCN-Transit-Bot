from domain.transport_type import TransportType
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from providers.helpers import logger


class UserDataManager:    

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

            logger.info(f"Connected to Google Spreadsheet '{spreadsheet_name}' successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize UserDataManager: {e}")
            raise

    # ---------------------------
    # USERS
    # ---------------------------
    def register_user(self, user_id: int, username: str):
        """Registra usuario en 'users' o incrementa usos si ya existe"""
        logger.debug(f"Registering user_id={user_id}, username={username}")
        users = self.users_ws.get_all_records()
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                new_uses = int(user["uses"]) + 1
                self.users_ws.update_cell(idx, self.USERS_LAST_START_COLUMN_INDEX, now)
                self.users_ws.update_cell(idx, self.USERS_USES_COLUMN_INDEX, new_uses)
                logger.info(f"Updated user {user_id}: uses={new_uses}")
                return new_uses

        self.users_ws.append_row([user_id, username, now, now, 1, 'en'])
        logger.info(f"New user registered: {user_id} ({username})")
        return 1
    
    def update_user_language(self, user_id: int, new_language: str):
        logger.debug(f"Updating language for user_id={user_id} to '{new_language}'")
        users = self.users_ws.get_all_records()

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                self.users_ws.update_cell(idx, self.USERS_LANGUAGE_INDEX, new_language)
                logger.info(f"User {user_id} language updated to '{new_language}'")
                return True
        logger.warning(f"Tried to update language for unknown user_id={user_id}")
        return False

    def get_user_language(self, user_id: int):
        logger.debug(f"Fetching language for user_id={user_id}")
        users = self.users_ws.get_all_records()

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                language = user["language"]
                logger.debug(f"User {user_id} language is '{language}'")
                return language

        logger.debug(f"User {user_id} not found, returning default 'en'")
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
                    user_id,
                    type.lower(),
                    item.get('STATION_CODE'),
                    item.get('STATION_NAME'),
                    item.get('STATION_GROUP_CODE'),
                    item.get('LINE_NAME'),
                    item.get('LINE_CODE'),
                    coordinates[1],
                    coordinates[0]
                ])
            elif type.lower() == TransportType.BUS.value:
                self.favorites_ws.append_row([
                    user_id,
                    type.lower(),
                    item.get('STOP_CODE'),
                    item.get('STOP_NAME'),
                    '',
                    '',
                    item.get('LINE_CODE'),
                    coordinates[1],
                    coordinates[0]
                ])
            elif type.lower() == TransportType.TRAM.value:
                self.favorites_ws.append_row([
                    user_id,
                    type.lower(),
                    item.get('STOP_CODE'),
                    item.get('STOP_NAME'),
                    '',
                    item.get('LINE_NAME'),
                    item.get('LINE_CODE'),
                    coordinates[1],
                    coordinates[0]
                ])
            logger.info(f"Added {type} favorite for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to add favorite for user_id={user_id}: {e}")
            raise

    def remove_favorite(self, user_id: int, type: str, item_id: str):
        """Elimina una estación/parada favorita por user_id + stop_id"""
        logger.debug(f"Removing favorite: user_id={user_id}, type={type}, item_id={item_id}")
        favorites = self.get_favorites_by_user(user_id)

        for idx, fav in enumerate(favorites, start=2):  # fila 2 porque fila 1 = headers
            if str(fav["type"]) == str(type) and str(fav["code"]) == str(item_id):
                self.favorites_ws.delete_rows(idx)
                logger.info(f"Favorite removed: user_id={user_id}, type={type}, item_id={item_id}")
                return True

        logger.warning(f"Favorite not found: user_id={user_id}, type={type}, item_id={item_id}")
        return False

    def get_favorites_by_user(self, user_id: int):
        logger.debug(f"Fetching favorites for user_id={user_id}")
        favorites = self.favorites_ws.get_all_records()
        filtered = [f for f in favorites if str(f["user_id"]) == str(user_id)]
        logger.debug(f"Found {len(filtered)} favorites for user_id={user_id}: \n {filtered}")
        return filtered
    
    def has_favorite(self, user_id, type, item_id):
        logger.debug(f"Checking if user_id={user_id} has favorite {type}:{item_id}")
        favorites = self.get_favorites_by_user(user_id)
        result = any(
            f.get('type') == str(type) and str(f.get('code')) == str(item_id)
            for f in favorites
        )
        logger.debug(f"User {user_id} has_favorite={result}")
        return result

    # ---------------------------
    # SEARCHES
    # ---------------------------
    def register_search(self, type: str, line: str, code: str, name: str):
        """Registra búsqueda o incrementa usos si ya existe"""
        logger.debug(f"Registering search: type={type}, line={line}, code={code}, name={name}")
        searches = self.searches_ws.get_all_records()
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        for idx, search in enumerate(searches, start=2):  # fila 2 = primera fila de datos
            if (str(search.get("type")) == str(type) and
                str(search.get("code")) == str(code) and
                str(search.get("line")) == str(line)):
                new_uses = int(search.get("searches", 0)) + 1
                self.searches_ws.update_cell(idx, self.SEARCHES_LAST_SEARCH_COLUMN_INDEX, now)
                self.searches_ws.update_cell(idx, self.SEARCHES_USES_COLUMN_INDEX, new_uses)
                logger.info(f"Search updated: type={type}, line={line}, code={code}, uses={new_uses}")
                return new_uses

        self.searches_ws.append_row([type, line, code, name, now, now, 1])
        logger.info(f"New search registered: type={type}, line={line}, code={code}")
        return 1
