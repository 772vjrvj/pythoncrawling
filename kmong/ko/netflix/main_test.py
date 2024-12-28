import requests

# URL 설정
url = "https://www.netflix.com/nq/website/memberapi/release/metadata?movieid=81726580"

# 헤더 설정
headers = {
    "authority": "www.netflix.com",
    "method": "GET",
    "path": "/nq/website/memberapi/release/metadata?movieid=81726580",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cookie": "flwssn=db01b2e5-e70f-48c5-abcc-6fec62caec37; profilesNewSession=0; nfvdid=BQFmAAEBEEn0gpFp2P5U5jWLH39YJAtgrDYaum9QVXLXkWXSS8uOzQfSX_hVTq9OfCl6SSjMz5w1q13lxkGKdjQrJny737I7hvV6SLcm97gqx5pFqSRgcDUt2c7LZAcYqwqmUZnxF9RwLcKX2Yn0gTUCugCDxiwo; SecureNetflixId=v%3D3%26mac%3DAQEAEQABABRDgEbUN5lIPT7InAPE_l9bjnBAdrjALEs.%26dt%3D1735362492402; NetflixId=v%3D3%26ct%3DBgjHlOvcAxKAA2SQSaqxt8LOyWyyrfJRyROJ4b9jttgebn2rGM_LfXUEYCm1HpmClYXybaKMv2i4FQgyAAi6tX00lKFzsds_q5qX2mhN2EqomswivOfl2Ui3JCBYB4zlz0XDKSjnEEmWxahu9l3DvSnYDzd08fT12afenSeANGC-NK4aDy3_X588egTlBJK8nC75v6Rtyf1AtJGVxqJ2RRoo0Z5GjyMFRcFqV2Dcsgxc982rJpn11cYUsWo3I5o9y8ZNN463qV3xergO22R6A7Tw8JcCfQt4SYLw1Gzotgnrnd00GYgDPjakBS4BIlJP-j9UGmeg7FmgPwu5h8oPyE3j7MqVVPbytU63QpMtaeArUFswXDyGW3zL-nYRggPhmIPeAVkU_hSN1PC-oNAufLIn17not1Wj-keZkV3AVteFQR2MS_WJwM-sURW7rgrth3pBmPDC7-H5bVLFCJowv1g4kLM8McLg4xLlZ3DVgNesNdRD3p9UDcxsQ8cxciDRT89DqjGR8gsS1RgGIg4KDF-bhVssC4gD_wfm3Q..%26ch%3DAQEAEAABABTNos4ezc_h-BtC9FFKNEAC30V5WK-W2Uk.; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Dec+28+2024+14%3A38%3A10+GMT%2B0900+(%ED%95%9C%EA%B5%AD+%ED%91%9C%EC%A4%80%EC%8B%9C)&version=202411.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=69ab3fdd-c07a-466e-9590-1ea94d67038c&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false",
    "priority": "u=1, i",
    "referer": "https://www.netflix.com/watch/81726580",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# GET 요청
response = requests.get(url, headers=headers)

# 결과 출력
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
