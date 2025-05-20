# API 호출 방식

이 문서는 kimcady 프로그램의 예약 관련 API 호출 방식을 설명합니다.

## 1. 예약 등록(Booking_Create) API

예약 등록 API는 두 가지 경로로 호출됩니다:

### 1.1. 점주(관리자) 예약 등록

* **감지 경로**: `/owner/booking` (POST 메서드)
* **처리 과정**:
  * `request.js` 파일의 `setupRequestHandler` 함수에서 경로와 메서드를 확인
  * 예약 정보를 파싱하고 `bookingDataMap`에 저장
  * 응답(response) 받은 후 `bookingService`에서 정보를 처리
  * `sendTo24GolfApi` 함수를 통해 'Booking_Create' 타입으로 외부 API 호출

### 1.2. 앱 사용자 예약 등록

* **감지 경로**: `/api/booking/confirm_state` (PATCH 또는 PUT 메서드)
* **처리 과정**:
  * `request.js`에서 경로와 메서드를 확인하고 상태가 'confirmed'인 경우 처리
  * 예약 정보를 `pendingBookingMap`에 저장하고 대기
  * `bookingService.js`의 `handleBookingConfirmation` 메서드에서 처리
  * 필요한 데이터 검증 후 `_createBooking` 메서드를 통해 API 호출

## 2. 예약 변경(Booking_Update) API

예약 변경 API는 예약 정보를 수정할 때 호출됩니다:

* **감지 경로**: `/booking/change_info` (PATCH 메서드)
* **처리 과정**:
  * `request.js`에서 경로와 메서드를 확인
  * URL에서 예약 ID 추출 (`extractBookingId` 함수 사용)
  * 변경된 정보를 `bookingDataMap`에 저장
  * 응답을 받은 후 `processPendingBookingUpdates` 함수에서 처리
  * `sendTo24GolfApi` 함수를 통해 'Booking_Update' 타입으로 외부 API 호출

## 3. 예약 취소(Booking_Cancel) API

예약 취소 API는 두 가지 경로로 호출됩니다:

### 3.1. 앱 사용자 예약 취소

* **감지 경로**: `/api/booking/confirm_state` (PATCH 또는 PUT 메서드, state=canceled)
* **처리 과정**:
  * `request.js`에서 경로와 메서드를 확인하고 상태가 'canceled'인 경우 처리
  * 취소 사유 추출 및 금액 정보 저장
  * `sendTo24GolfApi` 함수를 통해 'Booking_Cancel' 타입으로 외부 API 호출

### 3.2. 관리자 예약 취소

* **감지 경로**: `/booking/change_info` (PATCH 메서드, state=canceled)
* **처리 과정**:
  * `request.js`에서 경로와 메서드를 확인하고 상태가 'canceled'인 경우 처리
  * `sendTo24GolfApi` 함수를 통해 'Booking_Cancel' 타입으로 외부 API 호출
