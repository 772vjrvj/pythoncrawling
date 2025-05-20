# 결제 상태 처리 로직 문제 분석 및 수정 방안

## 문제 상황

예약 등록 API 요청 시 결제 완료 여부가 올바르게 반영되지 않는 문제가 발생했습니다. 로그 분석 결과, `revenue_detail.finished=true` 값이 존재함에도 불구하고 `is_paid=false` 값이 우선 적용되어 최종 API 호출 데이터에 `paymented: false`로 잘못 설정되는 상황이 발견되었습니다.

## 원인 분석

- `src/utils/api.js` 파일의 `sendTo24GolfApi` 함수에서 결제 상태 결정 로직이 `is_paid` 값을 최우선으로 사용하고 있습니다.
- `is_paid` 값이 `false`일 때 `revenue_detail.finished` 값이 `true`여도 무시됩니다.
- 실제로는 두 필드 중 하나라도 `true`인 경우 결제 완료로 간주해야 합니다.
- `src/handlers/response-helpers.js`에서도 `is_paid` 필드가 우선 적용되는 유사한 로직이 있어 결제 상태가 일관되지 않게 처리됩니다.

## 해결 방안

`src/utils/api.js` 파일의 `sendTo24GolfApi` 함수에서 결제 상태 결정 로직을 수정해야 합니다:
- `revenue_detail.finished` 값이 `true`면 무조건 결제 완료로 처리
- `is_paid`와 `revenue_detail.finished` 중 하나라도 `true`면 결제 완료로 간주
- 이 수정을 통해 예약 등록 및 업데이트 과정에서 결제 상태가 일관되게 처리될 것입니다.

# 결제 상태 변경 감지 문제 분석 및 해결 방안

## 문제 상황

예약의 결제 상태가 `paymentComplete: true`에서 `is_paid: false` 또는 `finished: false`로 변경되었을 때 예약 변경 API가 호출되지 않는 문제가 발생하고 있습니다. 로그 분석 결과, 시스템이 결제 상태 변경을 감지하지 못하는 것으로 확인되었습니다.

## 원인 분석

1. **필드명 불일치**: API 응답은 `paymentComplete` 필드를 사용하지만, 내부 처리는 `is_paid` 또는 `finished` 필드를 사용합니다.

2. **변경 감지 로직 문제**: 
   - 코드는 이전 상태와 현재 상태를 비교하지만, 이전 상태가 제대로 저장되지 않고 있습니다.
   - 결제 상태(`Finished`)의 변경이 감지되지 않고 있습니다.

3. **결제 상태 결정 로직 문제**:
   - `is_paid` 필드가 우선 사용되어 `revenue_detail.finished` 값의 변경이 무시됩니다.
   - 상태가 올바르게 결정되지 않아 변경 감지에 실패합니다.

4. **캐싱 및 상태 관리 문제**:
   - 이전 상태 값이 제대로 캐시되지 않거나 업데이트되지 않아 변경 감지에 실패합니다.

## 해결 방안

두 가지 주요 함수를 수정해야 합니다:

1. **src/handlers/response-helpers.js 파일의 processBookingUpdate 함수 수정**:
   - 이전 결제 상태와 현재 결제 상태를 명시적으로 비교
   - 결제 상태 결정 로직 개선: `is_paid`와 `revenue_detail.finished` 중 하나라도 true면 true로 처리
   - 결제 상태 변경 시 forceUpdate 플래그 추가하여 강제 업데이트

2. **src/utils/api.js 파일의 sendTo24GolfApi 함수 수정**:
   - forceUpdate 플래그가 설정된 경우 항상 API 호출 진행
   - 로그에 이전 결제 상태와 현재 결제 상태를 비교하여 변경 여부 기록
   - API 호출 후 결제 상태 업데이트 로직 추가

3. **src/handlers/response-helpers.js 파일의 handleBookingListingResponse 함수 수정**:
   - 결제 상태 결정 로직 일관성 유지
   - 결제 상태 변경 시 pendingUpdate에 forceUpdate 플래그 설정

## 기대 효과

1. **결제 상태 변경 감지 강화**:
   - 기존: `is_paid`만 확인하여 `revenue_detail.finished` 변경을 감지하지 못함
   - 수정 후: `is_paid` 또는 `revenue_detail.finished` 중 하나라도 변경되면 감지

2. **변경 내역 명확한 로깅**:
   - 이전 상태와 현재 상태를 명확히 비교하여 로깅

