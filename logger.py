import logging

# Самая простая настройка
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s %(module)s:%(lineno)d(def %(funcName)s) %(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)
