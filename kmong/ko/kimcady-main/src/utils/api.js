const axios = require('axios');
const { getStoreId, API_BASE_URL } = require('../config/env');

// 최근 API 호출 시간 추적을 위한 Map
const recentApiCalls = new Map();
const API_THROTTLE_MS = 3000; // 3초 중복 호출 방지

const getAccessToken = async () => {
  const storeId = getStoreId();
  const url = `${API_BASE_URL}/auth/token/stores/${storeId}/role/singleCrawler`;
  console.log(`[Token] Attempting to fetch access token from: ${url}`);

  try {
    const response = await axios.get(url, { 
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000 // 10 seconds timeout
    });
    
    if (!response.data) {
      throw new Error('Empty token response received');
    }
    
    const accessToken = response.data;
    console.log('[Token] Successfully obtained access token:', accessToken);
    return accessToken;
  } catch (error) {
    console.error('[Token Error] Failed to obtain access token:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    }
    throw error;
  }
};

// 매장 정보 조회 함수
const getStoreInfo = async (storeId) => {
  try {
    console.log(`[Store] Fetching store information for ID: ${storeId}`);
    const url = `${API_BASE_URL}/stores/${storeId}`;
    
    const response = await axios.get(url, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000
    });
    
    if (!response.data) {
      throw new Error('Empty store data response received');
    }
    
    console.log('[Store] Successfully retrieved store information:', JSON.stringify(response.data, null, 2));
    return {
      success: true,
      data: response.data,
      name: response.data.name || '알 수 없는 매장',
      branch: response.data.branch || ''
    };
  } catch (error) {
    console.error(`[Store Error] Failed to retrieve store information for ID ${storeId}:`, error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      
      // 404 오류인 경우 매장이 존재하지 않음
      if (error.response.status === 404) {
        return {
          success: false,
          error: '존재하지 않는 매장 ID입니다.',
          code: 'NOT_FOUND'
        };
      }
    }
    
    return {
      success: false,
      error: `매장 정보 조회에 실패했습니다: ${error.message}`,
      code: 'API_ERROR'
    };
  }
};

// 24golf API에서 허용하는 필드만 추출하는 함수
const extractAllowedFields = (data) => {
  // 엄격하게 허용된 필드만 포함
  const allowedFields = [
    'externalId',
    'name',
    'phone',
    'partySize',
    'startDate',
    'endDate',
    'roomId',
    'paymented',
    'paymentAmount',
    'crawlingSite'
  ];
  
  const result = {};
  for (const field of allowedFields) {
    if (data[field] !== undefined) {
      result[field] = data[field];
    }
  }
  
  return result;
};

// ISO 문자열에서 날짜 정보만 추출
const extractDateParts = (isoString) => {
  try {
    // "2025-04-08T00:00:00" 형식에서 날짜/시간 부분 추출
    const datePart = isoString.split('T')[0]; // "2025-04-08"
    const timePart = isoString.split('T')[1]?.split('.')[0] || "00:00:00"; // "00:00:00"
    
    const [year, month, day] = datePart.split('-').map(Number);
    const [hours, minutes, seconds] = timePart.split(':').map(Number);
    
    return { year, month: month - 1, day, hours, minutes, seconds };
  } catch (e) {
    console.error(`[ERROR] Failed to parse date parts from: ${isoString}`, e);
    return null;
  }
};

// 한국 시간(KST)을 UTC로 변환하는 함수
const convertKSTtoUTC = (kstDateTimeString) => {
  if (!kstDateTimeString) return null;
  
  try {
    console.log(`[DEBUG] Original KST input: ${kstDateTimeString}`);
    
    // 시간대 표시가 있는지 확인
    const hasTimezone = kstDateTimeString.includes('+') || 
                        kstDateTimeString.includes('-') ||
                        kstDateTimeString.includes('Z');
    
    // 타임존 표시가 이미 있는 경우 (예: 2025-04-08T00:00:00+09:00)
    if (hasTimezone) {
      // Date 객체가 알아서 시간대를 처리하므로 ISO 형식으로 반환
      const date = new Date(kstDateTimeString);
      const result = date.toISOString();
      console.log(`[DEBUG] Date with timezone converted to UTC: ${result}`);
      return result;
    }
    
    // 시간대 표시가 없는 경우 (예: 2025-04-08T00:00:00)
    // 이 경우 문자열을 KST로 해석하고 UTC로 변환 (9시간 차이)
    const parts = extractDateParts(kstDateTimeString);
    if (!parts) return kstDateTimeString;
    
    // KST -> UTC 변환을 위해 9시간 빼기
    // 브라우저/Node 환경의 날짜 객체가 로컬 시간대를 사용하는 문제를 피하기 위해 
    // UTC 메서드를 명시적으로 사용
    const utcDate = new Date();
    utcDate.setUTCFullYear(parts.year);
    utcDate.setUTCMonth(parts.month);
    utcDate.setUTCDate(parts.day);
    utcDate.setUTCHours(parts.hours - 9); // KST -> UTC 변환을 위해 9시간 빼기
    utcDate.setUTCMinutes(parts.minutes);
    utcDate.setUTCSeconds(parts.seconds);
    utcDate.setUTCMilliseconds(0);
    
    const result = utcDate.toISOString();
    console.log(`[DEBUG] KST time interpreted and converted to UTC: ${result}`);
    return result;
  } catch (e) {
    console.error(`[ERROR] Failed to convert KST to UTC: ${kstDateTimeString}`, e);
    return kstDateTimeString; // 변환 실패 시 원래 값 반환
  }
};

