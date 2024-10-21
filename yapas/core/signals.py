import asyncio

from logging import getLogger

logger = getLogger(__name__)

kill_event = asyncio.Event()


async def handle_shutdown(signal_name, server_obj):
    """Signal handler for graceful shutdown."""
    logger.info(f"Received {signal_name}, shutting down...")
    await asyncio.shield(server_obj.shutdown())
    kill_event.set()


async def handle_restart(server_obj):
    """Signal handler for server restart."""
    await server_obj._start()
