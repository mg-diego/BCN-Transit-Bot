import logging

# Configuración global del logger
logger = logging.getLogger("BCN-Transit-Bot")
logger.setLevel(logging.INFO)  # Nivel global: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Formato de salida
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s] - %(message)s"
)

# Handler de consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Handler de fichero
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Evitar que se propaguen logs duplicados a root logger
logger.propagate = False
