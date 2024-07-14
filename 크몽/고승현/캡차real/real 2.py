import pandas as pd
import numpy as np

some_paper = ["Themes in the work of Margaret Masterman",
              "Toward High Performance Machine Translation: Preliminary Results from Massively Parallel Memory-Based Translation on SNAP*",
              "Interactive multilingual text generation for a monolingual user","Corpora and Machine Translation",
              "A Parameter-Based Message-Passing Parser for MT of Korean and English",
              "DEVELOPING AND EVALUATING A PROBABILISTIC LR PARSER OF PART-OF-SPEECH AND PUNCTUATION LABELS*",
              "Associating semantic components with intersective Levin classes",
              "Harmonised large-scale syntactic/semantic lexicons: a European multilingual infrastructure",
              "NEW TABULAR ALGORITHMS FOR LIG PARSING",
              "Identification et catégorisation automatiques des anthroponymes du Franc ¸ais",
              "Word Formation in Computational Linguistics",
              "Une caractérisation de la pertinence pour les actions de référence", "Non-Contiguous Tree Parsing",
              "Europarl: A Parallel Corpus for Statistical Machine Translation",
              "Translation of Multiword Expressions Using Parallel Suffix Arrays",
              "Rapid development of RBMT systems for related languages",
              "The LIUM Arabic/English Statistical Machine Translation System for IWSLT 2008",
              "Can Semantic Role Labeling Improve SMT?",
              "Analyse morphologique en terminologie biomédicale par alignement et apprentissage non-supervisé",
              "The DCU Machine Translation Systems for IWSLT 2011",
              "A User-Based Usability Assessment of Raw Machine Translated Technical Instructions",
              "ROI Analysis model for Language Service Providers",
              "Comparison of post-editing productivity between professional translators and lay users",
              "Effects of Word Alignment Visualization on Post-Editing Quality & Speed †",
              "Factored Neural Machine Translation Architectures",
              "Analyse et évolution de la compréhension de termes techniques","Public Apologies in India -Semantics, Sentiment and Emotion",
              "A Language Invariant Neural Method for TimeML Event Detection",
              "Diverse dialogue generation with context dependent dynamic loss function",
              "XED: A Multilingual Dataset for Sentiment Analysis and Emotion Detection",
              "Entity Attribute Relation Extraction with Attribute-Aware Embeddings",
              "SimsterQ: A Similarity based Clustering Approach to Opinion Question Answering",
              "On the weak link between importance and prunability of attention heads",
              "Interpretable Entity Representations through Large-Scale Typing",
              "Generalizable and Explainable Dialogue Generation via Explicit Action Learning","Controlled Text Generation with Adversarial Learning",
              "ReINTEL: A Multimodal Data Challenge for Responsible Information Identification on Social Network Sites",
              "Embed More Ignore Less (EMIL): Exploiting Enriched Representations for Arabic NLP","Control Image Captioning Spatially and Temporally",
              "Coreference Reasoning in Machine Reading Comprehension","Peru is Multilingual, Its Machine Translation Should Be Too?",
              "CONDA: a CONtextual Dual-Annotated dataset for in-game toxicity understanding and detection",
              "Modeling Users and Online Communities for Abuse Detection: A Position on Ethics and Explainability","Situation-Specific Multimodal Feature Adaptation",
              "Welcome to the 18th biennial conference of the International Association of Machine Translation (IAMT) -MT Summit 2021 Virtual!",
              "End-to-end ASR to jointly predict transcriptions and linguistic annotations",
              "Double Perturbation: On the Robustness of Robustness and Counterfactual Bias Evaluation",
              "RocketQA: An Optimized Training Approach to Dense Passage Retrieval for Open-Domain Question Answering",
              "On the Usability of Transformers-based models for a French Question-Answering task",
              "A Semi-Supervised Approach to Detect Toxic Comments",
              "Unsupervised Representation Disentanglement of Text: An Evaluation on Synthetic Datasets",
              "Amrita_CEN_NLP@SDP2021 Task A and B",
              "NLRG at SemEval-2021 Task 5: Toxic Spans Detection Leveraging BERT-based Token Classification and Span Prediction Techniques",
              "DeepBlueAI at SemEval-2021 Task 1: Lexical Complexity Prediction with A Deep Ensemble Approach",
              "TransWiC at SemEval-2021 Task 2: Transformer-based Multilingual and Cross-lingual Word-in-Context Disambiguation",
              "Transformer-based Multi-Task Learning for Adverse Effect Mention Analysis in Tweets",
              "Memory-efficient Transformers via Top-k Attention",
              "Learning to Rank in the Age of Muppets: Effectiveness-Efficiency Tradeoffs in Multi-Stage Ranking",
              "Classifying Argumentative Relations Using Logical Mechanisms and Argumentation Schemes",
              "TextGraphs 2021 Shared Task on Multi-Hop Inference for Explanation Regeneration",
              "A Fine-Grained Analysis of BERTScore",
              "Decoding Part-of-Speech from Human EEG Signals","BRIO: Bringing Order to Abstractive Summarization",
              "Phone-ing it in: Towards Flexible, Multi-Modal Language Model Training using Phonetic Representations of Data",
              "Multitasking Framework for Unsupervised Simple Definition Generation",
              "Situated Dialogue Learning through Procedural Environment Generation",
              "USST's System for AutoSimTrans 2022","Codenames as a Game of Co-occurrence Counting",
              "Estimating word co-occurrence probabilities from pretrained static embeddings using a log-bilinear model",
              "MuCoT: Multilingual Contrastive Training for Question-Answering in Low-resource Languages",
              "Developing Machine Translation Engines for Multilingual Participatory Spaces",
              "Diversifying Content Generation for Commonsense Reasoning with Mixture of Knowledge Graph Experts",
              "KD-VLP: Improving End-to-End Vision-and-Language Pretraining with Object Knowledge Distillation",
              "Identifying and Mitigating Spurious Correlations for Improving Robustness in NLP Models",
              "Looking for a Handsome Carpenter! Debiasing GPT-3 Job Advertisements","Dual-Channel Evidence Fusion for Fact Verification over Texts and Tables",
              "drsphelps at SemEval-2022 Task 2: Learning idiom representations using BERTRAM",
              "SemEval 2022 Task 12: Symlink Linking Mathematical Symbols to their Descriptions",
              "DRS Parsing as Sequence Labeling","Text-based NP Enrichment"              
]

