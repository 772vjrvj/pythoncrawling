// services/customerService.js
const { sendTo24GolfApi, getAccessToken, convertKSTtoUTC } = require('../utils/api');
const { getAutoCancelService } = require('./puppeteer');

class CustomerService {
  constructor(maps, accessToken, processedCustomerRequests, bookingDataCache) {
    this.maps = maps;
    this.accessToken = accessToken;
    this.processedCustomerRequests = processedCustomerRequests;
    this.bookingDataCache = bookingDataCache;
    this.customerUpdates = new Map();
    this.recentCustomerIds = new Set();
    this.processedAppBookings = new Set();
    // 자동 취소 서비스는 Puppeteer 모듈에서 싱글톤으로 가져옴
    this.autoCancelService = null;
    
    // 중복 요청 관리를 위한 맵 - customerId_roomId 형태의 키를 사용
    this.processingCustomerRooms = new Map();
    
    // 클래스 초기화 시점에는 Puppeteer가 아직 시작되지 않았을 수 있으므로
    // 지연 초기화를 위한 코드 추가
    this._initAutoCancelService();
  }
  
  /**
   * 자동 취소 서비스 초기화
   * Puppeteer가 시작된 후에 호출 가능
   */
  _initAutoCancelService() {
    try {
      this.autoCancelService = getAutoCancelService();
      if (this.autoCancelService) {
        console.log('[INFO] Auto-cancel service initialized in CustomerService');
      } else {
        console.log('[WARN] Auto-cancel service not available yet, will try again later');
        
        // 5초 후 다시 시도
        setTimeout(() => {
          this.autoCancelService = getAutoCancelService();
          if (this.autoCancelService) {
            console.log('[INFO] Auto-cancel service initialized in CustomerService (retry)');
          } else {
            console.log('[ERROR] Failed to initialize auto-cancel service after retry');
          }
        }, 5000);
      }
    } catch (error) {
      console.error(`[ERROR] Error initializing auto-cancel service: ${error.message}`);
    }
  }

  async handleCustomerResponse(response) {
    console.log(`[DEBUG] Processing customer info API response: ${response.url()}`);
    const customerData = await response.json();
    const customerId = customerData?.id;
    if (!customerId) return;
  
    console.log(`[DEBUG] Detected customerId: ${customerId}`);
    this._storeCustomerUpdate(customerData);
    
    // URL에서 방 정보 추출 시도
    let roomId = null;
    try {
      // URL에서 room 관련 정보 추출 시도
      const urlPath = new URL(response.url()).pathname;
      // 매개변수 또는 쿼리스트링에서 roomId 추출 (실제 API 구조에 맞게 조정 필요)
      const match = urlPath.match(/\/room\/(\d+)/i) || response.url().match(/[?&]room(?:Id)?=(\d+)/i);
      if (match && match[1]) {
        roomId = match[1];
        console.log(`[DEBUG] Extracted roomId from URL: ${roomId}`);
      }
    } catch (e) {
      console.log(`[DEBUG] Could not extract roomId from URL: ${e.message}`);
    }
    
    // 예약 시작 시간 정보 추출 시도
    let startDateTime = null;
    try {
      // 1) customerData에서 직접 시작 시간 찾기 (가장 정확한 정보)
      if (customerData.start_datetime) {
        startDateTime = customerData.start_datetime;
        console.log(`[DEBUG] Extracted startDateTime directly from customerData: ${startDateTime}`);
      }
      // 2) 예약 정보에서 시작 시간 찾기
      else if (customerData.reservation && customerData.reservation.start_datetime) {
        startDateTime = customerData.reservation.start_datetime;
        console.log(`[DEBUG] Extracted startDateTime from customerData.reservation: ${startDateTime}`);
      }
      // 3) URL에서 시작 시간 파라미터 찾기 (필요한 경우)
      else {
        const startTimeMatch = response.url().match(/[?&]start(?:Time|DateTime)?=([^&]+)/i) || 
                              response.url().match(/[?&]date_from=([^&]+)/i);
        if (startTimeMatch && startTimeMatch[1]) {
          startDateTime = decodeURIComponent(startTimeMatch[1]);
          console.log(`[DEBUG] Extracted startDateTime from URL: ${startDateTime}`);
        }
      }
    } catch (e) {
      console.log(`[DEBUG] Could not extract startDateTime: ${e.message}`);
    }
    
    // 각 요청마다 고유 식별자 생성을 위해 타임스탬프 추가
    const timestamp = Date.now();
    
    // 고객 ID + 룸 ID + 시작 시간 + 타임스탬프로 복합 키 생성
    // 시작 시간이 없으면 타임스탬프로 대체하여 각 요청마다 고유하게 처리
    const customerRoomKey = customerId + 
                           (roomId ? `_${roomId}` : '_unknown') + 
                           (startDateTime ? `_${startDateTime}` : `_ts_${timestamp}`);
    
    console.log(`[DEBUG] Generated unique key for customer request: ${customerRoomKey}`);
    
    // 이미 처리 중인 복합 키는 건너뜀
    if (this.processingCustomerRooms.has(customerRoomKey)) {
      console.log(`[INFO] Already processing customer ${customerId} for room ${roomId || 'unknown'} and time ${startDateTime || 'unknown'}, skipping duplicate check`);
      return;
    }
  
    // 요청 중복 방지: 복합 키 기반 추적
    this.processingCustomerRooms.set(customerRoomKey, {
      customerId,
      roomId,
      startDateTime,
      timestamp: timestamp
    });
    
    // 호환성을 위해 기존 Set도 유지
    this.recentCustomerIds.add(customerId);
    this.processedCustomerRequests.add(customerId);
    console.log(`[INFO] Added customer ${customerId} (room: ${roomId || 'unknown'}, time: ${startDateTime || 'unknown'}) to recent checks, will process after booking data is received`);
  
    // 최신 예약 데이터를 얻은 후 처리 (10초 후)
    // startDateTime 파라미터 전달
    setTimeout(() => this._processPendingCustomer(customerId, roomId, startDateTime, customerRoomKey), 10000);
  }
  
