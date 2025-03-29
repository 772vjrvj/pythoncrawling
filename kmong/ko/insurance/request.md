# 보험 상품 데이터 수집 의뢰서

## 1. 개요
국내 34개 보험사의 공식 홈페이지에서 상품별 약관, 사업방법서, 상품요약서를 PDF로 수집하고, 각 상품의 핵심 정보를 JSON 형식으로 정리해주세요. 파일은 체계적인 디렉토리 구조로 저장하여 Node.js를 통해 쉽게 접근할 수 있어야 합니다.

## 2. 데이터 수집 방법
보험사 공식 홈페이지 공시실의 상품정보 페이지에서 상품별로 [약관, 사업방법서, 상품요약서] pdf 다운로드

## 3. 준비상황
대상 국내 보험사 목록(34개)

## 4. 요청하는 자료

### 핵심 데이터

```
    [   
        {
            companyCode: string;
            companyName: string;
            category: any;
            productNameOriginal: string;
            productName: string;
            productNameSafe: string;
            version: number;
            isForSale: boolean;
            saleStartDate: string; // YYYY-MM-DD 형식
            saleEndDate: string | null; // YYYY-MM-DD 형식, 판매중인 상품은 null
            policyFilePath: string;
            planFilePath: string | null;
            summaryFilePath: string | null;
        }
    ]
```
### 약관, 사업방법서, 상품요약서 파일
pdf 형태로 다운로드 받아서 제공해주세요

### 통계
결과물의 보험사-상품별 별로 version의 개수를 제공해주시기 바랍니다.


## 5. 필드 상세 설명
- companyCode: 금융기관코드. 추후 첨부파일 참고
- companyName: 금융기관명. 추후 첨부파일 참고
- category: 이번 의뢰의 핵심적인 부분은 아닙니다. "개인", "법인", "연금", "보장" 등의 키워드를 string[] 형태로 저장해주시는게 간단할 것 같습니다. 모든 보험사에 대하여 일관적인 방법을 적용하시되, 재처리가 가능한 수준에서 편하신 방식대로 결정하시면 됩니다.
- productNameOriginal: 상품명 - 페이지 내용 그대로 trim 처리만
- productName: productNameOriginal에서 공백문자열(' ')을 제거한 상품명
- productNameSafe: 파일 경로로 사용할 수 있도록 특수문자가 제거된 안전한 상품명. 파일 경로로 사용할수 없는 특수문자만 최소한으로 escape 처리해주세요. escape된 목록을 따로 알려주세요.
- version: 같은 상품도 약관 개정으로 인해 기간별로 약관이 다릅니다. 판매기간이 가장 과거인 것부터 1부터 시작하는 auto increment number로 지정해주세요.
- isForSale: 보험 상품이 현재 판매중인지, 판매중지인지 여부
- saleStartDate: 판매 시작일(YYYY-MM-DD 형식)
- saleEndDate: 판매 종료일(YYYY-MM-DD 형식). 현재 판매중인 상품은 null
- policyFilePath: 약관 파일의 경로
- planFilePath: 사업방법서 파일 경로
- summaryFilePath: 상품요약서 파일 경로

## 6. 파일 저장 규칙
- 파일 형식: PDF 형태로 다운로드하여 저장
- 디렉토리 구조: {금융기관코드}/{productNameSafe}/{파일명}
- 파일명 형식: v{version}-{파일종류}.pdf
  - 예시: v1-policy.pdf, v2-plan.pdf, v3-summary.pdf
- 파일 종류 코드:
  - policy: 약관
  - plan: 사업방법서
  - summary: 상품요약서

## 7. 파일종류에 대한 기타 정보
- 약관: 모든 version에 존재
- 사업방법서: 대부분 존재하나 아주 오래된 버전에는 없을 수 있음
- 상품요약서: 상품별로 가장 최근 version에만 존재