import pandas as pd
data = pd.read_json('full_raw.json')
data.head()

def extract_first_four_texts(data):
    result = {}
    for key, value in data.items():
        texts = [sentence['text'] for sentence in value['x'][:4]]
        result[key] = texts
    return result

extracted_texts = extract_first_four_texts(data)

for key, texts in extracted_texts.items():
    print(f"{texts}")

import time
import csv
from tqdm import tqdm_notebook
import re

import warnings
warnings.filterwarnings('ignore')

import pandas as pd

from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from fake_useragent import UserAgent
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
user_agent = UserAgent()
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={user_agent.random}")
#headers = {'User-Agent':user_agent.random}

# driver 설정
url = 'https://www.google.co.kr/'
driver = webdriver.Chrome(options=options)

paper_names = {}
error_names = {}
for key, texts in extracted_texts.items():
    driver.get(url)
    search_box = driver.find_element(By.NAME, 'q')
    search_box.clear()  # Clear the search box before entering new text
    search_box.send_keys(f"{texts}")
    #search_box.send_keys("\uE007")
    search_box.send_keys(Keys.RETURN)
    time.sleep(1.1)
    try:
        paper_name = driver.find_element(By.XPATH,'/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
        print("paper_name1:",paper_name)
        paper_names[key] = paper_name
        
    except:
        try:
            paper_name = driver.find_element(By.Xpath,'/html/body/div[5]/div/div[13]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
            print("paper_name2:",paper_name)
            paper_names[key] = paper_name
            
        except:
            try:
                paper_name = driver.find_element(By.Xpath,'/html/body/div[5]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
                print("paper_name3:",paper_name)
                paper_names[key] = paper_name
                
            except:
                try:
                    paper_name = driver.find_element(By.Xpath,'/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div/div/span/a/h3').text
                    print("paper_name4:",paper_name)
                    paper_names[key] = paper_name
                    
                except:
                    error_names[key] = "Not Found"
                    print("error!!")
                    pass
    time.sleep(0.5)
    