// 특수한 경우를 위한 함수 - 값을 검사하고 데이터 형태에 따라 적절히 처리
const correctTimeData = (dateTimeString) => {
  if (!dateTimeString) return null;
  
  try {
    console.log(`[DEBUG] Checking time data format: ${dateTimeString}`);
    
    // 시간대 표시가 있는지 확인
    const hasTimezone = dateTimeString.includes('+') || 
                        dateTimeString.includes('-') ||
                        dateTimeString.includes('Z');
                      
    // 시간대 표시가 있는 경우 그대로 반환
    if (hasTimezone) {
      console.log(`[DEBUG] Time data already has timezone info: ${dateTimeString}`);
      return dateTimeString;
    }
    
    // 시간대 표시가 없는 경우 KST로 가정하고 UTC로 변환
    return convertKSTtoUTC(dateTimeString);
  } catch (e) {
    console.error(`[ERROR] Failed to correct time data: ${dateTimeString}`, e);
    return dateTimeString;
  }
};

// 시간 문자열에서 시간대 정보 추출
const getTimezoneFromString = (dateTimeString) => {
  if (dateTimeString.includes('+09:00')) {
    return '+09:00';
  } else if (dateTimeString.includes('Z')) {
    return 'Z';
  }
  return '';
};

// 문자열 형식의 날짜가 적절한지 검사
const isValidDateString = (dateString) => {
  if (!dateString) return false;
  if (typeof dateString !== 'string') return false;
  
  // ISO 형식이나 일반 날짜 형식인지 확인
  const date = new Date(dateString);
  return !isNaN(date.getTime());
};

// 오래된 API 호출 기록 정리 함수
const cleanupOldApiCalls = () => {
  const now = Date.now();
  const THIRTY_MINUTES = 30 * 60 * 1000; // 30분
  let cleanedCount = 0;
  
  for (const [key, timestamp] of recentApiCalls.entries()) {
    if (now - timestamp > THIRTY_MINUTES) {
      recentApiCalls.delete(key);
      cleanedCount++;
    }
  }
  
  if (cleanedCount > 0) {
    console.log(`[INFO] Cleaned up ${cleanedCount} old API call records, remaining: ${recentApiCalls.size}`);
  }
};

const sendTo24GolfApi = async (type, url, payload, apiData, accessToken, processedBookings = new Set(), paymentAmounts = new Map(), paymentStatus = new Map()) => {
    if (!accessToken) {
      console.error(`[API Error] Cannot send ${type}: Missing access token`);
      try {
        accessToken = await getAccessToken();
      } catch (e) {
        console.error(`[API Error] Failed to refresh token: ${e.message}`);
        return;
      }
    }
  
    const bookId = apiData?.externalId || payload?.externalId || 'unknown';
  
    // 중복 예약 체크 - 기존 코드
    if (type === 'Booking_Create' && processedBookings.has(bookId)) {
      console.log(`[INFO] Skipping duplicate Booking_Create for book_id: ${bookId} - already in processed set`);
      return;
    }
    
    // 신규 추가: 10초 이내 중복 호출 방지 기능
    if (type === 'Booking_Create') {
      // API 호출 키 생성 (타입 + 예약 ID)
      const apiCallKey = `${type}_${bookId}`;
      const now = Date.now();
      const lastCallTime = recentApiCalls.get(apiCallKey);
      
      // 최근 10초 이내에 동일한 API 호출이 있었는지 확인
    //   if (lastCallTime && (now - lastCallTime < API_THROTTLE_MS)) {
    //     const secondsAgo = Math.round((now - lastCallTime) / 1000);
    //     console.log(`[INFO] Throttling ${type} for book_id: ${bookId} - last call was ${secondsAgo}s ago (< ${API_THROTTLE_MS/1000}s threshold)`);
    //     return; // 10초 내 중복 호출 방지
    //   }
      
      // 현재 API 호출 시간 기록
      recentApiCalls.set(apiCallKey, now);
      console.log(`[INFO] Recording API call time for ${apiCallKey}`);
      
      // 주기적으로 오래된 API 호출 기록 정리 (1/10 확률로 실행)
      if (Math.random() < 0.1) {
        cleanupOldApiCalls();
      }
    }
  
    // 결제 정보 설정
    let paymentAmount = apiData?.paymentAmount || paymentAmounts.get(bookId) || 0;
    
    let isPaymentCompleted = false;
    let paymentStatusSource = '알 수 없음';

    // revenue_detail.finished 값이 true면 무조건 결제 완료로 처리
    if (payload?.revenue_detail?.finished === true) {
      isPaymentCompleted = true;
      paymentStatusSource = 'payload.revenue_detail.finished';
      console.log(`[DEBUG] 결제 상태 결정: payload.revenue_detail.finished=true (최우선순위)`);
    }
    // 또는 is_paid와 revenue_detail.finished 중 하나라도 true면 결제 완료로 간주
    else if ((payload?.is_paid === true) || (payload?.revenue_detail?.finished === true)) {
      isPaymentCompleted = true;
      paymentStatusSource = 'payload.is_paid 또는 payload.revenue_detail.finished';
      console.log(`[DEBUG] 결제 상태 결정: is_paid=${payload?.is_paid}, revenue_detail.finished=${payload?.revenue_detail?.finished} (우선순위 1)`);
    }
    // apiData도 같은 로직 적용
    else if ((apiData?.is_paid === true) || (apiData?.revenue_detail?.finished === true)) {
      isPaymentCompleted = true;
      paymentStatusSource = 'apiData.is_paid 또는 apiData.revenue_detail.finished';
      console.log(`[DEBUG] 결제 상태 결정: is_paid=${apiData?.is_paid}, revenue_detail.finished=${apiData?.revenue_detail?.finished} (우선순위 2)`);
    }
    // 3. apiData에 paymented 값이 있는지 확인
    else if (apiData?.paymented !== undefined) {
      isPaymentCompleted = apiData.paymented === true;
      paymentStatusSource = 'apiData.paymented';
      console.log(`[DEBUG] 결제 상태 결정: apiData.paymented=${apiData.paymented} (우선순위 3)`);
    }
    // 4. 캐시된 상태 사용
    else {
      isPaymentCompleted = paymentStatus.get(bookId) === true;
      paymentStatusSource = 'cached';
      console.log(`[DEBUG] 결제 상태 결정: cached=${paymentStatus.get(bookId)} (우선순위 4)`);
    }
  
    console.log(`[DEBUG] 최종 결제 상태 결정: ${isPaymentCompleted} (출처: ${paymentStatusSource})`);
    console.log(`[DEBUG] Payment info for ${bookId} - Amount: ${paymentAmount}, Completed: ${isPaymentCompleted}`);
  
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${type} - URL: ${url} - Payload:`, JSON.stringify(payload, null, 2));
    console.log(`[DEBUG] Original apiData (before corrections):`, JSON.stringify(apiData, null, 2));
  
    const headers = { 'Authorization': `Bearer ${accessToken}`, 'Content-Type': 'application/json' };
    const storeId = getStoreId();
  
    let apiMethod, apiUrl, finalApiData;
    if (type === 'Booking_Create') {
      apiMethod = 'POST';
      apiUrl = `${API_BASE_URL}/stores/${storeId}/reservation/crawl`;
      
      // 시간 데이터 보정
      if (apiData.startDate) {
        // 이전 시간 저장
        const originalStartDate = apiData.startDate;
        // 시간 형식에 따라 적절히 처리 
        apiData.startDate = correctTimeData(apiData.startDate);
        console.log(`[DEBUG] StartDate corrected: ${originalStartDate} -> ${apiData.startDate}`);
      }
      
      if (apiData.endDate) {
        // 이전 시간 저장
        const originalEndDate = apiData.endDate;
        // 시간 형식에 따라 적절히 처리
        apiData.endDate = correctTimeData(apiData.endDate);
        console.log(`[DEBUG] EndDate corrected: ${originalEndDate} -> ${apiData.endDate}`);
      }
      
      // 최종 apiData에 결제 상태 설정: 계산된 isPaymentCompleted 값 사용
      apiData.paymented = isPaymentCompleted;
      
      finalApiData = extractAllowedFields(apiData);
    } else if (type === 'Booking_Update') {
      apiMethod = 'PATCH';
      apiUrl = `${API_BASE_URL}/stores/${storeId}/reservation/crawl`;
      
      // 시간 데이터 보정 (업데이트할 때도 동일하게 적용)
      if (apiData.startDate) {
        const originalStartDate = apiData.startDate;
        apiData.startDate = correctTimeData(apiData.startDate);
        console.log(`[DEBUG] StartDate corrected for update: ${originalStartDate} -> ${apiData.startDate}`);
      }
      
      if (apiData.endDate) {
        const originalEndDate = apiData.endDate;
        apiData.endDate = correctTimeData(apiData.endDate);
        console.log(`[DEBUG] EndDate corrected for update: ${originalEndDate} -> ${apiData.endDate}`);
      }
      
      // 최종 apiData에 결제 상태 설정: 계산된 isPaymentCompleted 값 사용
      finalApiData = {
        ...extractAllowedFields(apiData),
        paymented: isPaymentCompleted,
        paymentAmount: paymentAmount
      };
    } else if (type === 'Booking_Cancel') {
      apiMethod = 'DELETE';
      apiUrl = `${API_BASE_URL}/stores/${storeId}/reservation/crawl`;
      
      // cancelled_by가 'M'인 경우 공백으로 처리
      let cancelReason = '';
      if (payload.canceled_by && payload.canceled_by !== 'M') {
        cancelReason = payload.canceled_by;
        console.log(`[DEBUG] 취소 사유가 있고 'M'이 아닙니다: ${cancelReason}`);
      } else {
        console.log(`[DEBUG] 취소 사유가 'M'이거나 없어서 공백으로 설정합니다.`);
      }
      
      finalApiData = { 
        externalId: bookId, 
        crawlingSite: 'KimCaddie', 
        reason: cancelReason 
      };
    } else {
      console.log(`[WARN] Unknown type: ${type}, skipping API call`);
      return;
    }
  
    console.log(`[DEBUG] Final ${type} API data:`, JSON.stringify(finalApiData, null, 2));
  
    try {
      console.log(`[API Request] Sending ${type} to ${apiUrl}`);
      let apiResponse;
  
      if (apiMethod === 'DELETE') {
        apiResponse = await axios.delete(apiUrl, { 
          headers, 
          data: finalApiData,
          timeout: 10000
        });
      } else {
        apiResponse = await axios({ 
          method: apiMethod, 
          url: apiUrl, 
          headers, 
          data: finalApiData,
          timeout: 10000
        });
      }
  
      console.log(`[API] Successfully sent ${type}: ${apiResponse.status}`);
      console.log(`[API] Response data:`, JSON.stringify(apiResponse.data, null, 2));
  
      if (type === 'Booking_Create') {
        processedBookings.add(bookId);

        // 추가: 전역 집합에도 등록 (이미 생성된 예약으로 표시)
        if (!global.alreadyCreatedBookings) {
            global.alreadyCreatedBookings = new Set();
        }
        global.alreadyCreatedBookings.add(bookId);
        console.log(`[INFO] 예약 ID ${bookId}를 전역 등록 집합에 추가`);
        
        // 일정 시간 후 제거 (중복 방지를 위한 안전장치)
        setTimeout(() => {
            if (global.alreadyCreatedBookings && global.alreadyCreatedBookings.has(bookId)) {
                global.alreadyCreatedBookings.delete(bookId);
                console.log(`[INFO] 예약 ID ${bookId}를 전역 등록 집합에서 제거 (60초 타임아웃)`);
            }
        }, 60000); // 60초 후 제거

      }
  
      return apiResponse.data;
    } catch (error) {
      console.error(`[API Error] Failed to send ${type}: ${error.message}`);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
      }
  
      if (error.response && error.response.status === 401) {
        console.log('[API] Token might be expired, attempting to refresh...');
        try {
          const newToken = await getAccessToken();
          return sendTo24GolfApi(type, url, payload, apiData, newToken, processedBookings, paymentAmounts, paymentStatus);
        } catch (tokenError) {
          console.error(`[API Error] Failed to refresh token: ${tokenError.message}`);
        }
      }
    }
  };

// Helper function to calculate end time (1 hour after start time)
const calculateEndTime = (startTime) => {
  if (!startTime || startTime.includes('undefined')) {
    console.log(`[WARN] Invalid start time for calculation: ${startTime}`);
    return new Date().toISOString(); // UTC 반환
  }
  
  try {
    const date = new Date(startTime);
    date.setHours(date.getHours() + 1);
    return date.toISOString(); // UTC 형식으로 반환 ('Z' 포함)
  } catch (e) {
    console.error(`[ERROR] Failed to calculate end time from: ${startTime}`);
    return new Date().toISOString(); // UTC 반환
  }
};

module.exports = { getAccessToken, sendTo24GolfApi, getStoreInfo, convertKSTtoUTC };