  // 복합 키 생성 함수 추가
  _createUniqueKey(customerId, roomId = null, startDateTime = null) {
    const roomPart = roomId ? `_${roomId}` : '';
    const timePart = startDateTime ? `_${startDateTime}` : '';
    return `${customerId}${roomPart}${timePart}`;
  }

  _storeCustomerUpdate(data) {
    // 고객 정보 중 최근 업데이트 정보 확인
    let latestUpdateTime = null;
    if (data.customerinfo_set && Array.isArray(data.customerinfo_set) && data.customerinfo_set.length > 0) {
      const customerInfo = data.customerinfo_set[0];
      if (customerInfo.upd_date) {
        latestUpdateTime = new Date(customerInfo.upd_date).getTime();
      }
    }
    
    console.log(`[INFO] Detected customer info access - customerId: ${data.id}, name: ${data.name || ''}, updateTime: ${latestUpdateTime}`);
  
    // 자동 취소 서비스를 통한 취소 버튼 확인 - 이 부분이 문제!
    if (this.autoCancelService) {
        // 현재 처리 중인 이벤트 컨텍스트 확인
        if (global.currentProcessingModalType === 'cancel') {
        console.log('[INFO] 취소 모달 처리 중, 고객 정보 업데이트를 통한 새 예약 생성 억제');
        return; // 취소 모달 처리 중에는 고객 정보 저장 및 예약 생성 건너뛰기
        }
        
        this.autoCancelService.checkOnCustomerAccess(data.id, data.name || '');
    } else {
        console.log('[WARN] Auto-cancel service not available, trying to re-initialize');
        this._initAutoCancelService();
    }
    
    // 현재 시간 기준으로 최근 업데이트된 고객 정보만 저장 (30초 이내)
    const now = Date.now();
    const thirtySecondsAgo = now - 30 * 1000;
    
    if (latestUpdateTime && latestUpdateTime > thirtySecondsAgo) {
      console.log(`[INFO] Storing recent customer update for customerId: ${data.id}`);
      this.customerUpdates.set(data.id, {
        id: data.id,
        name: data.name || '',
        phone: data.phone || '',
        updateTime: latestUpdateTime,
        timestamp: now
      });
    }
  }

