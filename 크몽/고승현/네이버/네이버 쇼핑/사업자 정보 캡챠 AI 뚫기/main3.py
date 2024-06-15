import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import base64
from google.cloud import speech
import pyaudio
import wave

def save_base64_image(base64_data, folder_path, file_name):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    files = os.listdir(folder_path)
    index = 1
    new_file_name = f"{file_name}.png"
    while new_file_name in files:
        new_file_name = f"{file_name}_{index}.png"
        index += 1

    image_data = base64.b64decode(base64_data.split(",")[1])
    with open(os.path.join(folder_path, new_file_name), "wb") as f:
        f.write(image_data)

    return os.path.join(folder_path, new_file_name)


# 2. 오디오 캡처
def record_audio(filename, duration=15):
    print('record_audio 시작')
    try:
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        fs = 44100
        p = pyaudio.PyAudio()
        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)
        frames = []
        for i in range(0, int(fs / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
        print('Finished recording')
    except Exception as e:
        print(f"An error occurred during recording: {e}")


# 3. 녹음된 오디오 파일을 한글 텍스트로 변환
def transcribe_speech(filename):
    print('transcribe_speech 시작')
    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-file.json"
        client = speech.SpeechClient()
        with open(filename, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code="ko-KR",
        )
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))
    except FileNotFoundError:
        print("The specified audio file was not found.")
    except Exception as e:
        print(f"An error occurred during transcription: {e}")


def naver_login(username, password):
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--disable-popup-blocking")

    driver = uc.Chrome(options=options, version_main=125)

    try:
        driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))

        id_input = driver.find_element(By.ID, "id")
        id_input.send_keys(username)

        pw_input = driver.find_element(By.ID, "pw")
        pw_input.send_keys(password)

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "log.login")))

        login_button = driver.find_element(By.ID, "log.login")

        login_button.click()

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "pw")))

        pw_input = driver.find_element(By.ID, "pw")
        pw_input.send_keys(password)

        voiceButton = driver.find_element(By.ID, "voice")

        voiceButton.click()

        record_audio('output.wav', duration=10)
        transcribe_speech('output.wav')

        time.sleep(100)
        #
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'captchaimg')))
        # captcha_img = driver.find_element(By.ID, 'captchaimg')
        # base64_data = captcha_img.get_attribute('src')
        # captcha_image_path = save_base64_image(base64_data, "image", "captcha_image")
        #
        # # 새 탭을 열고 로그인 페이지로 이동
        # driver.execute_script("window.open('https://chatgpt.com', '_blank');")
        # time.sleep(5)  # 새 탭이 열릴 시간을 충분히 확보
        # handles = driver.window_handles
        # if len(handles) > 1:
        #     driver.switch_to.window(handles[1])
        # else:
        #     print("새 탭이 열리지 않았습니다.")
        #     return
        #
        # driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/")
        #
        # WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.flex.items-center.justify-center.text-token-text-primary')))
        # login_complete_button = driver.find_element(By.CSS_SELECTOR, 'button.flex.items-center.justify-center.text-token-text-primary')
        # login_complete_button.click()
        #
        # # 이미지 업로드
        # image_upload_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        # image_upload_input.send_keys(captcha_image_path)

    except TimeoutException as e:
        print(f"Timeout waiting for element: {e}")
    except NoSuchElementException as e:
        print(f"An element was not found on the page: {e}")
    except WebDriverException as e:
        print(f"An error occurred with the WebDriver: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

def main():
    username = "772vjrvj"
    password = "Ksh@8818510"
    naver_login(username, password)

if __name__ == "__main__":
    main()