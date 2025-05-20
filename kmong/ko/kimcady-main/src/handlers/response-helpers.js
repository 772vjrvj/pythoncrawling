const { sendTo24GolfApi, getAccessToken } = require('../utils/api');

// 외부에서 처리된 예약 ID 추적용 집합
const processedBookingIds = new Set();
// 예약 생성 진행 중인 ID를 추적하는 집합
const pendingCreateBookingIds = new Set();
// 클라이언트에서 설정한 결제 금액을 보존하기 위한 새로운 맵
const originalPaymentAmounts = new Map();
// 처리 중인 업데이트를 추적하는 집합 (중복 호출 방지)
const processingUpdates = new Set();

// 보류 중인 모든 예약 업데이트 처리
const processPendingBookingUpdates = async (accessToken, maps) => {
  const { bookingDataMap, requestMap } = maps;
  
  console.log('[INFO] Processing any pending booking updates after getting booking data');
  
  // 처리할 pendingUpdate 항목들의 키 목록 생성 (순회 중 삭제를 위해)
  const pendingUpdateKeys = Array.from(bookingDataMap.keys())
    .filter(key => key.startsWith('pendingUpdate_') && 
           bookingDataMap.get(key).type === 'Booking_Update_Pending' && 
           !bookingDataMap.get(key).processed); // 이미 처리 중인 항목 필터링
  
  console.log(`[INFO] Found ${pendingUpdateKeys.length} pending update(s) to process`);
  
  for (const key of pendingUpdateKeys) {
    const data = bookingDataMap.get(key);
    const bookId = key.replace('pendingUpdate_', '');
    
    // 이미 처리된 예약인지 확인
    if (processedBookingIds.has(bookId)) {
      console.log(`[INFO] Skipping already processed booking update for ${bookId}`);
      bookingDataMap.delete(key); // 이미 처리된 항목은 제거
      continue;
    }
    
    // 이미 처리 중인 업데이트인지 확인 (중복 호출 방지)
    if (processingUpdates.has(bookId)) {
      console.log(`[INFO] Skipping update for booking ${bookId} as it's currently being processed`);
      continue;
    }
    
    // 진행 중인 예약 생성이 있는지 확인 - 있으면 처리하지 않음
    if (pendingCreateBookingIds.has(bookId)) {
      console.log(`[INFO] Skipping update for booking ${bookId} as it's being created`);
      continue;
    }
    
    console.log(`[INFO] Found pending update for book_id ${bookId}`);
    
    let revenueUpdated = false;
    for (const [revKey, revData] of requestMap.entries()) {
      if (revKey.startsWith('revenueUpdate_') && revData.bookId === bookId && 
          (Date.now() - revData.timestamp) < 60000) { 
        revenueUpdated = true;
        break;
      }
    }
    
    try {
      console.log(`[INFO] Processing pending booking update for book_id ${bookId}${revenueUpdated ? ' with updated revenue data' : ''}`);
      
      // 처리 중으로 표시
      processingUpdates.add(bookId);
      // 처리 중 상태로 업데이트
      bookingDataMap.set(key, { ...data, processed: true });
      
      await processBookingUpdate(data.url, data.payload, accessToken, maps);
      
      // 성공적으로 처리 완료 후 맵에서 제거
      bookingDataMap.delete(key);
    } catch (error) {
      console.error(`[ERROR] Failed to process pending booking update for ${bookId}: ${error.message}`);
      // 에러 발생 시 processed 플래그 초기화하여 재시도 가능하게 함
      if (bookingDataMap.has(key)) {
        bookingDataMap.set(key, { ...data, processed: false });
      }
    } finally {
      // 처리 중 상태 해제
      processingUpdates.delete(bookId);
    }
  }
  
  // 새로 추가: 결제 정보만 업데이트된 예약 처리
  console.log('[INFO] Processing bookings with updated payment information');
  const { paymentAmounts, paymentStatus, bookIdToIdxMap } = maps;
  const processedIds = new Set();
  
  // 최근 결제 정보 업데이트 확인 (revenueUpdate_로 시작하는 키)
  for (const [key, data] of requestMap.entries()) {
    if (key.startsWith('revenueUpdate_') && data.bookId && !processedIds.has(data.bookId)) {
      const bookId = data.bookId;
      
      // 이미 처리된 예약인지 확인
      if (processedBookingIds.has(bookId)) {
        console.log(`[INFO] Skipping already processed payment update for ${bookId}`);
        continue;
      }
      
      // 중요: 예약 생성 중인 경우 스킵 (새로 추가)
      if (pendingCreateBookingIds.has(bookId)) {
        console.log(`[INFO] Skipping payment update for ${bookId} as it's being created`);
        continue;
      }
      
      // 이미 처리 중인지 확인
      if (processingUpdates.has(bookId)) {
        console.log(`[INFO] Skipping payment update for ${bookId} as it's currently being processed`);
        continue;
      }
      
      // 생성된지 1분 이내의 예약은 스킵 (새로 생성된 예약은 이미 최신 결제 정보 포함)
      const bookingData = bookingDataMap.get(bookId);
      if (bookingData && (Date.now() - bookingData.timestamp < 60000)) {
        console.log(`[INFO] Skipping payment update for ${bookId} as it was recently created`);
        continue;
      }
      
      // 중요: 원본 결제 금액이 있는 경우 그것을 사용
      let amount = originalPaymentAmounts.has(bookId) 
        ? originalPaymentAmounts.get(bookId) 
        : (data.amount || 0);
        
      const finished = data.finished || false;
      const timestamp = data.timestamp || 0;
      
      // 최근 5분 이내의 업데이트만 처리 (오래된 데이터는 무시)
      if ((Date.now() - timestamp) < 300000) {
        console.log(`[INFO] Processing payment update for book_id ${bookId}: amount=${amount}, finished=${finished}`);
        
        /*
        // 처리 중으로 표시
        processingUpdates.add(bookId);
        
        try {
          // 업데이트 페이로드 생성
          const payload = {
            externalId: bookId,
            paymentAmount: amount,
            paymented: finished
          };
          
          // API 호출
          let currentToken = accessToken;
          if (!currentToken) {
            currentToken = await getAccessToken();
          }
          
          await sendTo24GolfApi(
            'Booking_Update', 
            `payment_update_${bookId}`, 
            { externalId: bookId },
            payload, 
            currentToken, 
            null,
            paymentAmounts, 
            paymentStatus
          );
          
          console.log(`[INFO] Successfully updated payment for book_id ${bookId}`);
          processedIds.add(bookId);
          processedBookingIds.add(bookId); // 처리 완료 표시
          
          // 처리 완료 후 맵에서 제거
          requestMap.delete(key);
        } catch (error) {
          console.error(`[ERROR] Failed to update payment for book_id ${bookId}: ${error.message}`);
        } finally {
          // 처리 중 상태 해제
          processingUpdates.delete(bookId);
        }
        */
      }
    }
  }
};


