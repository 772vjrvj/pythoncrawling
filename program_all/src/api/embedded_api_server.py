# -*- coding: utf-8 -*-
"""
Run FastAPI inside current process with uvicorn on a background thread.
"""
import threading
from typing import Optional
import uvicorn
import asyncio

class EmbeddedApiServer:
    def __init__(self, app, host: str = "0.0.0.0", port: int = 8088, log_level: str = "info"):
        self._app = app
        self._host = host
        self._port = port
        self._log_level = log_level
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        def _run():
            asyncio.set_event_loop(asyncio.new_event_loop())
            config = uvicorn.Config(
                app=self._app,
                host=self._host,
                port=self._port,
                log_level=self._log_level,
                loop="asyncio",
                lifespan="on",
            )
            self._server = uvicorn.Server(config)
            asyncio.get_event_loop().run_until_complete(self._server.serve())
        self._thread = threading.Thread(target=_run, name="EmbeddedApiThread", daemon=True)
        self._thread.start()

    def stop(self, join_timeout: float = 5.0):
        if self._server:
            self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=join_timeout)
