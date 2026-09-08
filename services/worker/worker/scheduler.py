"""Periodic sync runner. Starts one sync immediately, then repeats on configured interval."""
import logging
import time

from .config import settings
from .sync import sync


def run() -> None:
    interval = max(settings.sync_interval_hours, 1) * 3600
    while True:
        try:
            sync()
        except Exception:
            logging.getLogger("elteh.scheduler").exception("scheduled sync failed")
        time.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
    run()
