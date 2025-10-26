import asyncio
import logging
import sys
import time
import traceback

from modules.bot import CryptoExchangeBot
from modules.constants import MAX_RESTARTS
from modules.database import Database
from modules.log import send_webhook_log
from modules.utils import get_env_config

config = get_env_config()

ERROR_LOG_WEBHOOK = config.error_log_webhook

MONGODB_URI = config.mongodb_uri
TOKEN = config.token

logging.basicConfig(
    level=logging.WARN,
    format="%(asctime)s %(levelname)s: %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def format_exception(exctype, value, tb):
    tb_str = ''.join(traceback.format_exception(exctype, value, tb))
    return f"```python\n{tb_str}\n```"

def global_exception_handler(exctype, value, tb):
    if exctype in (KeyboardInterrupt, SystemExit):
        return
    log = f"[동기 전역 예외 발생]\n{format_exception(exctype, value, tb)}"
    send_webhook_log(ERROR_LOG_WEBHOOK, log)
    print("전역 동기 예외 무시: 종료하지 않음")

sys.excepthook = global_exception_handler

def handle_async_exception(loop, context):
    err = context.get('exception') or context.get('message')
    tb = format_exception(type(err), err, getattr(err, '__traceback__', None))
    log = f"[비동기 예외 발생]\n```python\n{tb}```"
    send_webhook_log(ERROR_LOG_WEBHOOK, log)
    print("비동기 예외 무시, 계속 실행")

async def main():
    bot = CryptoExchangeBot()
    await Database.init_db(MONGODB_URI)
    await bot.start(TOKEN)

async def safe_main():
    try:
        await main()
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print("[main 예외] 재시작합니다:\n", tb_str)
        send_webhook_log(ERROR_LOG_WEBHOOK, f"[main() 예외 - 자동 재시작]\n```python\n{tb_str}\n```")
        raise

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(handle_async_exception)

    restarts = 0
    while restarts < MAX_RESTARTS:
        try:
            loop.run_until_complete(safe_main())
            restarts = 0
        except (KeyboardInterrupt, SystemExit):
            # 정상 종료
            break
        except Exception:
            restarts += 1
            logging.warning(f"Restarting bot after exception ({restarts}/{MAX_RESTARTS})")
            time.sleep(3)
        else:
            # 정상 종료 루프 빠져나오기
            break
    else:
        # 재시도 초과
        logging.critical("Exceeded maximum restart attempts; shutting down permanently")
        send_webhook_log(ERROR_LOG_WEBHOOK,
                         "[치명적 오류] 재시도 한도 초과로 봇을 종료합니다.")