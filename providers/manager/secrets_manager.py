from pathlib import Path
import os
from providers.helpers import logger


class SecretsManager:
    def __init__(self):
        """
        Inicializa el gestor de secretos leyendo las variables de entorno y el archivo de secretos.
        """
        logger.info("[SecretsManager] Initializing...")
        self.secrets = {}
        self._load_env()
        self._load_file('secrets')
        logger.info("[SecretsManager] Initialization complete.")

    def _load_env(self):
        """
        Carga secretos desde variables de entorno.
        """
        logger.info("[SecretsManager] Loading secrets from environment variables...")
        keys = [
            'TELEGRAM_TOKEN',
            'TELEGRAPH_TOKEN',
            'TMB_APP_ID',
            'TMB_APP_KEY',
            'TRAM_CLIENT_ID',
            'TRAM_CLIENT_SECRET',
            'ADMIN_ID',
            'DATABASE_URL',
        ]
        for key in keys:
            value = os.environ.get(key)
            if value:
                self.secrets[key] = value
                logger.debug(f"[SecretsManager] Loaded secret from env: {key}")
            else:
                logger.warning(f"[SecretsManager] Environment variable '{key}' not found.")

    def _load_file(self, filepath: str):
        """
        Carga secretos desde un archivo de texto con formato KEY=VALUE.
        """
        path = Path(filepath)
        if not path.is_file():
            logger.warning(f"[SecretsManager] Secrets file '{filepath}' not found. Skipping file-based secrets.")
            return

        logger.info(f"[SecretsManager] Loading secrets from file '{filepath}'...")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                self.secrets[key.strip()] = value.strip()
                logger.debug(f"[SecretsManager] Loaded secret from file: {key.strip()}")

        logger.info(f"[SecretsManager] Finished loading secrets from '{filepath}'.")

    def get(self, key: str, default=None):
        """
        Obtiene el valor de una clave. Devuelve 'default' si no existe.
        """
        value = self.secrets.get(key, default)
        if value is default:
            logger.warning(f"[SecretsManager] Secret '{key}' not found. Returning default value.")
        else:
            logger.debug(f"[SecretsManager] Secret '{key}' retrieved successfully.")
        return value

    def __getitem__(self, key: str):
        """
        Permite acceder con sintaxis tipo diccionario: secrets["KEY"]
        """
        return self.get(key)
