import os
import ssl
import sys

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from src.utils.log import log

ssl._create_default_https_context = ssl._create_unverified_context

class SeleniumDriverManager:

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # PyInstaller 환경을 고려한 인증서 경로 설정
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        cert_dir = os.path.join(base_path, 'seleniumwire')
        cert_path = os.path.join(cert_dir, 'ca.crt')
        key_path = os.path.join(cert_dir, 'ca.key')

        log(f"cert_path: {cert_path}")
        log(f"key_path: {key_path}")

        seleniumwire_options = {
            'disable_encoding': True,
            'verify_ssl': True,
            'intercept': True,  # 후킹 활성화
            'ca_cert': cert_path,
            'ca_key': key_path,
            'exclude_hosts': [
                'gstatic.com', 'google.com', 'googletagmanager.com', 'gvt1.com',
                'polyfill-fastly.io', 'fonts.googleapis.com', 'fonts.gstatic.com',
                'bizmall.golfzon.com', 'uf.gzcdn.net', 'https://i.gzcdn.net'
            ]
        }

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })

        return driver