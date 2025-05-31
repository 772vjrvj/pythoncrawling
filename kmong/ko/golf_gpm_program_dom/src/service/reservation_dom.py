from src.utils.log import log
from src.utils.js_loader import load_js

class JSFn:
    GET_BOOKING_DATA = "getBookingData"
    GET_USER_NAME = "getUserName"
    GET_POPUP_STATUS = "getPopupStatus"
    # 필요 시 여기에 계속 추가


class DomReservationExtractor:
    def __init__(self, driver):
        self.driver = driver

    def inject_observer(self):
        try:
            script = load_js("observe_booking_popup.js")
            self.driver.execute_script(script)
            log("[DOM] MutationObserver JS 주입 완료")
        except Exception as e:
            log(f"[DOM] JS 주입 실패: {e}")

    def js_fn(self, fn_name: str):
        try:
            return self.driver.execute_script(f"return {fn_name}();")
        except Exception as e:
            log(f"[DOM] JS 함수 호출 실패 ({fn_name}): {e}")
            return None
