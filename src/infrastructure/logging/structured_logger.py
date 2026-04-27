import logging
import sys
import structlog
from src.application.interfaces.logger import ILogger


class StructuredLogger(ILogger):
    """
    Logger estructurado en JSON. Ideal para observabilidad
    (Loki, Datadog, ELK). Implementa la interfaz ILogger
    del dominio para no acoplar los use-cases a structlog.
    """

    def __init__(self, level: str = "INFO") -> None:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, level)
            ),
            cache_logger_on_first_use=True,
        )
        self._log = structlog.get_logger()

    def info(self, event: str, **kwargs) -> None:
        self._log.info(event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        self._log.warning(event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        self._log.error(event, **kwargs)

    def debug(self, event: str, **kwargs) -> None:
        self._log.debug(event, **kwargs)