const processBookingUpdate = async (url, payload, accessToken, maps) => {
  const { processedBookings, paymentAmounts, paymentStatus, bookingDataCache } = maps;
  const bookId = payload.externalId;
  
  if (!bookId) {
    console.error('[ERROR] Missing booking ID in payload');
    return;
  }
  
  // 이미 처리된 예약인지 확인
  if (processedBookingIds.has(bookId)) {
    console.log(`[INFO] Skipping already processed booking update for ${bookId}`);
    return;
  }
  
  // 예약 생성 중인 경우 스킵
  if (pendingCreateBookingIds.has(bookId)) {
    console.log(`[INFO] Skipping update for booking ${bookId} as it's being created`);
    return;
  }
  
  console.log(`[INFO] Processing Booking_Update for book_id: ${bookId}`);
  
  // 기존 결제 상태 저장 (비교용)
  const prevPaymentStatus = paymentStatus.get(bookId);
  console.log(`[DEBUG] Previous payment status for ${bookId}: ${prevPaymentStatus}`);
  
  // 캐시된 예약 정보 확인
  const cachedBooking = bookingDataCache?.data?.results?.find(b => b.book_id === bookId);
  const apiData = { ...payload }; // 기본 payload 복사
  
  // 결제 정보 확인 로직
  let isPaymentCompleted = false;
  
  if (cachedBooking) {
    console.log(`[DEBUG] Found cached booking data for ${bookId}`);

    // revenue_detail.finished 값을 명시적으로 로깅
    if (cachedBooking.revenue_detail && cachedBooking.revenue_detail.finished !== undefined) {
      console.log(`[DEBUG] Found revenue_detail.finished=${cachedBooking.revenue_detail.finished} for ${bookId}`);
    }

    // 결제 상태 결정 로직 개선 - revenue_detail.finished가 명시적으로 true인 경우 우선 적용
    if (cachedBooking.revenue_detail?.finished === true || 
        cachedBooking.revenue_detail?.finished === 'true') {
      isPaymentCompleted = true;
      console.log(`[DEBUG] Update - Using revenue_detail.finished=true for book_id ${bookId}`);
    } else if (cachedBooking.is_paid === true) {
      isPaymentCompleted = true;
      console.log(`[DEBUG] Update - Using is_paid=true for book_id ${bookId}`);
    } else if (cachedBooking.payment) {
      isPaymentCompleted = true;
      console.log(`[DEBUG] Update - Using payment object existence for book_id ${bookId}`);
    } else {
      console.log(`[DEBUG] Update - No payment indicators found for book_id ${bookId}, finished=${isPaymentCompleted}`);
    }

    // 금액 정보 추가
    if (cachedBooking.amount) {
      apiData.paymentAmount = parseInt(cachedBooking.amount, 10);
      console.log(`[DEBUG] Using amount=${apiData.paymentAmount} from cached booking for ${bookId}`);
    }
    
    // 결제 상태 설정
    apiData.paymented = isPaymentCompleted;
  }
  
  // 원본 결제 금액 사용
  let currentAmount = originalPaymentAmounts.has(bookId)
    ? originalPaymentAmounts.get(bookId)
    : (paymentAmounts.get(bookId) || 0);
    
  // 최종 결제 상태 값과 이전 상태를 비교하여 변경 여부 확인
  const prevStatus = !!prevPaymentStatus;
  const currentStatus = !!isPaymentCompleted;
  const paymentStatusChanged = prevStatus !== currentStatus;
  
  console.log(`[INFO] Final payment values for book_id ${bookId}: amount=${currentAmount}, finished=${currentStatus}, paymentStatusChanged=${paymentStatusChanged}`);
  
  // 이전 API 호출 기록 확인
  const updateKey = `update_${bookId}`;
  const lastData = maps.processedApiCallMap ? maps.processedApiCallMap.get(updateKey) || {} : {};
  
  // 필드 변경 감지 로직
  const fieldsToCheck = {
    'Name': apiData.name,
    'Amount': currentAmount, 
    'Finished': currentStatus,
    'StartDate': apiData.startDate,
    'EndDate': apiData.endDate,
    'Person': apiData.partySize,
    'RoomId': apiData.roomId,
    'ForceUpdate': paymentStatusChanged  // 결제 상태 변경 감지용 플래그
  };
  
  console.log(`[DEBUG] Change detection for ${bookId}:`);
  let hasChanges = false;
  
  // 실제 변경 여부 정확히 감지하도록 수정
  Object.entries(fieldsToCheck).forEach(([field, value]) => {
    // ForceUpdate는 특수 처리
    if (field === 'ForceUpdate') {
      if (value === true) {
        hasChanges = true;
        console.log(`              ${field}: ${value} (Changed: ${value})`);
      }
      return;
    }
    
    // 이전 값과 실제로 다른 경우만 변경으로 감지 (undefined 검사 추가)
    const previousValue = lastData[field.toLowerCase()];
    const changed = value !== undefined && previousValue !== undefined && previousValue !== value;
    console.log(`              ${field}: ${previousValue} -> ${value} (Changed: ${changed})`);
    if (changed) hasChanges = true;
  });
  
  if (hasChanges || paymentStatusChanged) {
    console.log(`[INFO] Changes detected for Booking_Update of book_id: ${bookId}, proceeding with update`);
    
    let currentToken = accessToken;
    if (!currentToken) {
      try {
        currentToken = await getAccessToken();
      } catch (error) {
        console.error(`[ERROR] Failed to refresh token for Booking_Update: ${error.message}`);
        return;
      }
    }
    
    // 중요: 결제 상태 변경이 있을 경우, 강제로 paymented 값 설정
    if (paymentStatusChanged) {
      console.log(`[INFO] Setting explicit paymented=${currentStatus} due to payment status change`);
      apiData.paymented = currentStatus;
    }
    
    await sendTo24GolfApi(
      'Booking_Update', 
      url, 
      payload, 
      apiData, 
      currentToken, 
      processedBookings, 
      paymentAmounts, 
      paymentStatus
    );
    
    // 성공적인 API 호출 후 상태 업데이트
    paymentStatus.set(bookId, currentStatus);
    console.log(`[INFO] Updated paymentStatus map for ${bookId}: ${currentStatus}`);
    
    // 처리된 API 호출 기록 업데이트
    if (maps.processedApiCallMap) {
      maps.processedApiCallMap.set(updateKey, {
        timestamp: Date.now(),
        processed: true,
        amount: currentAmount,
        finished: currentStatus,
        startdate: apiData.startDate,
        enddate: apiData.endDate,
        person: apiData.partySize,
        roomid: apiData.roomId,
        name: apiData.name
      });
    }
    
    // 처리 완료 표시
    processedBookingIds.add(bookId);
  } else {
    console.log(`[INFO] No changes detected for Booking_Update of book_id: ${bookId}, skipping`);
  }
  
  console.log(`[INFO] Processed Booking_Update for book_id ${bookId}`);
};

