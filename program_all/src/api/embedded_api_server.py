# -*- coding: utf-8 -*-
"""
Run FastAPI inside current process with uvicorn on a background thread.
- 외부 log_func으로 uvicorn 로그를 전달 (별도 핸들러 클래스 정의 없이 간단 주입)
"""
import threading
from typing import Optional
import uvicorn
import asyncio
import logging


class EmbeddedApiServer:
    def __init__(self, app, host: str = "127.0.0.1", port: int = 8088, log_level: str = "info", log_func=None):
        self._app = app
        self._host = host
        self._port = port
        self._log_level = log_level
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self._log_func = log_func  # 외부(UI) 로그 함수

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

            # uvicorn 로그를 외부 log_func으로 포워딩
            if self._log_func:
                handler = logging.StreamHandler()
                handler.emit = lambda record: self._log_func(record.getMessage())
                for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
                    lg = logging.getLogger(name)
                    lg.handlers = [handler]
                    lg.setLevel(self._log_level.upper())
                    lg.propagate = False

                self._log_func(f"[EmbeddedApiServer] starting → http://{self._host}:{self._port}")

            asyncio.get_event_loop().run_until_complete(self._server.serve())

        self._thread = threading.Thread(target=_run, name="EmbeddedApiThread", daemon=True)
        self._thread.start()

    def stop(self, join_timeout: float = 5.0):
        if self._server:
            self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=join_timeout)
