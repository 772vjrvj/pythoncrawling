import time
import asyncio
from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal
import os
from src.core.global_state import GlobalState
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from playwright.async_api import async_playwright


class QThreadABCMeta(type(QThread), ABCMeta):
    pass


class BaseApiWorkerSec(QThread, metaclass=QThreadABCMeta):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float, float)
    progress_end_signal = pyqtSignal()
    msg_signal = pyqtSignal(str, str, object)

    def __init__(self, headless=False):
        super().__init__()
        self.file_driver = None
        self.excel_driver = None
        self.running = True

        self.page = None
        self.context = None
        self.browser = None
        self.base_url = None
        self.before_pro_value = 0
        self.headless = headless

        self.playwright = None

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        try:
            await self.base_init()
            await self.main()
        except Exception as e:
            self.log_func(f"❌ 예외 발생: {e}")
        finally:
            await self.base_end()

    async def base_init(self):
        self.log_func("크롤링 시작 ========================================")

        self.excel_driver = ExcelUtils(self.log_func)
        self.file_driver = FileUtils(self.log_func)

        state = GlobalState()
        user = state.get("user")

        self.log_func("👉 실제 브라우저 프로필을 재사용하여 쿠팡 우회 중...")

        # ✅ Chrome 프로필 경로
        chrome_profile_path = os.path.join(
            f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data", "Default"
        )
        if not os.path.exists(chrome_profile_path):
            raise FileNotFoundError(f"❌ Chrome 프로필 경로 없음: {chrome_profile_path}")

        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=chrome_profile_path,
            headless=self.headless,
            executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",  # ✅ 실제 크롬
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
            locale="ko-KR",
            viewport={"width": 1200, "height": 900},
            ignore_https_errors=True,
        )

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

        # 기본 URL 진입이 필요하다면 init 쪽에서
        await self.init()

    async def base_end(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_func("=============== 크롤링 종료중...")
        await asyncio.sleep(3)
        self.log_func("=============== 크롤링 종료")

        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

        self.progress_end_signal.emit()

    def log_func(self, msg):
        self.log_signal.emit(msg)

    def stop(self):
        self.running = False
        asyncio.create_task(self._safe_close())

    async def _safe_close(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    async def main(self):
        pass
