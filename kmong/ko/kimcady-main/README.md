# KimCady

KimCady는 김캐디 웹사이트와 통합하여 예약 정보를 수집하고 관리하는 시스템입니다.

## 최근 업데이트 내용

### 2025-04-11 결제 상태 감지 로직 개선 (추가 수정)

예약 날짜 변경 시 결제 완료 상태가 올바르게 유지되지 않는 문제를 전체 시스템 레벨에서 해결했습니다.

**문제점:**
- 예약 날짜 변경 처리 시 결제 완료(`is_paid`) 상태가 올바르게 전달되지 않음
- 예약 앱 처리(`_processAppBookings`)에서만 is_paid 체크 로직을 적용했으나, API 요청 단계에서 해당 로직이 누락됨
- API 통신 및 응답 처리 과정에서 결제 상태 우선순위가 일관되지 않게 적용됨

**해결 방법:**
- API 요청 함수(`sendTo24GolfApi`)에서 결제 상태 확인 로직 개선
- 결제 상태 확인 우선순위 명확하게 설정: `is_paid` → `paymented` → 캐시된 상태
- 예약 업데이트 처리(`processBookingUpdate`)에 캐시된 예약의 `is_paid` 상태 전달 로직 추가
- 데이터 캐싱 및 매핑 과정에서 결제 상태 확인 로직 우선순위 통일

```javascript
// 수정: 결제 상태 논리 변경
// 1. apiData.is_paid가 정의되어 있으면 최우선으로 사용
// 2. apiData.paymented가 정의되어 있으면 해당 값 사용
// 3. 부킹 ID 기반 캐시된 상태 사용
let isPaymentCompleted = false;

if (apiData?.is_paid !== undefined) {
  // 1순위: is_paid 필드가 있으면 이것을 최우선 사용
  isPaymentCompleted = apiData.is_paid === true;
  console.log(`[DEBUG] Using is_paid field for payment status: ${isPaymentCompleted}`);
} else if (apiData?.paymented !== undefined) {
  // 2순위: paymented 필드 사용
  isPaymentCompleted = apiData.paymented === true;
  console.log(`[DEBUG] Using paymented field for payment status: ${isPaymentCompleted}`);
} else {
  // 3순위: 캐시된 상태 사용
  isPaymentCompleted = paymentStatus.get(bookId) === true;
  console.log(`[DEBUG] Using cached payment status: ${isPaymentCompleted}`);
}
```

### 2025-04-11 결제 상태 감지 로직 개선

예약 날짜 변경 시 결제 완료 상태가 false로 전달되는 문제를 해결했습니다.

**문제점:**
- 날짜가 변경된 예약의 경우 결제 정보는 유지되지만 `revenue_detail.finished` 값이 false로 설정됨
- 결제 상태 확인 우선순위 문제로 인해 실제 결제 완료된 예약이 미결제로 표시됨
- 여러 필드(`is_paid`, `revenue_detail.finished`, `payment` 객체)에서 불일치 발생

**해결 방법:**
- 결제 상태 판단 시 `is_paid` 필드를 최우선으로 확인하도록 로직 변경
- 필드 검사 우선순위 명확하게 설정: `is_paid` → `revenue_detail.finished` → `payment` 객체 존재 여부
- 디버깅 로그 추가로 결제 상태 판단 과정 추적 용이

```javascript
// 수정 전: revenue_detail.finished 필드 우선 확인
let finished = revenueDetail.finished === true || revenueDetail.finished === 'true';

// 수정 후: is_paid 필드를 최우선으로 확인
let finished = false;

// is_paid 필드가 있으면 우선 사용
if (booking.is_paid !== undefined) {
  finished = booking.is_paid === true;
  console.log(`[DEBUG] Using is_paid field for book_id ${bookId}: is_paid=${booking.is_paid}, finished=${finished}`);
} 
// is_paid가 없는 경우에만 revenue_detail.finished 사용
else if (revenueDetail.finished !== undefined) {
  finished = revenueDetail.finished === true || revenueDetail.finished === 'true';
  console.log(`[DEBUG] Using revenue_detail.finished for book_id ${bookId}: revenue_detail.finished=${revenueDetail.finished}, finished=${finished}`);
}
// payment 정보가 있으면 사용
else if (booking.payment) {
  finished = true; // payment 객체가 있다면 결제가 완료된 것으로 간주
  console.log(`[DEBUG] Using payment object existence for book_id ${bookId}: payment exists, finished=${finished}`);
}
```

