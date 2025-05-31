from src.utils.js_bridge import call_js, inject_js_once


class JSContext:
    def __init__(self, driver):
        self.driver = driver

    def call(self, func_name, js_file):
        return call_js(self.driver, func_name, js_file)

    def inject_only(self, js_file):
        inject_js_once(self.driver, js_file)