3. **강제 업데이트 메커니즘**:
   - 결제 상태 변경 시 `forceUpdate` 플래그로 강제 업데이트 수행

4. **결제 상태 결정 로직 일관성**:
   - 하나라도 `true`면 결제 완료로 처리하는 일관된 로직 적용

# HTML 캡처 위치 및 모달 자동 처리 기능 개선

## 1. HTML 캡처 위치 변경

### 문제 상황

HTML 모달 캡처 파일이 사용자의 운영체제 애플리케이션 데이터 폴더(`/Users/username/Library/Application Support/Electron/html_captures/`)에 저장되어 접근이 어려움.

### 원인 분석

`main.js` 파일에서 HTML 캡처 디렉토리를 명시적으로 Electron 애플리케이션 데이터 폴더로 설정하고 있었습니다.

### 해결 방안

캡처 디렉토리 경로를 프로젝트 루트 폴더로 변경하여 접근성을 높였습니다.
- 파일: `main.js`
- 변경 내용: `captureDir` 경로를 `app.getPath('userData')`에서 `process.cwd()`로 변경

## 2. 김캐디 즉시확정 예약 모달 자동 처리 기능 추가

### 기능 설명

"김캐디 즉시확정 예약" 모달이 감지되었을 때 자동으로 "예약 페이지 이동" 버튼을 클릭하여 사용자 경험을 개선했습니다.

### 주요 변경사항

1. **모달 감지 로직 개선**:
   - 파일: `src/services/modalDetectionService.js`
   - 함수: `_setupPuppeteerPageMonitoring` - 모달 감지 및 DOM 변화 감시 설정 개선
   - 함수: `window.__checkForModals` - 김캐디 모달 감지 및 사이드바와 구분 로직 추가

2. **모달 처리 자동화**:
   - 파일: `src/services/modalDetectionService.js`
   - 함수: `_handleBookingModal` - 모달 처리 및 버튼 클릭 로직 개선
   - 함수: `_closeBookingModal` - 모달 닫기 기능 추가 (X 버튼, 외부 클릭, ESC 키)
   - 함수: `_forceCleanupModalElements` - 모달 강제 제거 기능 추가
   - 함수: `_safeWait` - 버전 호환성을 위한 안전한 대기 함수 추가

### 버튼 클릭 전략

예약 페이지 이동 버튼을 찾기 위해 세 가지 다른 방법을 구현했습니다:

1. **클래스 선택자 사용**: `.sc-jRqOxM` 클래스를 가진 링크 요소 찾기
2. **텍스트 콘텐츠 기반**: "예약 페이지 이동" 텍스트를 포함하는 버튼 또는 링크 찾기
3. **모달 하단 영역 탐색**: `.sc-kNiUwJ` 클래스를 가진 푸터 영역에서 링크 찾기

### 모달 닫기 전략

모달을 닫기 위한 여러 방법을 순차적으로 시도합니다:

1. **상단 X 버튼 클릭**: 모달 상단의 SVG 아이콘을 찾아 클릭
2. **모달 외부 영역 클릭**: 모달 바깥 영역을 계산하여 클릭 이벤트 발생
3. **ESC 키 누르기**: 키보드 ESC 키 이벤트 발생
4. **예약 버튼 직접 클릭**: 예약 페이지 이동 버튼을 직접 클릭하여 처리
5. **DOM에서 강제 제거**: 모달 관련 요소를 DOM에서 직접 제거

### 사이드바와 모달 구분 로직

사이드바가 모달로 잘못 감지되는 문제를 해결하기 위한 로직 추가:

- 제외할 클래스 패턴 정의: `MuiDrawer-paper`, `Drawer`, `sidebar` 등
- 모달 요소의 클래스 확인 후 사이드바 관련 클래스가 포함된 경우 제외
- 실제 김캐디 즉시확정 예약 모달만 선택적으로 처리

### 페이지 새로고침 대응

페이지 새로고침 또는 네비게이션 후에도 모달 감지가 정상 작동하도록 개선:

- `domcontentloaded` 이벤트에 모달 감지 재초기화 코드 추가
- 네비게이션 후 모달 검사 수행
- 타이머를 통한 주기적 모달 확인 기능 강화

### 기대 효과

1. HTML 캡처 파일이 프로젝트 루트의 `html_captures` 폴더에 저장되어 접근성이 향상됨
2. "김캐디 즉시확정 예약" 모달이 나타나면 자동으로 예약 페이지로 이동하여 워크플로우 개선
3. 다양한 방식으로 버튼을 찾고 모달을 닫기 때문에 모달 구조가 변경되어도 안정적으로 작동
4. 사이드바와 실제 모달을 구분하여 정확한 모달 처리 가능
5. 페이지 새로고침 또는 네비게이션 후에도 모달 감지 및 처리 가능

# 모달 감지 로직 개선 및 불필요한 로그 최적화

## 문제 상황

기존 모달 감지 및 처리 로직은 다음과 같은 문제점을 가지고 있었습니다:

1. 예약 관리 페이지(`/booking`)로 이동한 후에도 불필요한 모달 감지 로직이 계속 작동
2. 불필요한 로그가 지속적으로 출력되어 콘솔이 가득 차고 중요한 로그 확인이 어려움
3. `Modal processing in progress, skipping` 메시지가 반복적으로 출력됨
4. 모달 처리 후 상태 플래그(`__modalProcessing`)가 제때 해제되지 않는 문제 발생

## 해결 방안

### 1. 디버그 모드 도입

- 파일: `src/services/modalDetectionService.js` 
- 불필요한 로그를 필터링하기 위한 디버그 모드 추가
- 중요 로그는 항상 표시하고, 디버그 목적의 세부 로그는 디버그 모드 활성화 시에만 표시

```javascript
// 클래스 생성자에 로깅 제어 플래그 추가
constructor() {
  this.debugMode = false; // 로깅 레벨 제어
}

// 디버그 모드 설정 메서드 추가
setDebugMode(enabled) {
  this.debugMode = enabled;
  console.log(`[INFO] Debug mode ${enabled ? 'enabled' : 'disabled'}`);
}
```

### 2. 조건부 로깅 구현

- 클라이언트 측 로깅 함수 구현으로 불필요한 로그 출력 최소화
- 중요 로그는 강제 출력, 일반 로그는 디버그 모드에서만 출력

```javascript
// 조건부 로깅 함수
window.__log = function(message, force = false) {
  if (window.__debugMode || force) {
    console.log(message);
  }
};
```

### 3. URL 기반 모달 감지 스킵 기능

- 예약 관리 페이지(`/booking`)에서는 모달 감지 로직을 비활성화
- 페이지 이동 감지 및 URL 기반 조건부 처리 추가

```javascript
// 페이지 URL에 따라 모달 감지 일시 중지
window.__shouldSkipModalDetection = function() {
  // 예약 페이지에서는 감지 불필요
  const isBookingPage = window.location.href.includes('/booking');
  return isBookingPage;
};
```

### 4. 타이머 관리 개선

- 모달 처리 타임아웃을 10초에서 5초로 단축하여 빠른 상태 해제
- 기존 타이머 클리어 로직 추가로 메모리 누수 방지 및 중복 타이머 방지

```javascript
// 이전 타이머 클리어
if (window.__modalProcessingTimer) {
  clearTimeout(window.__modalProcessingTimer);
}

// 새 타이머 설정 (5초로 단축)
window.__modalProcessingTimer = setTimeout(() => {
  window.__modalProcessing = false;
  window.__log('[Browser] Modal processing timeout cleared', true);
}, 5000);
```

### 5. 모달 자동 처리 개선

- 모달 처리 후 즉시 예약 페이지로 이동
- 페이지 이동 후 모달 처리 상태 초기화 로직 추가

```javascript
// 4. 예약 페이지로 직접 이동
setTimeout(() => {
  window.__log('[Browser] Navigating directly to booking page', true);
  window.location.href = 'https://owner.kimcaddie.com/booking';
  
  // 페이지 이동 후 모달 처리 상태 초기화
  setTimeout(() => {
    window.__modalProcessing = false;
    window.__lastModalHTML = '';
  }, 1000);
}, 1000);
```

## 기대 효과

1. **콘솔 로그 가독성 향상**:
   - 중요한 로그만 표시되어 문제 진단이 용이해짐
   - 디버그 모드를 통해 필요시에만 상세 로그 확인 가능

2. **시스템 부하 감소**:
   - 불필요한 모달 감지 프로세스 스킵으로 CPU 및 메모리 사용량 감소
   - 예약 관리 페이지에서 모달 감지 로직을 비활성화하여 효율성 향상

3. **상태 관리 개선**:
   - 모달 처리 플래그의 타임아웃 시간 단축으로 빠른 상태 회복
   - 기존 타이머 클리어 로직으로 메모리 누수 방지

4. **사용자 경험 향상**:
   - 불필요한 모달 감지 로직 최소화로 성능 개선
   - 실제 필요한 상황에서만 모달 감지 및 처리