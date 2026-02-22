# -*- coding: utf-8 -*-
"""Padrões mínimos de observabilidade estruturada para eventos de domínio."""

from __future__ import annotations

from typing import Any

from utils.structured_logger import StructuredLogger


class Events:
    SYNC_STARTED = "sync_started"
    SYNC_SUCCEEDED = "sync_succeeded"
    SYNC_FAILED = "sync_failed"
    PROFILE_SAVED = "profile_saved"


def emit_event(
    logger: StructuredLogger,
    event: str,
    level: str = "info",
    **context: Any,
) -> None:
    """Emite evento estruturado com chave padrão `event`."""
    logger.log(level, event, event=event, **context)