### 2025-04-11 수동 로그인 후 자동 리다이렉트 비활성화

사용자가 직접 로그인한 경우에도 예약 관리 페이지로 자동 이동하는 기능을 비활성화했습니다.

**변경 내용:**
- 수동 로그인 감지 및 자동 이동 기능 비활성화
- 로그인 버튼 클릭 이벤트 감지 및 리다이렉트 코드 주석 처리
- DOM 변화 감지를 통한 자동 이동 기능 비활성화

```javascript
// 로그인 성공 시 예약 페이지로 이동
if (loginSuccess) {
  await new Promise(resolve => setTimeout(resolve, 1000));
  console.log('[INFO] call navigateToBookingPage');
  await navigateToBookingPage(page);
} else {
  // 수동 로그인 감지 및 페이지 이동 기능 추가
  // 주석 처리: 수동 로그인 후 자동 리다이렉트 비활성화
  // await setupLoginDetection(page);
  console.log('[INFO] Manual login redirect disabled - user will remain on the main dashboard after login');
}
```

### 2025-04-10 웹사이트 기본 동작 유지 및 간섭 최소화
모달 위치 조정 코드를 비활성화하고 웹사이트의 기본 동작을 유지하도록 개선했습니다.

**문제점:**
- 웹사이트에 적용한 CSS가 기존 레이아웃과 충돌
- 일반 크롬 브라우저에서는 잘 작동하는 반응형 UI가 Puppeteer에서 깨짐
- CSS 직접 주입으로 인한 사이트 스타일 오염

**해결 방법:**
- 모달 위치 조정 기능 비활성화 및 웹사이트 기본 동작 유지
- 스크롤 관련 변경사항을 최소화하여 필요한 기능만 적용
- 브라우저 설정 최적화 (사용자 에이전트, 뷰포트 설정)
- 불필요한 CSS 변경 제거

```javascript
/**
 * 모달 관련 설정을 조정하지 않는 함수 (기본 웹사이트 동작 유지)
 * @param {Object} page - Puppeteer 페이지 인스턴스
 */
const fixModalPositions = async (page) => {
  // 이 함수는 의도적으로 아무것도 하지 않습니다.
  // 기본 웹사이트 동작을 그대로 유지하기 위함입니다.
  console.log('[INFO] 모달 위치 조정이 비활성화되었습니다. 웹사이트 기본 동작을 유지합니다.');
};
```

```javascript
// 일반 브라우저처럼 동작하도록 설정
await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
```

```javascript
// 최소한의 스크롤 활성화만 적용 (다른 스타일에 영향 안 주도록)
await page.evaluate(() => {
  console.log('[Browser] 스크롤 기능을 활성화합니다.');
  
  // 기존 스크롤 요소 제거
  const existingElement = document.getElementById('scroll-force');
  if (existingElement) {
    existingElement.remove();
  }
  
  // body/html 스크롤 허용 (최소한의 변경만)
  if (document.body.style.overflow === 'hidden') {
    document.body.style.overflow = 'auto';
  }
  if (document.documentElement.style.overflow === 'hidden') {
    document.documentElement.style.overflow = 'auto';
  }
  
  // 최소한의 스크롤 요소 추가 (클릭 방해 최소화)
  const scrollForce = document.createElement('div');
  scrollForce.id = 'scroll-force';
  scrollForce.style.cssText = 'height: 1000px; width: 100%; position: relative; z-index: -1; pointer-events: none;';
  document.body.appendChild(scrollForce);
  
  console.log('[Browser] 스크롤 기능 활성화 완료');
});
```

### 2025-04-10 클릭 이벤트 및 모달 위치 개선

#### 1. 클릭 이벤트 방해 요소 최소화
예약 관리 화면에서 시간대 표를 클릭했을 때 팝업이 제대로 나타나지 않는 문제를 해결했습니다.

**문제점:**
- 스크롤 기능 개선 코드가 클릭 이벤트를 방해하는 문제 발생
- 예약 관리 화면에서 시간대 표를 클릭해도 팝업이 나타나지 않음

