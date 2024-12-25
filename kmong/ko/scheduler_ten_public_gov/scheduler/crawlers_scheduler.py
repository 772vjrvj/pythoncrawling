import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import logger
from utils.date import get_current_time
from db.db_connection import connect_to_db
from db.dmnfr_trend.dmnfr_trend_operations import select_existing_data, insert_all_data_to_db, select_init_data
from crawlers import get_crawler
from utils.date import get_date


class Scheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()

    def start(self):
        crawler_list_two = ["KatiExport", "KatiReport"]
        self.scheduler.add_job(self.crawlers_and_db, CronTrigger(hour=2, minute=0, second=0), args=[crawler_list_two])  # 새벽 2시

        crawler_list_three = ["KreiList", "KreiResearch", "StepiReport", "UsdaPress", "MaffPress", "MoaPress"]
        self.scheduler.add_job(self.crawlers_and_db, CronTrigger(hour=3, minute=0, second=0), args=[crawler_list_three]) # 새벽 3시

        crawler_list_seven = ["KistepGpsTrend", "KistepBoard"]
        self.scheduler.add_job(self.crawlers_and_db, CronTrigger(hour=7, minute=0, second=0), args=[crawler_list_seven]) # 새벽 7시

        # 스케줄러 시작
        try:
            logger.info("스케줄러 시작")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("스케줄러 종료")


    def crawlers_and_db(self, crawler_list):

        logger.info("작업이 실행되었습니다. 시간: {}".format(get_current_time()))
        logger.info(f'작업목록 : {crawler_list}')


        for crawler_info in crawler_list:
            session = connect_to_db()  # DB 연결 함수 호출

            # 미리 생성된 크롤러 객체를 가져옴
            crawler = get_crawler(crawler_info)

            try:
                db_exist_datas = select_existing_data(session, crawler.src)
                crawler_datas = crawler.run()

                # 오늘 날짜와 어제 날짜 계산
                today = get_date(0)  # 오늘 날짜
                yesterday = get_date(-1)  # 어제 날짜

                # 크롤링 데이터에서 오늘과 어제 날짜만 필터링
                filter_crawler_datas = [
                    crawler_data for crawler_data in crawler_datas
                    if crawler_data.get('REG_YMD') == today or crawler_data.get('REG_YMD') == yesterday
                ]

                new_datas = [
                    filter_data for filter_data in filter_crawler_datas
                    if filter_data["URL"] not in [exist_data["URL"] for exist_data in db_exist_datas]
                ]
                if new_datas:
                    result = insert_all_data_to_db(session, new_datas)
                    if result:
                        logger.info(f"성공적으로 {result}개의 데이터가 등록되었습니다.")
                    else:
                        logger.info("데이터 등록에 실패했습니다.")
                else:
                    logger.info(f"등록할 데이터가 없습니다.")

            except Exception as e:
                logger.error(f"에러 발생: {str(e)}")

            finally:
                # DB 세션 종료
                session.close()
                logger.info("DB 연결 종료")
                time.sleep(random.uniform(2,3))

        logger.info("작업이 종료되었습니다. 시간: {}".format(get_current_time()))


    # 전체 DB데이터 초기화를 위해 처음 한번만 실행
    def init_crawlers_data_set(self, crawler_list):

        logger.info("작업이 실행되었습니다. 시간: {}".format(get_current_time()))
        logger.info(f"작업 목록: {crawler_list}")


        for index, crawler_info in enumerate(crawler_list, start=1):
            session = connect_to_db()  # DB 연결 함수 호출
            logger.info(f"번호 : {index}, 작업: {crawler_info}")

            # 미리 생성된 크롤러 객체를 가져옴
            crawler = get_crawler(crawler_info)

            try:
                init_data_cnt = select_init_data(session, crawler.src)
                # init_data_cnt = 0
                if init_data_cnt == 0:

                    crawler_datas = crawler.run()

                    if crawler_datas:
                        result = insert_all_data_to_db(session, crawler_datas)
                        # result = None
                        if result:
                            logger.info(f"성공적으로 {result}개의 데이터가 등록되었습니다.")
                        else:
                            logger.info("데이터 등록에 실패했습니다.")
                    else:
                        logger.info(f"등록할 데이터가 없습니다.")

            except Exception as e:
                logger.error(f"에러 발생: {str(e)}")

            finally:
                # DB 세션 종료
                session.close()
                logger.info("DB 연결 종료")

        logger.info("작업이 종료되었습니다. 시간: {}".format(get_current_time()))