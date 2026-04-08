"""Async event bus for research progress tracking and SSE streaming."""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from collections.abc import AsyncIterator

from deep_research.schemas.events import ResearchEvent


class EventEmitter:
    """Fan-out event emitter: each research_id can have multiple subscribers."""

    def __init__(self) -> None:
        self._queues: dict[uuid.UUID, list[asyncio.Queue[ResearchEvent | None]]] = defaultdict(
            list
        )

    async def emit(self, event: ResearchEvent) -> None:
        for queue in self._queues.get(event.research_id, []):
            await queue.put(event)

    async def subscribe(self, research_id: uuid.UUID) -> AsyncIterator[ResearchEvent]:
        queue: asyncio.Queue[ResearchEvent | None] = asyncio.Queue()
        self._queues[research_id].append(queue)
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            self._queues[research_id].remove(queue)
            if not self._queues[research_id]:
                del self._queues[research_id]

    async def close(self, research_id: uuid.UUID) -> None:
        for queue in self._queues.get(research_id, []):
            await queue.put(None)


# Singleton for the application
_emitter: EventEmitter | None = None


def get_event_emitter() -> EventEmitter:
    global _emitter  # noqa: PLW0603
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter
