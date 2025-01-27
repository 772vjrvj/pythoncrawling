from scheduler.crawlers_scheduler import Scheduler
from crawlers import crawler_list  # crawler_list를 임포트


def main():
    scheduler = Scheduler()

    # DB 데이터 초기화를 위해 한번만 실행
    # scheduler.init_crawlers_data_set(crawler_list)

    # 스케줄러 시작
    scheduler.start()

if __name__ == '__main__':
    main()