  async _processPendingCustomer(customerId, roomId, startDateTime, customerRoomKey) {
    try {
        // 시작 시간 정보 추출 (customerRoomKey로부터)
    let startDateTime = null;
    if (customerRoomKey && customerRoomKey.includes('_')) {
      const parts = customerRoomKey.split('_');
      if (parts.length >= 3) {
        startDateTime = parts[2]; // customerId_roomId_startDateTime 형식 가정
      }
    }

      // 캐시된 예약 데이터 확인
      if (this.bookingDataCache.data && (Date.now() - this.bookingDataCache.timestamp < 60000)) {
        console.log(`[INFO] Using cached booking data from ${new Date(this.bookingDataCache.timestamp).toISOString()}`);
        await this.processCustomerBookings(customerId, this.bookingDataCache.data, roomId, startDateTime);
      } else {
        console.log(`[INFO] Waiting for next booking data to process customer ${customerId} (room: ${roomId || 'unknown'}, time: ${startDateTime || 'unknown'})`);
        // 다음 예약 데이터가 수신될 때까지 기다림 - 주기적으로 요청되는 데이터
        
        // customerUpdates에 이 고객 정보를 더 오래 유지 (3분으로 연장)
        if (this.customerUpdates.has(customerId)) {
          const customerData = this.customerUpdates.get(customerId);
          customerData.timestamp = Date.now(); // 타임스탬프 갱신하여 더 오래 유지
          // 시작 시간 정보 추가 (없었다면)
          if (startDateTime && !customerData.startDateTime) {
            customerData.startDateTime = startDateTime;
          }
          this.customerUpdates.set(customerId, customerData);
          console.log(`[INFO] Extended customer update retention time for ${customerId}`);
        }
      }
    } catch (e) {
      console.error(`[ERROR] Failed to process customer ${customerId} bookings: ${e.message}`);
    } finally {
      // customerRoomKey 기반 처리 정보 정리
      if (customerRoomKey) {
        this.processingCustomerRooms.delete(customerRoomKey);
        console.log(`[INFO] Removed customer-room-time ${customerRoomKey} from processing list`);
      }
      
      // 여기서 recentCustomerIds에서는 제거하지만, 
      // processedCustomerRequests에서는 제거하지 않음 (시간 연장)
      this.recentCustomerIds.delete(customerId);
      
      // 10초 후에 processedCustomerRequests에서 제거 
      setTimeout(() => {
        this.processedCustomerRequests.delete(customerId);
        console.log(`[INFO] Removed customer ${customerId} from processed requests after 10 seconds`);
      }, 10000); // 10초로 단축
      
      console.log(`[INFO] Removed customer ${customerId} from recent checks after processing`);
    }
  }

