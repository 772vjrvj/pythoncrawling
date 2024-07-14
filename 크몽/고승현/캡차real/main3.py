import pandas as pd
import numpy as np
import time
import csv
from tqdm import tqdm_notebook
import re
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import ssl
import random
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# SSL 설정 (인증서 검증 비활성화)
ssl._create_default_https_context = ssl._create_unverified_context

# 경고 무시
warnings.filterwarnings('ignore')

# 논문 제목
some_paper = [
    "Themes in the work of Margaret Masterman", "Toward High Performance Machine Translation: Preliminary Results from Massively Parallel Memory-Based Translation on SNAP*",
    "Interactive multilingual text generation for a monolingual user", "Corpora and Machine Translation",
    "A Parameter-Based Message-Passing Parser for MT of Korean and English", "DEVELOPING AND EVALUATING A PROBABILISTIC LR PARSER OF PART-OF-SPEECH AND PUNCTUATION LABELS*",
    "Associating semantic components with intersective Levin classes", "Harmonised large-scale syntactic/semantic lexicons: a European multilingual infrastructure",
    "NEW TABULAR ALGORITHMS FOR LIG PARSING", "Identification et catégorisation automatiques des anthroponymes du Franc ¸ais",
    "Word Formation in Computational Linguistics", "Une caractérisation de la pertinence pour les actions de référence", "Non-Contiguous Tree Parsing",
    "Europarl: A Parallel Corpus for Statistical Machine Translation", "Translation of Multiword Expressions Using Parallel Suffix Arrays",
    "Rapid development of RBMT systems for related languages", "The LIUM Arabic/English Statistical Machine Translation System for IWSLT 2008",
    "Can Semantic Role Labeling Improve SMT?", "Analyse morphologique en terminologie biomédicale par alignement et apprentissage non-supervisé",
    "The DCU Machine Translation Systems for IWSLT 2011", "A User-Based Usability Assessment of Raw Machine Translated Technical Instructions",
    "ROI Analysis model for Language Service Providers", "Comparison of post-editing productivity between professional translators and lay users",
    "Effects of Word Alignment Visualization on Post-Editing Quality & Speed †", "Factored Neural Machine Translation Architectures",
    "Analyse et évolution de la compréhension de termes techniques", "Public Apologies in India -Semantics, Sentiment and Emotion",
    "A Language Invariant Neural Method for TimeML Event Detection", "Diverse dialogue generation with context dependent dynamic loss function",
    "XED: A Multilingual Dataset for Sentiment Analysis and Emotion Detection", "Entity Attribute Relation Extraction with Attribute-Aware Embeddings",
    "SimsterQ: A Similarity based Clustering Approach to Opinion Question Answering", "On the weak link between importance and prunability of attention heads",
    "Interpretable Entity Representations through Large-Scale Typing", "Generalizable and Explainable Dialogue Generation via Explicit Action Learning",
    "Controlled Text Generation with Adversarial Learning", "ReINTEL: A Multimodal Data Challenge for Responsible Information Identification on Social Network Sites",
    "Embed More Ignore Less (EMIL): Exploiting Enriched Representations for Arabic NLP", "Control Image Captioning Spatially and Temporally",
    "Coreference Reasoning in Machine Reading Comprehension", "Peru is Multilingual, Its Machine Translation Should Be Too?",
    "CONDA: a CONtextual Dual-Annotated dataset for in-game toxicity understanding and detection", "Modeling Users and Online Communities for Abuse Detection: A Position on Ethics and Explainability",
    "Situation-Specific Multimodal Feature Adaptation", "Welcome to the 18th biennial conference of the International Association of Machine Translation (IAMT) -MT Summit 2021 Virtual!",
    "End-to-end ASR to jointly predict transcriptions and linguistic annotations", "Double Perturbation: On the Robustness of Robustness and Counterfactual Bias Evaluation",
    "RocketQA: An Optimized Training Approach to Dense Passage Retrieval for Open-Domain Question Answering", "On the Usability of Transformers-based models for a French Question-Answering task",
    "A Semi-Supervised Approach to Detect Toxic Comments", "Unsupervised Representation Disentanglement of Text: An Evaluation on Synthetic Datasets",
    "Amrita_CEN_NLP@SDP2021 Task A and B", "NLRG at SemEval-2021 Task 5: Toxic Spans Detection Leveraging BERT-based Token Classification and Span Prediction Techniques",
    "DeepBlueAI at SemEval-2021 Task 1: Lexical Complexity Prediction with A Deep Ensemble Approach", "TransWiC at SemEval-2021 Task 2: Transformer-based Multilingual and Cross-lingual Word-in-Context Disambiguation",
    "Transformer-based Multi-Task Learning for Adverse Effect Mention Analysis in Tweets", "Memory-efficient Transformers via Top-k Attention",
    "Learning to Rank in the Age of Muppets: Effectiveness-Efficiency Tradeoffs in Multi-Stage Ranking", "Classifying Argumentative Relations Using Logical Mechanisms and Argumentation Schemes",
    "TextGraphs 2021 Shared Task on Multi-Hop Inference for Explanation Regeneration", "A Fine-Grained Analysis of BERTScore",
    "Decoding Part-of-Speech from Human EEG Signals", "BRIO: Bringing Order to Abstractive Summarization",
    "Phone-ing it in: Towards Flexible, Multi-Modal Language Model Training using Phonetic Representations of Data",
    "Multitasking Framework for Unsupervised Simple Definition Generation", "Situated Dialogue Learning through Procedural Environment Generation",
    "USST's System for AutoSimTrans 2022", "Codenames as a Game of Co-occurrence Counting",
    "Estimating word co-occurrence probabilities from pretrained static embeddings using a log-bilinear model",
    "MuCoT: Multilingual Contrastive Training for Question-Answering in Low-resource Languages", "Developing Machine Translation Engines for Multilingual Participatory Spaces",
    "Diversifying Content Generation for Commonsense Reasoning with Mixture of Knowledge Graph Experts", "KD-VLP: Improving End-to-End Vision-and-Language Pretraining with Object Knowledge Distillation",
    "Identifying and Mitigating Spurious Correlations for Improving Robustness in NLP Models", "Looking for a Handsome Carpenter! Debiasing GPT-3 Job Advertisements",
    "Dual-Channel Evidence Fusion for Fact Verification over Texts and Tables", "drsphelps at SemEval-2022 Task 2: Learning idiom representations using BERTRAM",
    "SemEval 2022 Task 12: Symlink Linking Mathematical Symbols to their Descriptions", "DRS Parsing as Sequence Labeling", "Text-based NP Enrichment"
]


