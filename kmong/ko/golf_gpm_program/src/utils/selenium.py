import os
import ssl
import sys

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumDriverManager:

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # ✅ 디스크 캐시 비활성화
        chrome_options.add_argument('--disk-cache-size=0')
        chrome_options.add_argument('--disable-application-cache')
        chrome_options.add_argument('--media-cache-size=0')

        # ✅ HTTP 캐시 무력화 헤더
        header_overrides = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }

        # PyInstaller 환경 대응
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        cert_dir = os.path.join(base_path, 'seleniumwire')
        cert_path = os.path.join(cert_dir, 'ca.crt')
        key_path = os.path.join(cert_dir, 'ca.key')

        seleniumwire_options = {
            'disable_encoding': True,
            'verify_ssl': True,
            'intercept': True,
            'ca_cert': cert_path,
            'ca_key': key_path,
            'capture_headers': True,
            'ignore_http_methods': ['OPTIONS'],
            'exclude_hosts': [
                'gstatic.com', 'google.com', 'googletagmanager.com', 'gvt1.com',
                'polyfill-fastly.io', 'fonts.googleapis.com', 'fonts.gstatic.com',
                'bizmall.golfzon.com', 'uf.gzcdn.net', 'i.gzcdn.net'
            ],
            'request_storage_base_dir': None,  # 메모리 캐시 사용 시 필요
        }

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )

        # ✅ 캐시 무력화를 위한 헤더 설정
        driver.header_overrides = header_overrides

        # ✅ 탐지 회피용 JS 삽입
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })

        return driver
