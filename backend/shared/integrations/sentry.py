import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from shared.config.config import get_settings
from shared.logging.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def init_sentry():
    """Initialize Sentry with proper error handling."""

    if not settings.SENTRY.DSN or str(settings.SENTRY.DSN) == "http://127.0.0.1":
        logger.warning("Sentry DSN not configured, skipping initialization")
        return

    try:
        sentry_sdk.init(
            dsn=str(settings.SENTRY.DSN),
            environment=settings.APP.ENV,
            release=f"{settings.APP.NAME}@{settings.APP.VERSION}",
            integrations=[
                StarletteIntegration(transaction_style="url"),
                FastApiIntegration(transaction_style="url"),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            # Performance
            traces_sample_rate=1.0 if settings.APP.ENV == "local" else 0.1,
            profiles_sample_rate=1.0 if settings.APP.ENV == "local" else 0.1,
            # Privacy
            send_default_pii=True,
            # Error filtering
            ignore_errors=[
                KeyboardInterrupt,
                "ConnectionResetError",
            ],
        )
        logger.info(f"Sentry initialized for {settings.APP.ENV} environment")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
