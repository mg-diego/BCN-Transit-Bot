import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Crear la carpeta /logs si no existe
log_dir = './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configuración global del logger
logger = logging.getLogger("BCN-Transit-Bot")
logger.setLevel(logging.DEBUG)  # Nivel global: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Formato de salida
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s] - %(message)s"
)

# Handler de consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Handler de fichero con rotación diaria
file_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, "app.log"),
    when="midnight",  # Rotar a medianoche
    interval=1,  # Cada día
    backupCount=30,  # Mantener logs de los últimos 30 días
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Evitar que se propaguen logs duplicados a root logger
logger.propagate = False