**해결 방법:**
- DOM 조작을 최소화하여 클릭 이벤트 방해 요소 제거
- 스크롤 요소에 `pointer-events: none`과 `z-index: -1` 적용
- CSS 스타일 간소화

```javascript
// 더 간소화된 CSS 스타일 적용 - 클릭 이벤트 방해 방지
await page.addStyleTag({
  content: `
    html, body {
      height: auto !important;
      overflow-y: auto !important;
    }
    
    /* 테이블 특별 처리 */
    .MuiTable-root, .MuiTableContainer-root, [role="grid"] {
      overflow: auto !important;
      max-height: 500px !important;
    }
    
    /* 스크롤 요소 - 최소한의 영향만 주도록 설정 */
    #scroll-force {
      height: 1000px;
      width: 100%;
      position: relative;
      display: block;
      z-index: -1;
      pointer-events: none;
    }
  `
});
```

### 2025-04-10 브라우저 화면 및 페이지 스크롤 기능 개선

#### 1. 반응형 브라우저 화면 구현
브라우저 창 크기를 화면에 맞게 조정하고 웹사이트가 올바르게 표시되도록 개선했습니다.

**변경 내용:**
- 화면 크기에 맞는 브라우저 창 자동 계산 (화면 너비의 98%, 높이의 95%)
- 뷰포트 설정 최적화로 반응형 표시 지원
- 테이블과 차트 영역의 내부 스크롤 보존

```javascript
// 화면 크기 가져오기
const { width, height } = require('electron').screen.getPrimaryDisplay().workAreaSize;
console.log(`[INFO] Detected screen size: ${width}x${height}`);

// 실제 사용할 브라우저 창 크기 계산 (작업 표시줄 등을 고려하여 약간 줄임)
const browserWidth = Math.floor(width * 0.98);
const browserHeight = Math.floor(height * 0.95);
console.log(`[INFO] Setting browser size to: ${browserWidth}x${browserHeight}`);
```

#### 2. 페이지 전체 스크롤 기능 강제 활성화
웹사이트의 모든 내용(차트, 테이블, Footer 등)을 스크롤하여 볼 수 있도록 개선했습니다.

**문제점:**
- 특히 예약 페이지(`/booking`)에서 스크롤이 작동하지 않는 문제 발생
- 테이블과 차트는 내부 스크롤이 가능하지만 페이지 전체 스크롤이 되지 않음
- Footer 영역까지 접근할 수 없는 UX 문제

**해결 방법:**
- 강제 스크롤 요소를 DOM에 삽입하여 페이지 스크롤 활성화
- CSS와 JavaScript를 결합한 스크롤 차단 요소 감지 및 수정
- 페이지 전환 시 자동으로 스크롤 기능 재적용

### 2025-04-09 로그인 후 예약 페이지 자동 이동 기능 추가

#### 1. 로그인 후 기본 경로 변경
로그인 후 기본 대시보드가 아닌 예약 관리 페이지로 자동 이동하도록 수정했습니다.

**변경 내용:**
- 자동 로그인 성공 시 예약 페이지(`/booking`)로 자동 이동
- 메인 페이지 이동 감지 시 예약 페이지로 리다이렉트 
- 수동 로그인 이벤트 감지 후 예약 페이지로 자동 이동

```javascript
/**
 * 로그인 후 예약 페이지로 자동 이동
 * @param {Object} page - Puppeteer 페이지 인스턴스
 */
const navigateToBookingPage = async (page) => {
  try {
    console.log('[INFO] Navigating to booking page...');
    await page.goto('https://owner.kimcaddie.com/booking', { waitUntil: 'networkidle2', timeout: 30000 });
    console.log('[INFO] Successfully navigated to booking page');
  } catch (error) {
    console.error(`[ERROR] Failed to navigate to booking page: ${error.message}`);
    
    // 다른 방식으로 예약 페이지로 이동 시도
    try {
      console.log('[INFO] Trying alternative navigation method...');
      await page.evaluate(() => {
        // 브라우저 콘솔에서 직접 이동
        window.location.href = 'https://owner.kimcaddie.com/booking';
      });
      
      // 페이지 로드 대기
      await page.waitForNavigation({ timeout: 10000 });
      console.log('[INFO] Alternative navigation successful');
    } catch (e) {
      console.error(`[ERROR] Alternative navigation also failed: ${e.message}`);
    }
  }
};
```

