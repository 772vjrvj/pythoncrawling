import logging
import os
import sys
import time

try:
    from mitmproxy import ctx
    MITM_AVAILABLE = True
except ImportError:
    ctx = None
    MITM_AVAILABLE = False

_pando_logger = None

def get_executable_dir():
    """
    운영 vs 개발 경로 반환
    - 배포(Packed with PyInstaller): sys.frozen == True -> 실행파일이 있는 폴더
    - 개발(소스 실행): 현재 파일(__file__) 기준으로 프로젝트 루트(상위 2단계)
    # __file__을 절대경로화하고, PyInstaller의 임시 폴더(sys._MEIPASS)를 고려함
    """
    # PyInstaller에서 리소스가 풀리는 임시 폴더 체크
    if getattr(sys, "frozen", False):
        # PyInstaller로 묶였을 때의 실행 파일 경로
        # sys._MEIPASS는 PyInstaller가 리소스를 푸는 임시 경로(존재하면 사용)
        base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
        return os.path.abspath(base)
    else:
        # __file__을 절대경로로 정리해서 상위 2단계로 이동
        # (프로젝트 구조에 따라 조정 필요)
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

def init_pando_logger():
    """
    전역 로거 초기화
    - 여러 번 호출되어도 핸들러 중복 추가되지 않게 보호
    - 로그 폴더 없으면 생성
    - 오래된 로그 정리 수행
    """
    global _pando_logger

    logs_dir = os.path.join(get_executable_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # 오래된 로그 삭제 (예외 안전성 추가)
    clean_old_logs(logs_dir, prefix="pando", days=7)
    clean_old_logs(logs_dir, prefix="proxy_server", days=1)


    # 이미 초기화된 로거가 있으면 중복 핸들러 추가 안함
    if _pando_logger is not None:
        if _pando_logger.handlers:
            # 이미 초기화되어 있음 -> 아무 작업 안함
            return

    _pando_logger = logging.getLogger("pando")
    _pando_logger.setLevel(logging.INFO)

    log_path = os.path.join(logs_dir, "pando.log")

    # FileHandler 대신 필요하면 RotatingFileHandler로 교체 가능
    handler = logging.FileHandler(log_path, encoding="utf-8")

    fmt = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    _pando_logger.addHandler(handler)

# ✅ 오래된 로그 정리 함수 (예외 안전성 추가)
def clean_old_logs(log_dir, prefix, days=7):
    now = time.time()
    cutoff = now - (days * 86400)

    if not os.path.isdir(log_dir):
        return

    for fname in os.listdir(log_dir):
        if fname.startswith(prefix) and fname.endswith(".log"):
            path = os.path.join(log_dir, fname)
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)


# ✅ UI 전용 로그
def ui_log(message):
    # === 신규 ===: 호출자 파일/라인이 찍히도록 stacklevel=2 시도 (Py3.8+)
    if _pando_logger:
        try:
            _pando_logger.info(message, stacklevel=2)
        except TypeError:
            _pando_logger.info(message)

# ✅ 프록시 전용 로그
def log_info(message):
    if MITM_AVAILABLE and ctx:
        # === 신규 ===: mitmproxy 로그 API는 warning/info 등으로 통일
        try:
            ctx.log.info(message)
        except Exception:
            # 호환성 문제 시 무시
            pass
    if _pando_logger:
        # === 신규 ===: 호출자 위치 보존
        try:
            _pando_logger.info(message, stacklevel=2)
        except TypeError:
            _pando_logger.info(message)

def log_warn(message):
    if MITM_AVAILABLE and ctx:
        try:
            # warn 대신 warning 권장
            ctx.log.warning(message)
        except Exception:
            # 일부 구버전에서는 warn만 제공할 수 있으므로 폴백
            try:
                ctx.log.warn(message)
            except Exception:
                pass
    if _pando_logger:
        # === 신규 ===: 호출자 위치 보존
        try:
            _pando_logger.warning(message, stacklevel=2)
        except TypeError:
            _pando_logger.warning(message)

def log_error(message):
    if MITM_AVAILABLE and ctx:
        try:
            ctx.log.error(message)
        except Exception:
            pass
    if _pando_logger:
        # === 신규 ===: 호출자 위치 보존
        try:
            _pando_logger.error(message, stacklevel=2)
        except TypeError:
            _pando_logger.error(message)
