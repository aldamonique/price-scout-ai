import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ThreadPoolJobRunner:
    def __init__(self, max_workers: int) -> None:
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="shopping-request"
        )

    def submit(self, job: Callable[[], None]) -> None:
        self._pool.submit(self._run_safely, job)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=True, cancel_futures=True)

    @staticmethod
    def _run_safely(job: Callable[[], None]) -> None:
        try:
            job()
        except Exception:
            logger.exception("background job failed")
