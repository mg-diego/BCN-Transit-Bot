import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class UserDataManager:    

    def __init__(self, spreadsheet_name: str = "TMB", credentials_file: str = "credentials.json"):
        # Autenticación con Google
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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


    # ---------------------------
    # USERS
    # user_id | username | initial_start | last_start | uses
    # ---------------------------
    def register_user(self, user_id: int, username: str):
        """Registra usuario en 'users' o incrementa usos si ya existe"""
        users = self.users_ws.get_all_records()
        now = str(datetime.now().strftime("%Y:%m:%d %H:%M:%S"))

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                # Usuario ya existe → incrementar usos
                new_uses = int(user["uses"]) + 1
                self.users_ws.update_cell(idx, self.USERS_LAST_START_COLUMN_INDEX, now)
                self.users_ws.update_cell(idx, self.USERS_USES_COLUMN_INDEX, new_uses)
                return new_uses

        # Si no existe → crear fila
        self.users_ws.append_row([user_id, username, now, now, 1, 'en'])
        return 1
    
    def update_user_language(self, user_id: int, new_language: str):
        users = self.users_ws.get_all_records()

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                self.users_ws.update_cell(idx, self.USERS_LANGUAGE_INDEX, new_language)
                return True

    def get_user_language(self, user_id: int):
        users = self.users_ws.get_all_records()

        for idx, user in enumerate(users, start=2):
            if str(user["user_id"]) == str(user_id):
                return user["language"]

    # ---------------------------
    # FAVORITES
    # user_id |	type | code | name | codi_group_estacio | nom_linia | codi_linia | latitud | longitud
    # ---------------------------
    def add_favorite(self, user_id: int, type: str, item):
        """Añade una estación/parada favorita"""

        coordinates = item.get('coordinates')
        if type.lower() == "metro":
            self.favorites_ws.append_row(
                [
                    user_id,
                    type.lower(),
                    item.get('CODI_ESTACIO'),
                    item.get('NOM_ESTACIO'),
                    item.get('CODI_GRUP_ESTACIO'),
                    item.get('NOM_LINIA'),
                    item.get('CODI_LINIA'),
                    coordinates[1],
                    coordinates[0]
                ]
            )
        elif type.lower() == "bus":
            self.favorites_ws.append_row(
                [
                    user_id,
                    type.lower(),
                    item.get('CODI_PARADA'),
                    item.get('NOM_PARADA'),
                    '',
                    '',
                    item.get('CODI_LINIA'),
                    coordinates[1],
                    coordinates[0]
                ]
            )

    def remove_favorite(self, user_id: int, type: str, item_id: str):
        """Elimina una estación/parada favorita por user_id + stop_id"""
        favorites = self.get_favorites_by_user(user_id)

        for idx, fav in enumerate(favorites, start=2):  # fila 2 porque fila 1 = headers
            if str(fav["type"]) == str(type) and str(fav["code"]) == str(item_id):
                self.favorites_ws.delete_rows(idx)
                return True
        return False

    def get_favorites_by_user(self, user_id: int):
        """Devuelve todas las favoritas de un usuario"""
        favorites = self.favorites_ws.get_all_records()
        return [f for f in favorites if str(f["user_id"]) == str(user_id)]
    
    def has_favorite(self, user_id, type, item_id):
        """
        Check if a user has a specific favorite item.

        Args:
            user_id (str | int): ID of the user.
            category (str | int): Type/category of the favorite ('metro', 'bus', etc.).
            item_id (str | int): Code/ID of the item to check.

        Returns:
            bool: True if the item is in the user's favorites, False otherwise.
        """
        favorites = self.get_favorites_by_user(user_id)
        return any(f.get('type') == str(type) and str(f.get('code')) == str(item_id) for f in favorites)
    

    # ---------------------------
    # SEARCHES
    # type | line | code | name | initial_search | last_search | searches
    # ---------------------------
    def register_search(self, type: str, line: str, code: str, name: str):
        """Registra búsqueda o incrementa usos si ya existe"""
        searches = self.searches_ws.get_all_records()
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        # Buscar coincidencia exacta
        for idx, search in enumerate(searches, start=2):  # fila 2 = primera fila de datos
            if (str(search.get("type")) == str(type) and
                str(search.get("code")) == str(code) and
                str(search.get("line")) == str(line)):
                # Existe → incrementar
                new_uses = int(search.get("searches", 0)) + 1
                self.searches_ws.update_cell(idx, self.SEARCHES_LAST_SEARCH_COLUMN_INDEX, now)
                self.searches_ws.update_cell(idx, self.SEARCHES_USES_COLUMN_INDEX, new_uses)
                return new_uses

        # No existe → añadir fila nueva
        self.searches_ws.append_row([type, line, code, name, now, now, 1])
        return 1