#### 2. 수동 로그인 감지 및 페이지 이동 기능 추가
API 요청을 감시하여 수동 로그인 성공 시에도 예약 페이지로 자동 이동하는 기능을 추가했습니다.

```javascript
// 페이지에 이벤트 리스너 추가
await page.evaluate(() => {
  // 네트워크 요청 감시
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const result = await originalFetch.apply(this, args);
    
    // 로그인 API 요청 감지
    if (args[0] && (args[0].includes('/api/login') || args[0].includes('/api/auth/token'))) {
      // 로그인 응답 확인
      result.clone().json().then(data => {
        if (data && (data.token || data.access_token)) {
          console.log('[Browser] Login detected, will navigate to booking page');
          
          // 잠시 대기 후 예약 페이지로 이동 (로그인 처리 완료 대기)
          setTimeout(() => {
            console.log('[Browser] Navigating to booking page after login');
            window.location.href = 'https://owner.kimcaddie.com/booking';
          }, 2000);
        }
      }).catch(e => {
        console.error('[Browser] Error checking login response:', e);
      });
    }
    
    return result;
  };
});
```

### 2025-04-08 범용 모달 감지 시스템 구현

#### 1. 모달 감지 서비스 확장
기존 취소 모달 감지 기능을 확장하여 모든 종류의 모달을 감지하고 저장하는 기능을 구현했습니다.

**기능:**
- 다양한 종류의 모달 감지 (예약 취소, 예약 요청, 전화 알림, 일반 알림)
- 모든 모달 HTML 자동 저장
- 모달 유형별 분류 및 저장 경로 구성

```javascript
// 모달 유형 분류 로직
let modalType = 'unknown';

// 1. 취소 모달 감지
if (
  modalText.includes('취소') || 
  modalText.includes('cancel') ||
  (node.querySelector('.sc-kHzJqM') && 
   node.querySelector('.sc-kHzJqM').textContent.includes('김캐디 취소 접수'))
) {
  modalType = 'cancel';
}
// 2. 예약 요청 모달 감지
else if (
  modalText.includes('예약') || 
  modalText.includes('reservation') ||
  modalText.includes('booking')
) {
  modalType = 'booking';
}
// 3. 전화 알림 모달 감지
else if (
  modalText.includes('전화') || 
  modalText.includes('call') ||
  modalText.includes('phone')
) {
  modalType = 'call';
}
// 4. 일반 알림 모달 감지
else if (
  modalText.includes('알림') || 
  modalText.includes('notification') ||
  modalText.includes('alert') ||
  modalText.includes('notice')
) {
  modalType = 'notification';
}
```

#### 2. 저장 디렉토리 구조 개선
모달 유형별로 HTML 파일을 저장하는 디렉토리 구조를 개선했습니다.

```
html_captures/
  ├── cancel/         # 취소 모달
  ├── booking/        # 예약 요청 모달
  ├── call/           # 전화 알림 모달
  ├── notification/   # 일반 알림 모달
  ├── unknown/        # 유형을 확인할 수 없는 모달
  └── full_page/      # 전체 페이지 캡처
```

#### 3. API 응답 기반 HTML 캡처 기능
중요한 API 요청/응답 시점에 HTML을 캡처하여 웹사이트 상태를 기록하는 기능을 추가했습니다.

**캡처 지점:**
- 예약 상태 변경 요청/응답 시
- 고객 정보 요청/응답 시
- 예약 목록 조회 시
- 예약 생성/변경/취소 시
- 결제 정보 업데이트 시
- 오류 발생 시

```javascript
// 예약 생성 응답을 받으면 페이지 캡처
if (modalDetectionService) {
  try {
    const responseData = await response.clone().json();
    const bookId = responseData.book_id || 'unknown';
    await modalDetectionService.captureFullPageHTML('booking_created', bookId);
  } catch (error) {
    console.error(`[ERROR] Failed to capture booking creation response: ${error.message}`);
  }
}
```

### 2025-04-08 예약 취소 감지 로직 개선

