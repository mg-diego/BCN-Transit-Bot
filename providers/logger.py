# logger.py
import logging
import sys

# Configuración global del logger
logger = logging.getLogger("my_bot")
logger.setLevel(logging.INFO)  # Nivel global: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Formato de salida
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Handler a consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Evitar que se propaguen logs duplicados a root logger
logger.propagate = False
