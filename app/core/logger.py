import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):

    def filter(self, record):

        record.request_id = get_request_id()

        return True


LOG_DIRECTORY = Path("logs")
LOG_DIRECTORY.mkdir(exist_ok=True)

LOG_FILE = LOG_DIRECTORY / "rag_chatbot.log"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "[%(request_id)s] | "
    "%(message)s"
)

formatter = logging.Formatter(LOG_FORMAT)

logger = logging.getLogger("rag-chatbot")

logger.setLevel(logging.INFO)

logger.propagate = False

request_filter = RequestIdFilter()

if not logger.handlers:

    console = logging.StreamHandler()

    console.setFormatter(formatter)

    console.addFilter(request_filter)

    file = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )

    file.setFormatter(formatter)

    file.addFilter(request_filter)

    logger.addHandler(console)

    logger.addHandler(file)