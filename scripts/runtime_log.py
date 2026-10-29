"""Local, rotating diagnostics for runtime stages (never transcript content)."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_runtime_logger():
    logger = logging.getLogger("jarvis.runtime")
    if not logger.handlers:
        root = Path(
            os.environ.get("JARVIS_BASE_PATH", Path(__file__).resolve().parent.parent)
        )
        try:
            log_dir = root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                log_dir / "runtime.log", maxBytes=1_000_000, backupCount=2,
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            )
        except OSError as error:
            print(f"[RuntimeLog] File logging unavailable: {error}")
            handler = logging.NullHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