  // async 키워드 추가 - 이 함수 내에서 await을 사용하므로 필요함
  async processCustomerBookings(customerId, bookingData, roomId) {
    console.log(`[INFO] Processing bookings for customer ${customerId}${roomId ? ` and room ${roomId}` : ''}${startDateTime ? ` and time ${startDateTime}` : ''}`);
  const { paymentAmounts, paymentStatus, processedBookings } = this.maps;
    
    try {
        if (!bookingData.results || !Array.isArray(bookingData.results)) {
          console.log(`[WARN] No booking results found in data`);
          return;
        }
        
        // 고객 ID에 해당하는 예약만 필터링 (roomId와 startDateTime이 제공된 경우 추가 필터링)
        const customerBookings = bookingData.results.filter(booking => {
          const customerMatch = booking.customer === customerId;
          const roomMatch = !roomId || booking.room?.toString() === roomId;
          
          // 시작 시간 일치 여부 확인 (추가)
          let timeMatch = true;
          if (startDateTime && booking.start_datetime) {
            // 일반 문자열 비교 또는 필요 시 시간 변환 후 비교
            timeMatch = booking.start_datetime === startDateTime;
          }
          
          const stateMatch = booking.state === 'success';
          const notProcessed = !processedBookings.has(booking.book_id) && !this.processedAppBookings.has(booking.book_id);
          
          return customerMatch && roomMatch && timeMatch && stateMatch && notProcessed;
        });
        
        console.log(`[INFO] Found ${customerBookings.length} success bookings for customer ${customerId}${roomId ? ` and room ${roomId}` : ''}${startDateTime ? ` and time ${startDateTime}` : ''}`);
        
      if (customerBookings.length > 0) {
        // 최신 업데이트 순으로 정렬
        customerBookings.sort((a, b) => {
          const aDate = new Date(a.customer_detail?.customerinfo_set?.[0]?.upd_date || 0);
          const bDate = new Date(b.customer_detail?.customerinfo_set?.[0]?.upd_date || 0);
          return bDate - aDate;
        });
        
        // 최신 예약 처리
        for (const booking of customerBookings) {
          const bookId = booking.book_id;
          console.log(`[DEBUG] Processing booking: ${bookId}`);
          
          // 결제 정보 가져오기
          const revenueDetail = booking.revenue_detail || {};
          const amount = parseInt(revenueDetail.amount || booking.amount || 0, 10);
          
          // 결제 완료 여부 확인 (finished가 true인 경우에만 true)
          const finished = revenueDetail.finished === true || revenueDetail.finished === 'true';
          
          console.log(`[DEBUG] Booking info - book_id: ${bookId}, customer: ${booking.customer}, state: ${booking.state}`);
          console.log(`[DEBUG] Extracted payment info for book_id ${bookId}: amount=${amount}, finished=${finished}`);
          
          // 맵에 저장
          paymentAmounts.set(bookId, amount);
          paymentStatus.set(bookId, finished);
          
          // 날짜 변환 (KST -> UTC)
          const startDate = booking.start_datetime ? convertKSTtoUTC(booking.start_datetime) : null;
          const endDate = booking.end_datetime ? convertKSTtoUTC(booking.end_datetime) : null;
          
          console.log(`[DEBUG] UTC times - Start: ${startDate}, End: ${endDate}`);
          
          // 예약 처리 데이터 준비
          const bookingData = {
            externalId: bookId,
            name: booking.name || 'Unknown',
            phone: booking.phone || '010-0000-0000',
            partySize: parseInt(booking.person || 1, 10),
            startDate: startDate,
            endDate: endDate,
            roomId: booking.room?.toString() || 'unknown',
            hole: booking.hole,
            paymented: finished,
            paymentAmount: amount,
            crawlingSite: 'KimCaddie',
            immediate: booking.immediate_booked || false
          };
          
          // 로그 추가 - 최종 결제 금액 확인
          console.log(`[DEBUG] Final API payment amount for customer booking ${bookId}: ${bookingData.paymentAmount}`);
          
          /*
          try {
            // 유효한 토큰 확인
            let currentToken = this.accessToken;
            if (!currentToken) {
              console.log(`[DEBUG] No access token available, fetching new one`);
              currentToken = await getAccessToken();
            }
            
            console.log(`[INFO] Processing Auto Booking_Create for book_id: ${bookId}`);
            console.log(`[DEBUG] Sending API data for auto booking:`, JSON.stringify(bookingData, null, 2));
            
            // 예약 등록 API 호출
            await sendTo24GolfApi(
              'Booking_Create', 
              '', 
              {}, 
              bookingData, 
              currentToken, 
              processedBookings, 
              paymentAmounts, 
              paymentStatus
            );
            
            console.log(`[INFO] Requested Auto Booking_Create for book_id: ${bookId}`);
            this.processedAppBookings.add(bookId);
          } catch (error) {
            console.error(`[ERROR] Failed to process Auto Booking_Create: ${error.message}`);
          }
            */
        }
      } else {
        console.log(`[INFO] No new success bookings found for customer ${customerId}${roomId ? ` and room ${roomId}` : ''}`);
      }
    } catch (e) {
      console.error(`[ERROR] Failed to process customer bookings: ${e.message}`);
    }
  }

  // 오래된 고객 업데이트 정보 정리
  cleanUpOldUpdates() {
    // 15분으로 연장 (기존 5분)
    const fifteenMinutesAgo = Date.now() - 15 * 60 * 1000;
    for (const [customerId, data] of this.customerUpdates.entries()) {
      if (data.timestamp < fifteenMinutesAgo) {
        this.customerUpdates.delete(customerId);
      }
    }
    
    // customerRooms 정리 - 15분 이상 된 항목 삭제
    for (const [key, data] of this.processingCustomerRooms.entries()) {
      if (data.timestamp < fifteenMinutesAgo) {
        this.processingCustomerRooms.delete(key);
        console.log(`[INFO] Cleaned up old customer-room tracking: ${key}`);
      }
    }
    
    // 오래된 처리 정보 정리 (하루에 한 번)
    if (this.processedAppBookings.size > 1000) {
      console.log(`[INFO] Clearing old processed app bookings (size=${this.processedAppBookings.size})`);
      this.processedAppBookings.clear();
    }
  }
}

module.exports = CustomerService;