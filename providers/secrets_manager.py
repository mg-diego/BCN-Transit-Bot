from pathlib import Path

class SecretsManager:
    def __init__(self):
        """
        Inicializa el gestor de secretos leyendo el archivo dado.
        :param filepath: Ruta al archivo 'secrets'.
        """
        self.secrets = {}
        self._load('secrets')

    def _load(self, filepath: str):
        """
        Lee el archivo y guarda las claves/valores en memoria.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Secrets file not found: {filepath}")

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
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