#### 1. `/owner/booking` 응답 검사 로직 비활성화
중복된 취소 API 호출 문제를 해결하기 위해 기존 취소 감지 로직을 변경했습니다.

**문제점:**
- 자동 취소 팝업 클릭 기능과 `/owner/booking` 응답을 통한 취소 감지 로직이 동시에 작동하여 중복 취소 API 호출 발생
- API에서 `ALREADY_CANCELLED` 에러 다수 발생

**해결 방법:**
- `_handleCancelingBookings` 메서드 비활성화
- `handleBookingList` 메서드에서 취소 감지 로직 호출 제거
- 취소 감지 및 처리를 자동 취소 팝업 클릭 기능으로 일원화

```javascript
// 비활성화된 _handleCancelingBookings 메서드
async _handleCancelingBookings(data, customerService) {
  console.log(`[INFO] 자동 취소 기능이 자동 팝업 클릭 방식으로 변경되었습니다. /owner/booking 응답에서 취소 예약 감지는 비활성화되었습니다.`);
  // 이 기능은 autoCancelService._clickCancelConfirmButton()로 대체되었으며,
  // 취소 팝업이 감지되면 직접 취소 버튼을 클릭하는 방식으로 변경되었습니다.
  return;
}
```

### 2025-04-08 예약 취소 자동 클릭 기능 구현

#### 1. 취소 버튼 자동 클릭 기능 구현
취소 팝업이 감지되면 자동으로 취소 확인 버튼을 클릭하는 기능을 구현했습니다.

**문제점:**
- 기존에는 취소 팝업 HTML만 캡처하고 실제 클릭은 수동으로 해야 했음
- 앱에서 취소 요청 시 웹사이트에서 수동으로 확인해야 하는 번거로움 존재

**해결 방법:**
- 취소 팝업 감지 시 자동으로 "예약 취소 확인" 버튼을 클릭
- 여러 방법으로 버튼을 찾아 안정적인, 커버리지 높은 클릭 기능 구현
- 취소 사유 자동 입력 기능 추가

#### 2. 취소 사유 자동 입력 기능
취소 팝업에서 취소 사유를 자동으로 입력하는 기능을 추가했습니다.

```javascript
// 취소 사유 텍스트 영역 찾기
const textareas = document.querySelectorAll('textarea');
let reasonTextarea = null;

for (const textarea of textareas) {
  if (textarea.getAttribute('name') === 'comment' || 
      textarea.className.includes('sc-jCDoxP')) {
    reasonTextarea = textarea;
    break;
  }
}

if (reasonTextarea) {
  // 취소 사유 입력
  reasonTextarea.value = '앱에서 자동 취소 처리됨';
  console.log('[Browser] Entered cancellation reason');
  
  // 취소 사유 변경 이벤트 발생
  const event = new Event('input', { bubbles: true });
  reasonTextarea.dispatchEvent(event);
}
```

### 2025-04-08 Puppeteer 기반 HTML 캡처 기능 구현

#### 1. Puppeteer 기반 HTML 캡처 서비스 개선
웹 브라우저 환경이 아닌 Node.js 환경에서 HTML 캡처가 가능하도록 수정했습니다.

**문제점:**
- 기존 HTML 캡처 코드는 브라우저 DOM API를 사용하여 동작하도록 설계됨
- Node.js 환경에서 실행 시 "HTML capture can only run in browser environment" 에러 발생

**해결 방법:**
- Puppeteer를 활용한 HTML 캡처 기능 구현
- 파일 시스템(fs)을 사용하여 캡처된 HTML을 로컬 파일로 저장
- `html_captures` 디렉토리에 캡처된 HTML 자동 저장

## 향후 개선 계획

1. 모달 유형별 자동 처리 로직 확장
   - 전화 알림 모달 자동 응답
   - 예약 요청 모달 자동 수락/거부
   - 일반 알림 모달 자동 닫기

2. 모달 데이터 분석 시스템 구축
   - 모달 데이터 DB 저장 및 분석
   - 모달 발생 빈도 및 패턴 분석

3. 자동 취소 기능 성공률 개선 및 모니터링 시스템 구축
4. 코드 중복 제거 및 공통 유틸리티 함수 추출
5. 일관된 로깅 시스템 구현
6. 캐시 관리 최적화