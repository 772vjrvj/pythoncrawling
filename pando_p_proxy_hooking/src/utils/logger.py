# src/utils/logger.py
import logging
import os
import sys
import time
import threading
import shutil
from datetime import datetime, timedelta

_pando_logger = None
__LOG_MAINTENANCE_STARTED = False


# 경로 가져오기
def get_executable_dir() -> str:
    """
    실행 환경에 따라 기준 디렉토리 반환
    - 배포(PyInstaller): 실행 파일 폴더 또는 _MEIPASS
    - 개발(소스 실행): 현재 파일 기준 프로젝트 루트(상위 2단계)
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
        return os.path.abspath(base)
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# 초기화
def init_pando_logger() -> None:
    """
    전역 pando 로거 초기화 (중복 안전)
    - logs/pando.log 생성
    - 자정마다 백업 + 원본 초기화 스레드 기동
    - 오래된 pando 백업 자동 정리
    """
    global _pando_logger

    logs_dir = os.path.join(get_executable_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # pando 백업들만 유지기간 체크
    delete_old_backups(logs_dir, prefix="pando", keep_days=7)  # ← 이렇게 교체

    if _pando_logger is not None and _pando_logger.handlers:
        _start_log_maintenance_background(logs_dir)
        return

    logger = logging.getLogger("pando")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 상위 루트 로거로 전파 방지

    log_path = os.path.join(logs_dir, "pando.log")
    handler = logging.FileHandler(log_path, encoding="utf-8")

    fmt = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
    _pando_logger = logger

    _start_log_maintenance_background(logs_dir)



# pando.log 파일 초기화
def _truncate_current_handler_file() -> None:
    """열려 있는 FileHandler 스트림을 사용해 안전하게 내용만 0바이트로."""
    if not _pando_logger:
        return
    for h in _pando_logger.handlers:
        if isinstance(h, logging.FileHandler):
            try:
                h.acquire()
                h.flush()
                h.stream.seek(0)
                h.stream.truncate(0)
            finally:
                h.release()
            return


# pando.log -> pando-yyyymmdd.log로 파일 백업 자정에
def _backup_if_not_empty(src_path: str, dst_path: str) -> bool:
    """원본이 비어있지 않으면 복사하여 백업."""
    try:
        if not os.path.exists(src_path) or os.path.getsize(src_path) <= 0:
            return False
        shutil.copyfile(src_path, dst_path)
        return True
    except Exception as e:
        if _pando_logger:
            _pando_logger.warning(f"[log] 백업 실패: {src_path} -> {dst_path} / err={e}")
        return False


# 날짜별 로그 파일 경로
def _dated_backup_path(logs_dir: str, prefix: str, date_obj: datetime) -> str:
    """YYYYMMDD 접미사 파일명 생성(중복 시 -1, -2…)."""
    base = f"{prefix}-{date_obj.strftime('%Y%m%d')}.log"
    candidate = os.path.join(logs_dir, base)
    if not os.path.exists(candidate):
        return candidate
    idx = 1
    while True:
        alt = os.path.join(logs_dir, f"{prefix}-{date_obj.strftime('%Y%m%d')}-{idx}.log")
        if not os.path.exists(alt):
            return alt
        idx += 1


# 백업 전에 핸들 flush (윈도우 잠금/유실 예방)
def _flush_file_handlers() -> None:
    if not _pando_logger:
        return
    for h in _pando_logger.handlers:
        if isinstance(h, logging.FileHandler):
            try:
                h.flush()
            except Exception:
                pass


# 파일 백업 및 초기화
def backup_and_clear_pando(logs_dir: str) -> None:
    pando_src = os.path.join(logs_dir, "pando.log")
    backup_dst = _dated_backup_path(logs_dir, "pando", datetime.now())

    _flush_file_handlers()  # ← 추가
    did_backup = _backup_if_not_empty(pando_src, backup_dst)

    _truncate_current_handler_file()
    if _pando_logger:
        _pando_logger.info(f"[log] pando.log 자정 처리: 백업={'OK' if did_backup else 'SKIP'}, 원본 초기화")


# 7일 경과 파일들 삭제 7개만 보존
def delete_old_backups(logs_dir: str, prefix: str, keep_days: int) -> None:
    """
    달력 기준 보존: '오늘'을 포함해 keep_days일만 남기고 그 이전은 삭제.
    예) keep_days=1 -> 오늘만 보존, 어제 00:00 이전은 전부 삭제.
    """
    if not os.path.isdir(logs_dir):
        return

    # 자정 기준 컷오프 계산 (오늘 00:00 - (keep_days-1)일)
    today0 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_dt = today0 - timedelta(days=max(keep_days - 1, 0))
    cutoff_ts = cutoff_dt.timestamp()

    for fname in os.listdir(logs_dir):
        # 메인 pando.log는 항상 보존
        if fname == f"{prefix}.log":
            continue
        if not (fname.startswith(prefix) and fname.endswith(".log")):
            continue

        path = os.path.join(logs_dir, fname)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff_ts:
                os.remove(path)
        except Exception as e:
            if _pando_logger:
                _pando_logger.warning(f"[log] 오래된 로그 삭제 실패: {fname} / err={e}")


# 자정까지 남은 초 리턴
def _seconds_until_next_midnight() -> float:
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    next_midnight = datetime.combine(tomorrow, datetime.min.time())
    return max(1.0, (next_midnight - now).total_seconds())



# 실제 자정마다 파일 삭제를 위해 도는 루프
def _pando_midnight_rotate_loop(logs_dir: str, keep_days: int = 7) -> None:
    """자정마다 pando.log 백업+초기화 후 보존기간 경과 백업 삭제."""
    while True:
        time.sleep(_seconds_until_next_midnight())
        try:
            backup_and_clear_pando(logs_dir)
        except Exception as e:
            if _pando_logger:
                _pando_logger.warning(f"[log] pando 자정 백업/초기화 실패: err={e}")
        try:
            delete_old_backups(logs_dir, prefix="pando", keep_days=keep_days)
        except Exception as e:
            if _pando_logger:
                _pando_logger.warning(f"[log] pando 오래된 백업 삭제 실패: err={e}")


# 쓰레드 시작
def _start_log_maintenance_background(logs_dir: str) -> None:
    """자정 회전 스레드 단 한 번만 기동."""
    global __LOG_MAINTENANCE_STARTED
    if __LOG_MAINTENANCE_STARTED:
        return
    __LOG_MAINTENANCE_STARTED = True
    t = threading.Thread(target=_pando_midnight_rotate_loop, args=(logs_dir, 7), daemon=True)
    t.start()


# === Public logging helpers ===
def ui_log(message: str) -> None:
    if _pando_logger:
        try:
            _pando_logger.info(message, stacklevel=2)
        except TypeError:
            _pando_logger.info(message)


def log_info(message: str) -> None:
    if _pando_logger:
        try:
            _pando_logger.info(message, stacklevel=2)
        except TypeError:
            _pando_logger.info(message)


def log_warn(message: str) -> None:
    if _pando_logger:
        try:
            _pando_logger.warning(message, stacklevel=2)
        except TypeError:
            _pando_logger.warning(message)


def log_error(message: str) -> None:
    if _pando_logger:
        try:
            _pando_logger.error(message, stacklevel=2)
        except TypeError:
            _pando_logger.error(message)
