import os
import subprocess
import time

def run_install_cert():
    bat_path = os.path.join(os.path.dirname(__file__), "install_cert.bat")
    print("\n[🔐] 인증서 설치 중...\n")
    result = subprocess.call(bat_path, shell=True)
    if result == 0:
        print("[✔] 인증서 설치 완료. 후킹을 바로 시작합니다...\n")
        run_mitmproxy()
    else:
        print("[❌] 인증서 설치 중 오류가 발생했습니다.")

def run_mitmproxy():
    bat_path = os.path.join(os.path.dirname(__file__), "run_mitmproxy.bat")
    print("\n[📡] 후킹을 시작합니다...\n")
    subprocess.call(bat_path, shell=True)

def run_reset_proxy():
    bat_path = os.path.join(os.path.dirname(__file__), "reset_proxy.bat")
    subprocess.call(bat_path, shell=True)

def main():
    while True:
        print("=======================================")
        print("      mitmproxy 후킹 실행기 (CMD)")
        print("=======================================")
        print("1. 인증서 설치 → 후킹 자동 실행")
        print("2. 후킹만 실행")
        print("3. 프록시 초기화")
        print("4. 종료")
        print("=======================================")

        choice = input("실행할 작업 번호를 입력하세요 (1~4): ").strip()

        if choice == "1":
            run_install_cert()
        elif choice == "2":
            run_mitmproxy()
        elif choice == "3":
            run_reset_proxy()
        elif choice == "4":
            print("프로그램을 종료합니다.")
            time.sleep(1)
            break
        else:
            print("잘못된 입력입니다. 다시 선택해주세요.\n")

if __name__ == "__main__":
    main()
