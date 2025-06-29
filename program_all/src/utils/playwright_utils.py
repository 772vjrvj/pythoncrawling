import asyncio
import os
import psutil
import traceback
import requests
from pathlib import Path
from playwright.async_api import async_playwright


class PlaywrightUtils:
    def __init__(self, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session = requests.Session()
        self.headless = headless
        self.auth_state_path = "auth_state.json"

    async def _launch_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-http2",  # ✅ HTTP/2 비활성화
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )

    async def set_browser(self):
        try:
            await self._launch_browser()

            # ✅ 로그인 상태 재사용 여부 확인
            if Path(self.auth_state_path).exists():
                self.context = await self.browser.new_context(
                    storage_state=self.auth_state_path,
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36"
                    ),
                    locale="ko-KR"
                )
            else:
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36"
                    ),
                    locale="ko-KR"
                )

            self.page = await self.context.new_page()

            await self._bypass_bot_detection()

        except Exception as e:
            print(f"❌ Browser launch failed: {e}")
            traceback.print_exc()

    async def set_browser_with_user_profile(self):
        try:
            self._close_chrome_processes()
            await self._launch_browser()

            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/114.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="ko-KR"
            )

            self.page = await self.context.new_page()
            await self._bypass_bot_detection()
        except Exception as e:
            print(f"❌ User profile launch failed: {e}")
            traceback.print_exc()

    async def _bypass_bot_detection(self):
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

    def _close_chrome_processes(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    async def save_storage_state(self):
        """로그인 후 상태 저장"""
        if self.context:
            await self.context.storage_state(path=self.auth_state_path)
            print(f"✅ 로그인 상태 저장됨: {self.auth_state_path}")

    def reset_auth_state(self):
        """로그인 상태 초기화"""
        if Path(self.auth_state_path).exists():
            os.remove(self.auth_state_path)
            print("🔄 로그인 상태 초기화 완료")

    async def start_browser(self, use_user_profile=False):
        if use_user_profile:
            await self.set_browser_with_user_profile()
        else:
            await self.set_browser()
        return self.page

    def get_session(self):
        return self.session

    async def quit(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
