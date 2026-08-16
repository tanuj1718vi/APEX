"""
In-process event bus.

RuntimeEngine executes synchronously inside a background thread
(started via asyncio.to_thread from the FastAPI route), but the
WebSocket consumer lives on the asyncio event loop. This bus bridges
the two safely: publish() is called from the worker thread and uses
loop.call_soon_threadsafe to push onto an asyncio.Queue that the
WebSocket handler reads from.

Each execution gets its own queue so multiple executions can stream
concurrently without cross-talk.
"""

import asyncio
from typing import Dict, Any, Optional


class EventBus:
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queues: Dict[str, "asyncio.Queue"] = {}

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Call once, from the running FastAPI event loop."""
        self._loop = loop

    def create_queue(self, execution_id: str) -> "asyncio.Queue":
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[execution_id] = queue
        return queue

    def get_queue(self, execution_id: str) -> Optional["asyncio.Queue"]:
        return self._queues.get(execution_id)

    def drop_queue(self, execution_id: str) -> None:
        self._queues.pop(execution_id, None)

    def publish(self, execution_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Thread-safe. Safe to call even if there's no active queue or
        loop yet (e.g. very first event of a run) -- it's just a
        no-op in that case, since REST polling (GET /executions/{id})
        remains the source of truth regardless.
        """
        queue = self._queues.get(execution_id)
        if queue is None or self._loop is None:
            return

        message = {"event_type": event_type, "payload": payload}

        def _put():
            queue.put_nowait(message)

        try:
            self._loop.call_soon_threadsafe(_put)
        except RuntimeError:
            # Loop already closed (e.g. during shutdown/tests).
            pass


# Single shared bus for the whole process -- executions are
# distinguished by execution_id, not by bus instance.
event_bus = EventBus()