// book ID 찾기 (revenue ID 또는 book_idx로)
const findBookIdByRevenueIdOrBookIdx = (revenueId, bookIdx, maps) => {
  const { revenueToBookingMap, bookIdToIdxMap } = maps;
  
  // 먼저 revenue ID로 찾기
  let bookId = revenueToBookingMap.get(revenueId);
  if (bookId) {
    return bookId;
  }
  
  // 없으면 book_idx로 찾기
  if (bookIdx) {
    const entries = Array.from(bookIdToIdxMap.entries());
    const match = entries.find(([, idx]) => idx === bookIdx);
    if (match) {
      return match[0];  // book ID
    }
  }
  
  return null;
};

const extractRevenueId = (url) => {
  try {
    const match = url.match(/\/owner\/revenue\/(\\d+)\//);
    if (match && match[1]) {
      return parseInt(match[1], 10);
    }
  } catch (err) {
    console.error(`[ERROR] Failed to extract revenue ID from URL: ${url}`);
  }
  return null;
};

const handleBookingListingResponse = async (response, maps) => {
  const { paymentAmounts, paymentStatus, bookIdToIdxMap, revenueToBookingMap, requestMap, bookingDataCache } = maps;
  
  try {
    const responseBody = await response.json();
    console.log(`[DEBUG] /owner/booking/ response received, count: ${responseBody.count || 0}`);

    // 중요: 받은 응답을 bookingDataCache에 저장
    if (bookingDataCache) {
      bookingDataCache.data = responseBody;
      bookingDataCache.timestamp = Date.now();
    }

    if (!responseBody.results || !Array.isArray(responseBody.results)) {
      console.log(`[WARN] Unexpected booking list response format:`, JSON.stringify(responseBody, null, 2));
      return;
    }

    
    for (const booking of responseBody.results) {
      if (!booking.book_id) {
        console.log(`[WARN] Booking without book_id in response`);
        continue;
      }

      const bookId = booking.book_id;
      const bookIdx = booking.idx?.toString() || '';
      const revenueId = booking.revenue;
      
      
      const revenueDetail = booking.revenue_detail || {};
      const serverAmount = revenueDetail.amount || booking.amount || 0;
      
      // 수정: 결제 상태 판단 로직 변경 - is_paid 우선 확인
      let finished = false;
      
      // 1순위: is_paid 필드 확인
      if (booking.is_paid !== undefined) {
        finished = booking.is_paid === true;
        console.log(`[DEBUG] Using is_paid field for book_id ${bookId}: is_paid=${booking.is_paid}, finished=${finished}`);
      }
      // 2순위: revenue_detail.finished 필드 확인
      else if (revenueDetail.finished !== undefined) {
        finished = revenueDetail.finished === true || revenueDetail.finished === 'true';
        console.log(`[DEBUG] Using revenue_detail.finished for book_id ${bookId}: revenue_detail.finished=${revenueDetail.finished}, finished=${finished}`);
      }
      // 3순위: payment 객체 존재 여부 확인
      else if (booking.payment) {
        finished = true; // payment 객체가 있으면 결제 완료로 간주
        console.log(`[DEBUG] Using payment object existence for book_id ${bookId}: payment exists, finished=${finished}`);
      }
      
      // 로그 추가
      if (booking.payment) {
        console.log(`[DEBUG] Payment object exists for ${bookId}`);
      }
      if (booking.is_paid !== undefined) {
        console.log(`[DEBUG] is_paid value for ${bookId}: ${booking.is_paid}`);
      }
      if (revenueDetail.finished !== undefined) {
        console.log(`[DEBUG] revenue_detail.finished value for ${bookId}: ${revenueDetail.finished}`);
      }

      if (revenueId) {
        revenueToBookingMap.set(revenueId, bookId);
      }
      bookIdToIdxMap.set(bookId, bookIdx);
      
      
      const tmpRevenueKey = `revenueUpdate_${revenueId}`;
      const pendingRevenue = requestMap.get(tmpRevenueKey);
      
      // 중요: 진행 중인 예약에 대해서는 서버 금액이 아닌 클라이언트 금액 사용
      const isNewBooking = pendingCreateBookingIds.has(bookId);
      let finalAmount = serverAmount;
      
      if (isNewBooking && originalPaymentAmounts.has(bookId)) {
        // 새 예약이고 원본 금액이 있으면 해당 금액 사용
        finalAmount = originalPaymentAmounts.get(bookId);
        console.log(`[INFO] Using original client amount ${finalAmount} for new booking ${bookId} instead of server amount ${serverAmount}`);
      } else if (pendingRevenue) {
        console.log(`[INFO] Found pending revenue update for book_id ${bookId} (revenue ID ${revenueId}): amount=${pendingRevenue.amount}, finished=${pendingRevenue.finished}`);
        
        
        finalAmount = pendingRevenue.amount;
        paymentAmounts.set(bookId, finalAmount);
        paymentStatus.set(bookId, pendingRevenue.finished);
        
        // 중요: 이제 book_idx와 bookId를 연결하여 저장
        pendingRevenue.bookId = bookId;
        requestMap.set(tmpRevenueKey, pendingRevenue);
      } else {
        // 기존 예약이고 원본 금액이 없으면 서버 금액 사용
        // 단, 예약 생성 중인 경우에는 금액 업데이트 하지 않음
        if (!isNewBooking) {
          paymentAmounts.set(bookId, parseInt(serverAmount, 10) || 0);
          paymentStatus.set(bookId, finished);
        }
      }

      console.log(`[INFO] Mapped revenue ${revenueId} to book_id ${bookId}, amount: ${finalAmount}, finished: ${paymentStatus.get(bookId) || false}, idx: ${bookIdx}`);
      
      // 중요: book_idx로도 매핑 저장 (향후 결제 정보 업데이트에 필요)
      if (bookIdx) {
        requestMap.set(`bookIdx_${bookIdx}`, { bookId, timestamp: Date.now() });
      }
      
      // bookIdx와 관련된 결제 정보 업데이트가 있는지 확인
      const paymentUpdateKey = `paymentUpdate_${bookIdx}`;
      const paymentInfo = requestMap.get(paymentUpdateKey);
      
      if (paymentInfo && paymentInfo.processed === false) {
        console.log(`[INFO] Found matching book_id ${bookId} for book_idx ${bookIdx} in pending payment update`);
        
        // revenueUpdate 생성 또는 업데이트
        const revenueKey = `revenueUpdate_${paymentInfo.revenueId || 'unknown'}`;
        
        // 중요: 예약 생성 중인 경우에는 원본 금액 사용
        const updateAmount = isNewBooking && originalPaymentAmounts.has(bookId)
          ? originalPaymentAmounts.get(bookId)
          : paymentInfo.amount;
        
        requestMap.set(revenueKey, {
          bookId,
          bookIdx,
          revenueId: paymentInfo.revenueId,
          amount: updateAmount,
          finished: paymentInfo.finished,
          timestamp: Date.now()
        });
        
        // 처리 표시
        paymentInfo.processed = true;
        paymentInfo.bookId = bookId;
        requestMap.set(paymentUpdateKey, paymentInfo);
        
        console.log(`[INFO] Created/updated revenue update for book_id ${bookId}: amount=${updateAmount}, finished=${paymentInfo.finished}`);
      }
    }
    
    // 중요: 여기서 processPendingBookingUpdates 호출 제거
    // 이 부분이 중복 호출의 주요 원인이었으므로 반드시 제거해야 함
    // processPendingBookingUpdates(accessToken, maps);
  } catch (e) {
    console.error(`[ERROR] Failed to parse /owner/booking/ response: ${e.message}`);
  }
};

// 새 함수: 보류 중인 결제 정보 처리
const processPendingPaymentUpdates = (maps) => {
  const { requestMap, bookIdToIdxMap } = maps;
  
  // 모든 결제 정보 업데이트 찾기
  for (const [key, data] of requestMap.entries()) {
    // book_idx를 기반으로 한 결제 정보 업데이트 검색
    if (key.startsWith('paymentUpdate_') && data.bookIdx && !data.processed) {
      const bookIdx = data.bookIdx;
      
      // bookIdx를 통해 bookId 찾기
      let bookId = null;
      for (const [id, idx] of bookIdToIdxMap.entries()) {
        if (idx === bookIdx) {
          bookId = id;
          break;
        }
      }
      
      if (bookId) {
        console.log(`[INFO] Found matching book_id ${bookId} for book_idx ${bookIdx} in pending payment update`);
        
        // 예약 생성 중인지 확인
        if (pendingCreateBookingIds.has(bookId)) {
          console.log(`[INFO] Skipping payment update for ${bookId} as it's being created`);
          continue;
        }
        
        // 해당 bookId로 revenueUpdate_를 생성하거나 업데이트
        const revenueKey = `revenueUpdate_${data.revenueId || 'unknown'}`;
        
        // 중요: 예약 생성 중인 경우에는 원본 금액 사용
        const updateAmount = pendingCreateBookingIds.has(bookId) && originalPaymentAmounts.has(bookId)
          ? originalPaymentAmounts.get(bookId)
          : data.amount;
          
        requestMap.set(revenueKey, {
          bookId,
          bookIdx,
          revenueId: data.revenueId,
          amount: updateAmount,
          finished: data.finished,
          timestamp: Date.now()
        });
        
        // 처리 표시
        data.processed = true;
        data.bookId = bookId;
        requestMap.set(key, data);
        
        console.log(`[INFO] Created/updated revenue update for book_id ${bookId}: amount=${updateAmount}, finished=${data.finished}`);
      } else {
        console.log(`[WARN] No book_id found for book_idx ${bookIdx} in pending payment update`);
      }
    }
  }
};

const handleRevenueResponse = async (response, request, maps) => {
  const { paymentAmounts, paymentStatus, bookIdToIdxMap, requestMap, bookingDataMap } = maps;
  const { parseMultipartFormData } = require('../utils/parser');
  
  try {
    const responseData = await response.json();
    let payload;
    
    try {
      payload = parseMultipartFormData(request.postData());
    } catch (e) {
      console.error(`[ERROR] Failed to parse revenue request data: ${e.message}`);
      return null;
    }
    
    if (!payload || !payload.book_idx) {
      console.log(`[WARN] Missing book_idx in revenue payload:`, JSON.stringify(payload, null, 2));
      return null;
    }

    const bookIdx = payload.book_idx;
    const amount = parseInt(payload.amount, 10) || 0;
    
    // string 'true'/'false'를 실제 boolean으로 변환
    const finishedStr = payload.finished?.toLowerCase() || 'false';
    const finished = finishedStr === 'true';
    
    console.log(`[DEBUG] Payment status in revenue payload: '${payload.finished}' -> ${finished}`);
    
    const bookIdEntries = Array.from(bookIdToIdxMap.entries());
    const match = bookIdEntries.find(([, idx]) => idx === bookIdx);
    const bookId = match ? match[0] : null;

    if (bookId) {
      // 이전 결제 상태 확인
      const previousFinished = paymentStatus.get(bookId);
      const paymentStatusChanged = previousFinished !== finished;
      
      if (paymentStatusChanged) {
        console.log(`[INFO] Payment status changed for ${bookId}: ${previousFinished} -> ${finished}`);
        
        // 중요: 결제 상태 변경 감지 시 강제 업데이트를 위한 플래그 설정
        // pendingUpdate가 이미 있는 경우 forceUpdate 플래그 추가
        const pendingUpdateKey = `pendingUpdate_${bookId}`;
        if (bookingDataMap.has(pendingUpdateKey)) {
          const pendingData = bookingDataMap.get(pendingUpdateKey);
          pendingData.forceUpdate = true;
          bookingDataMap.set(pendingUpdateKey, pendingData);
          console.log(`[INFO] Setting forceUpdate flag for pending update of ${bookId}`);
        }
      }
      
      // 예약 생성 중인 경우 원본 금액 보존
      if (pendingCreateBookingIds.has(bookId)) {
        console.log(`[INFO] Found booking ${bookId} in creation process, updating payment info`);
        
        if (!originalPaymentAmounts.has(bookId)) {
          originalPaymentAmounts.set(bookId, amount);
          console.log(`[INFO] Stored original payment amount ${amount} for new booking ${bookId}`);
        }
        
        paymentAmounts.set(bookId, amount);
        paymentStatus.set(bookId, finished);
        return { bookId, amount, finished };
      }
      
      paymentAmounts.set(bookId, amount);
      paymentStatus.set(bookId, finished);
      console.log(`[INFO] Updated payment for book_id ${bookId} (book_idx ${bookIdx}): amount=${amount}, finished=${finished}`);
      
      // 결제 정보 업데이트 저장
      const revenueId = responseData?.id || null;
      const revenueKey = `revenueUpdate_${revenueId || 'unknown'}`;
      
      requestMap.set(revenueKey, {
        bookId,
        bookIdx,
        revenueId,
        amount,
        finished,
        timestamp: Date.now(),
        paymentStatusChanged // 결제 상태 변경 여부 추가
      });
      
      console.log(`[INFO] Stored payment update for book_id ${bookId} in requestMap`);
      
      return { bookId, amount, finished };
    } else {
      console.log(`[WARN] No book_id found for book_idx ${bookIdx}`);
      
      // book_id를 즉시 찾을 수 없으면 임시 저장
      const revenueId = responseData?.id || null;
      const paymentKey = `paymentUpdate_${bookIdx}`;
      
      requestMap.set(paymentKey, {
        bookIdx,
        revenueId,
        amount, 
        finished,
        processed: false,
        timestamp: Date.now()
      });
      
      console.log(`[INFO] Stored pending payment update for book_idx ${bookIdx}: amount=${amount}, finished=${finished}`);
    }
  } catch (e) {
    console.error(`[ERROR] Failed to parse /owner/revenue/ response: ${e.message}`);
  }
  
  return null;
};

const handleBookingCreateResponse = async (url, response, requestMap, accessToken, maps) => {
  const { processedBookings, paymentAmounts, paymentStatus, bookIdToIdxMap, bookingDataMap } = maps;
  
  try {
    let responseData;
    try {
      responseData = await response.json();
    } catch (e) {
      console.error(`[ERROR] Failed to parse booking create response: ${e.message}`);
      return;
    }
    
    console.log(`[DEBUG] Booking_Create Response Data:`, JSON.stringify(responseData, null, 2));
    
    if (!responseData || !responseData.book_id) {
      console.log(`[WARN] Missing book_id in booking create response:`, JSON.stringify(responseData, null, 2));
      return;
    }

    let requestData = requestMap.get(url);
    if (!requestData) {
      console.log(`[WARN] No matching request data found for URL: ${url}`);
      requestData = { type: 'Booking_Create', payload: {} };
    }

    const bookId = responseData.book_id;
    
    // 이 예약이 현재 처리 중이라고 표시
    pendingCreateBookingIds.add(bookId);
    
    // 이미 처리된 예약인지 확인
    if (processedBookingIds.has(bookId)) {
      console.log(`[INFO] Skipping already processed booking create for ${bookId}`);
      return;
    }
    
    bookIdToIdxMap.set(bookId, responseData.idx?.toString() || '');
    
    bookingDataMap.set(bookId, { 
      type: 'Booking_Create', 
      payload: requestData.payload, 
      response: responseData, 
      timestamp: Date.now() 
    });
    
    // 중요: 원본 결제 금액 저장
    if (responseData.amount) {
      const clientAmount = parseInt(responseData.amount, 10);
      originalPaymentAmounts.set(bookId, clientAmount);
      console.log(`[INFO] Saved original client payment amount ${clientAmount} for book_id ${bookId}`);
    }

    console.log(`[INFO] Booking_Create stored for book_id ${bookId}, idx: ${responseData.idx}`);
    
    // 완료 후 처리 중 목록에서 제거
    setTimeout(() => {
      pendingCreateBookingIds.delete(bookId);
      console.log(`[INFO] Removed ${bookId} from pending creation list`);
    }, 5000); // 5초 후에 예약 생성 중 목록에서 제거
    
    // 결제 정보 확인은 생략 - 이제 request.js에서 직접 처리함
    processedBookingIds.add(bookId); // 처리 완료 표시
    
    // Clean up request map entry
    requestMap.delete(url);
  } catch (e) {
    console.error(`[ERROR] Failed to process Booking_Create: ${e.message}`);
  }
};

module.exports = {
  processPendingBookingUpdates,
  processBookingUpdate,
  findBookIdByRevenueIdOrBookIdx,
  extractRevenueId,
  handleBookingListingResponse,
  handleRevenueResponse,
  handleBookingCreateResponse,
  processPendingPaymentUpdates,
  pendingCreateBookingIds,  // 예약 생성 중 목록을 외부에 노출
  originalPaymentAmounts,   // 원본 결제 금액 맵을 외부에 노출
  processedBookingIds,      // 처리 완료된 예약 목록을 외부에 노출
  processingUpdates         // 처리 중인 업데이트 목록을 외부에 노출
};