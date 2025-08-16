from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class SecretsManager:
    def __init__(self):
        """
        Inicializa el gestor de secretos leyendo el archivo dado.
        :param filepath: Ruta al archivo 'secrets'.
        """
        self.secrets = {}
        self._load_env()
        self._load_file('secrets')        

        logger.info(self.secrets)
        
    def _load_env(self):
        self.secrets['TELEGRAM_TOKEN'] = os.environ.get('TELEGRAM_TOKEN')
        self.secrets['APP_ID'] = os.environ.get('APP_ID')
        self.secrets['APP_KEY'] = os.environ.get('APP_KEY')

    def _load_file(self, filepath: str):
        path = Path(filepath)
        if not path.is_file():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                self.secrets[key.strip()] = value.strip()

    def get(self, key: str, default=None):
        """
        Obtiene el valor de una clave. Devuelve 'default' si no existe.
        """
        return self.secrets.get(key, default)

    def __getitem__(self, key: str):
        """
        Permite acceder con sintaxis tipo diccionario: secrets["KEY"]
        """
        return self.get(key)
