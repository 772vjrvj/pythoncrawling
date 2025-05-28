import os

def load_js(filename: str) -> str:
    base_path = os.path.dirname(os.path.dirname(__file__))
    js_path = os.path.join(base_path, "js", filename)
    with open(js_path, "r", encoding="utf-8") as f:
        return f.read()