# 데이터 로드 함수
def load_data(file_path):
    """JSON 파일에서 데이터를 로드하는 함수"""
    return pd.read_json(file_path)


# 첫 네 개의 텍스트를 추출하는 함수
def extract_first_four_texts(data):
    """각 항목에서 첫 네 개의 텍스트를 추출하는 함수"""
    result = {}
    for key, value in data.items():
        texts = [sentence['text'] for sentence in value['x'][:4]]
        result[key] = texts
    return result


# Selenium 웹 드라이버 설정 함수
def setup_driver():
    try:
        chrome_options = Options()
        user_data_dir = "C:\\Users\\772vj\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        chrome_options.add_experimental_option('prefs', {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        script = '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
        '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None



def search_google(driver, url, texts):
    driver.get(url)
    search_box = driver.find_element(By.NAME, 'q')
    search_box.clear()
    search_box.send_keys(f"{texts}")
    search_box.send_keys(Keys.RETURN)



# 논문 제목을 검색하는 함수
def search_paper_titles(driver, extracted_texts, url='https://www.google.co.kr/'):
    """추출된 텍스트를 사용하여 구글에서 논문 제목을 검색하는 함수"""
    paper_names = {}
    error_names = {}

    index = 0

    for key, texts in extracted_texts.items():
        index = index + 1
        print(f"============= index: {index}, key : {key}")
        search_google(driver, url, texts)
        time.sleep(random.uniform(2, 5))

        # 캡챠 확인

        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            print("reCAPTCHA iframe 존재.")

            # reCAPTCHA iframe 으로 변경
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )

            # 클릭 the reCAPTCHA checkbox
            recaptcha_checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))
            )

            # 로봇 방지 클릭
            recaptcha_checkbox.click()
            time.sleep(3)

            # 안전한 검색을 위해 재 검색 시도
            search_google(driver, url, texts)
            print("크롤링 재시도...")

            time.sleep(random.uniform(2, 5))

            paper_names, error_names = paper_name(driver, key, paper_names, error_names)
            if key in error_names:
                pass

        except TimeoutException:
            print("reCAPTCHA iframe 미존재.")
            paper_names, error_names = paper_name(driver, key, paper_names, error_names)
            if key in error_names:
                pass


    return paper_names, error_names


def paper_name(driver, key, paper_names, error_names):
    try:
        paper_name = driver.find_element(By.XPATH, '/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
        print("paper_name1:", paper_name)
        paper_names[key] = paper_name
    except:
        try:
            paper_name = driver.find_element(By.XPATH, '/html/body/div[5]/div/div[13]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
            print("paper_name2:", paper_name)
            paper_names[key] = paper_name
        except:
            try:
                paper_name = driver.find_element(By.XPATH, '/html/body/div[5]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
                print("paper_name3:", paper_name)
                paper_names[key] = paper_name
            except:
                try:
                    paper_name = driver.find_element(By.XPATH, '/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div/div/span/a/h3').text
                    print("paper_name4:", paper_name)
                    paper_names[key] = paper_name
                except:
                    error_names[key] = "Not Found"
                    print("error!!")
    time.sleep(0.5)
    return paper_names, error_names


# CSV 파일로 저장하는 함수
def save_to_csv(paper_names, file_path):
    """paper_names 딕셔너리를 CSV 파일로 저장하는 함수"""
    df = pd.DataFrame(list(paper_names.items()), columns=['Key', 'Paper Name'])
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")


# 메인 함수
def main():
    """메인 실행 함수"""
    data = load_data('full_raw.json')  # 데이터 로드
    extracted_texts = extract_first_four_texts(data)  # 텍스트 추출

    for key, texts in extracted_texts.items():
        print(f"{texts}")

    driver = setup_driver()  # 웹 드라이버 설정
    paper_names, error_names = search_paper_titles(driver, extracted_texts)  # 논문 제목 검색
    driver.quit()  # 드라이버 종료

    print("========================================")
    print("Paper Names:", paper_names)
    print("Errors:", error_names)

    # CSV 파일로 저장
    save_to_csv(paper_names, 'paper_names.csv')


# 프로그램 실행
if __name__ == "__main__":
    main()
