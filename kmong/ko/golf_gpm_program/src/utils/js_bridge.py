import os

_injected_scripts = set()

def _get_js_path(js_file: str) -> str:
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "js", js_file)

def inject_js_once(driver, js_file: str):
    """JS 파일을 한 번만 주입"""
    if js_file in _injected_scripts:
        return
    with open(_get_js_path(js_file), encoding="utf-8") as f:
        js = f.read()
        driver.execute_script(js)
    _injected_scripts.add(js_file)

def call_js(driver, func_name: str, js_file: str):
    """JS 주입 후 함수 호출"""
    inject_js_once(driver, js_file)
    return driver.execute_script(f"return {func_name}();")
