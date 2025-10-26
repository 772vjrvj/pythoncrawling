# -*- coding: utf-8 -*-
"""
Run FastAPI inside current process with uvicorn on a background thread.
- uvicorn 기본 포맷터(uvicorn.logging.DefaultFormatter) 미사용
- 표준 logging.Formatter 기반 커스텀 log_config 적용 → 빌드 환경에서도 안전
- 시작 실패(포트/권한/모듈) 즉시 예외로 표면화
- 서브스레드 시그널 핸들러 무력화(Windows 호환)
"""
import threading
from typing import Optional
import uvicorn
import asyncio
import logging


class EmbeddedApiServer:
    def __init__(self, app, host: str = "127.0.0.1", port: int = 8088,
                 log_level: str = "info", log_func=None):
        self._app = app
        self._host = host
        self._port = port
        self._log_level = log_level
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self._log_func = log_func

        self._started_evt = threading.Event()
        self._error: Optional[BaseException] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def _basic_log_config(self):
        lvl = self._log_level.upper()
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                # uvicorn 계열 로거만 심플 핸들러로 고정
                "uvicorn":        {"handlers": ["console"], "level": lvl, "propagate": False},
                "uvicorn.error":  {"handlers": ["console"], "level": lvl, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": lvl, "propagate": False},
            },
            "root": {"level": lvl, "handlers": ["console"]},
        }

    def start(self, timeout: float = 3.0):
        if self._thread and self._thread.is_alive():
            return

        def _run():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

                config = uvicorn.Config(
                    app=self._app,
                    host=self._host,
                    port=self._port,
                    log_level=self._log_level,
                    loop="asyncio",
                    lifespan="on",
                    # ★ uvicorn 기본 로깅 대신 안전한 커스텀 로깅 설정 적용
                    log_config=self._basic_log_config(),
                )
                self._server = uvicorn.Server(config)

                # 서브스레드에서 시그널 핸들러 설치 금지
                try:
                    self._server.install_signal_handlers = lambda: None
                except Exception:
                    pass

                if self._log_func:
                    self._log_func(f"[EmbeddedApiServer] starting → {self.url}")

                # 시작 플래그 올리고 serve 실행
                self._started_evt.set()
                self._loop.run_until_complete(self._server.serve())

            except BaseException as e:
                self._error = e
                self._started_evt.set()
                if self._log_func:
                    self._log_func(f"[EmbeddedApiServer] start error: {e!r}")

        self._thread = threading.Thread(target=_run, name="EmbeddedApiThread", daemon=True)
        self._thread.start()

        # 시작 대기 후 실패 시 예외
        if not self._started_evt.wait(timeout=timeout):
            raise RuntimeError("Uvicorn did not start within timeout.")
        if self._error:
            raise RuntimeError(f"Uvicorn start failed: {self._error}")

    def stop(self, join_timeout: float = 5.0):
        try:
            if self._server:
                self._server.should_exit = True
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(lambda: None)
        finally:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=join_timeout)
