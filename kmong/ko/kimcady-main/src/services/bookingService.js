const { sendTo24GolfApi, getAccessToken, convertKSTtoUTC } = require('../utils/api');
const { parseMultipartFormData } = require('../utils/parser');
const { handleBookingListingResponse, handleBookingCreateResponse, processPendingBookingUpdates } = require('../handlers/response-helpers');

class BookingService {
    constructor(maps, accessToken, bookingDataCache) {
        this.maps = maps;
        this.accessToken = accessToken;
        this.bookingDataCache = bookingDataCache;
        this.processedAppBookings = new Set();
        this.processedCancelRequests = new Map(); // 고객 ID와 업데이트 시간으로 취소 요청 추적
        this.pendingBookingCreations = new Map(); // 예약 생성 대기 목록 (금액 확인 전)
        this.htmlCaptureService = null; // HTML 캡처 서비스 참조 (외부에서 설정)
        this.processingBookingRequests = new Set();
        this.bookingListProcessing = false; // 예약 목록 응답 처리 중인지 여부 추적
        this.modalDetectionService = null;
        this.canceledBookingIds = new Set(); // 취소된 예약 ID 추적
        this.bookingLocks = new Map(); // 예약 ID별 락 추적

        // 추가: 전역 변수가 없으면 초기화
        if (!global.modalBookingInProgress) {
            global.modalBookingInProgress = false;
            global.modalBookingId = null;
        }

        // 추가: 전역 등록된 예약 ID 집합 초기화
        if (!global.alreadyCreatedBookings) {
            global.alreadyCreatedBookings = new Set();
        }
      }

      async _createBookingWithLock(data) {
        const bookId = data.externalId;
        
        // 이미 처리된 예약인지 확인하는 메커니즘 강화
        if (this.maps.processedBookings.has(bookId)) {
          console.log(`[INFO] Skipping duplicate booking creation for ${bookId} - already processed (확인 1)`);
          return;
        }
        
        // 락 확인 전에 processedApiCallMap을 통한 추가 확인
        if (this.maps.processedApiCallMap && this.maps.processedApiCallMap.has(bookId)) {
          console.log(`[INFO] Skipping duplicate booking creation for ${bookId} - found in processedApiCallMap (확인 2)`);
          return;
        }
        
        // 이미 락이 있는 경우 대기
        if (this.bookingLocks.has(bookId)) {
          console.log(`[INFO] Waiting for lock release on bookId: ${bookId}`);
          try {
            await this.bookingLocks.get(bookId);
            console.log(`[INFO] Lock released for bookId: ${bookId}, but skipping duplicate request`);
            return; // 락이 해제되면 중복 요청은 건너뛰기
          } catch (error) {
            console.log(`[INFO] Previous processing for bookId: ${bookId} failed, proceeding with current request`);
          }
        }
        
        // 새 락 생성 (Promise로)
        let resolveLock, rejectLock;
        const lockPromise = new Promise((resolve, reject) => {
          resolveLock = resolve;
          rejectLock = reject;
        });
        this.bookingLocks.set(bookId, lockPromise);
        
        try {
          // 모든 호출 진입점에서 API 호출 여부 확인하도록 전역 플래그 추가
          if (!global.bookingApiCallInProgress) {
            global.bookingApiCallInProgress = new Map();
          }
          
          // 이미 진행 중인 API 호출이 있는지 확인
          if (global.bookingApiCallInProgress.has(bookId)) {
            console.log(`[INFO] API call already in progress for bookId: ${bookId}, skipping duplicate call`);
            return;
          }
          
          // API 호출 진행 중 표시
          global.bookingApiCallInProgress.set(bookId, Date.now());
          
          // 기존 _createBooking 로직 수행
          await this._createBooking(data);
          
          // 성공적으로 처리 완료 후 진행 중 표시 제거
          global.bookingApiCallInProgress.delete(bookId);
          
          resolveLock(); // 성공 시 락 해제
        } catch (error) {
          // 실패 시도 진행 중 표시 제거
          if (global.bookingApiCallInProgress) {
            global.bookingApiCallInProgress.delete(bookId);
          }
          
          rejectLock(error); // 실패 시 락 해제 (실패 상태로)
          throw error;
        } finally {
          // 락 제거
          setTimeout(() => {
            this.bookingLocks.delete(bookId);
          }, 10000); // 10초 후 락 제거 (안전장치)
        }
      }
  /**
   * HTML 캡처 서비스 설정
   * @param {Object} htmlCaptureService - HTML 캡처 서비스 인스턴스
   */
  setHtmlCaptureService(htmlCaptureService) {
    this.htmlCaptureService = htmlCaptureService;
    console.log('[INFO] HTML capture service set in BookingService');
  }

  async handleBookingConfirmation(request) {
    const payload = parseMultipartFormData(request.postData());
    if (!payload || payload.state !== 'success') return;
  
    console.log(`[INFO] Detected booking confirmation: bookId=${payload.book_id}, room=${payload.room}, state=${payload.state}`);
  
    try {
      const bookId = payload.book_id;
      // 이미 처리 중인 예약인지 확인
        if (this.processingBookingRequests.has(bookId)) {
            console.log(`[INFO] Skipping duplicate booking confirmation for ${bookId} - already in progress`);
            return;
        }
        
        // 이미 처리 완료된 예약인지 확인
        if (this.maps.processedBookings.has(bookId) || this.processedAppBookings.has(bookId)) {
            console.log(`[INFO] Skipping duplicate booking confirmation for ${bookId} - already processed`);
            return;
        }
        
        // 처리 중 상태로 변경
        this.processingBookingRequests.add(bookId);
        
      let bookingInfo = {};
      if (payload.bookingInfo) {
        try {
          bookingInfo = JSON.parse(payload.bookingInfo);
          console.log(`[DEBUG] Parsed booking info:`, JSON.stringify(bookingInfo, null, 2));
        } catch (e) {
          console.error(`[ERROR] Failed to parse bookingInfo JSON: ${e.message}`);
        }
      }
  
      let amount = parseInt(bookingInfo.amount || 0, 10);
      let finished = false;
      const roomId = payload.room || bookingInfo.room;
  
      let startDate = bookingInfo.start_datetime ? convertKSTtoUTC(bookingInfo.start_datetime) : null;
      let endDate = bookingInfo.end_datetime ? convertKSTtoUTC(bookingInfo.end_datetime) : null;
  
      const apiData = {
        externalId: bookId,
        name: bookingInfo.name || payload.name || 'Unknown',
        phone: bookingInfo.phone || payload.phone || '010-0000-0000',
        partySize: parseInt(bookingInfo.person || payload.person || 1, 10),
        startDate: startDate,
        endDate: endDate,
        roomId: roomId || 'unknown',
        hole: bookingInfo.hole || '9',
        paymented: finished,
        paymentAmount: amount,
        crawlingSite: 'KimCaddie',
        immediate: false
      };
  
      // 1. 초기 금액 확인
      console.log(`[INFO] Waiting for accurate price information for booking ${bookId}...`);
      const initialAccurateAmount = await this._getAccuratePrice(bookId);
      if (initialAccurateAmount && initialAccurateAmount > amount) {
        console.log(`[INFO] Found initial accurate price ${initialAccurateAmount} for booking ${bookId} (initial: ${amount})`);
        amount = initialAccurateAmount;
        apiData.paymentAmount = initialAccurateAmount;
      }
  
      // 2. 최신 owner/booking 데이터 강제 가져오기
      console.log(`[INFO] Forcing fetch of latest booking data for ${bookId} to ensure accurate price`);
      await this._fetchLatestBookingsInfo(); // 캐시 갱신
      const latestBooking = this.bookingDataCache.data?.results?.find(b => b.book_id === bookId);
      if (latestBooking && latestBooking.amount && latestBooking.amount > amount) {
        console.log(`[INFO] Updated amount from latest booking data: ${latestBooking.amount} for ${bookId}`);
        amount = latestBooking.amount;
        apiData.paymentAmount = amount;
        apiData.paymented = latestBooking.is_paid === true || latestBooking.revenue_detail?.finished === true;
      }
  
      // 3. 매핑된 revenue 데이터 확인 (최신 requestMap 반영)
      for (const [key, value] of this.maps.requestMap.entries()) {
        if (key.includes(bookId) && value && value.amount && value.amount > amount) {
          console.log(`[INFO] Found mapped revenue amount ${value.amount} for ${bookId} in requestMap`);
          amount = value.amount;
          apiData.paymentAmount = amount;
          apiData.paymented = value.finished === true;
          break;
        }
      }
  
      // 4. 추가 대기 (필요 시)
      if (amount === parseInt(bookingInfo.amount || 0, 10)) { // 초기 금액과 동일하면 추가 확인
        console.log(`[INFO] Initial amount unchanged, waiting briefly for owner/booking update for ${bookId}`);
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5초 대기
        await this._fetchLatestBookingsInfo(); // 다시 최신 데이터 가져오기
        const recheckedBooking = this.bookingDataCache.data?.results?.find(b => b.book_id === bookId);
        if (recheckedBooking && recheckedBooking.amount && recheckedBooking.amount > amount) {
          console.log(`[INFO] Updated amount after wait: ${recheckedBooking.amount} for ${bookId}`);
          amount = recheckedBooking.amount;
          apiData.paymentAmount = amount;
          apiData.paymented = recheckedBooking.is_paid === true || recheckedBooking.revenue_detail?.finished === true;
        }
        for (const [key, value] of this.maps.requestMap.entries()) {
          if (key.includes(bookId) && value && value.amount && value.amount > amount) {
            console.log(`[INFO] Found updated mapped revenue amount ${value.amount} for ${bookId} in requestMap`);
            amount = value.amount;
            apiData.paymentAmount = amount;
            apiData.paymented = value.finished === true;
            break;
          }
        }
      }
  
        // 5. 최종 금액으로 예약 생성
        console.log(`[INFO] Creating booking ${bookId} with final amount: ${apiData.paymentAmount}, paymented: ${apiData.paymented}`);

        try {
        // 예약 생성 전에 처리 중인 상태로 표시
        this.processedAppBookings.add(bookId);
        await this._createBooking(apiData);
        console.log(`[INFO] Processed Confirmed Booking_Create for book_id: ${bookId}`);
        } catch (error) {
        if (error.response?.status === 500 && error.response?.data?.message?.includes('duplicate key error')) {
            console.log(`[INFO] Booking ${bookId} already exists, treating as successful`);
        } else {
            console.error(`[ERROR] Failed to create booking: ${error.message}`);
            // 실패한 경우 처리된 상태에서 제거
            this.processedAppBookings.delete(bookId);
            throw error;
        }
        } finally {
        // 처리 중 상태 해제
        this.processingBookingRequests.delete(bookId);
        }
  
      console.log(`[INFO] Processed Confirmed Booking_Create for book_id: ${bookId}`);
    } catch (error) {
        console.error(`[ERROR] Failed to process confirmed booking: ${error.message}`);
        console.error(`[ERROR] Stack trace:`, error.stack);
        // 에러 발생 시 처리 중 상태 해제 - 추가
        this.processingBookingRequests.delete(payload?.book_id);
      }
  }

  // 정확한 금액 정보 가져오기
  async _getAccuratePrice(bookId) {
    // 1. 캐시된 데이터 확인 (최신 여부 확인: 10초 이내)
    if (this.bookingDataCache.data?.results && (Date.now() - this.bookingDataCache.timestamp < 10000)) {
      const booking = this.bookingDataCache.data.results.find(item => item.book_id === bookId);
      if (booking && booking.amount > 0) {
        console.log(`[INFO] Found price ${booking.amount} for booking ${bookId} in fresh cache`);
        return booking.amount;
      }
    }
  
    // 2. 캐시가 오래되었거나 데이터가 없으면 강제 갱신
    console.log(`[INFO] Cache outdated or no data for ${bookId}, fetching latest booking info`);
    await this._fetchLatestBookingsInfo();
    const booking = this.bookingDataCache.data?.results?.find(item => item.book_id === bookId);
    if (booking && booking.amount > 0) {
      console.log(`[INFO] Found price ${booking.amount} for booking ${bookId} in updated booking data`);
      return booking.amount;
    }
  
    // 3. 매핑 데이터 확인
    for (const [key, value] of this.maps.requestMap.entries()) {
      if (key.includes(bookId) && value && value.amount > 0) {
        console.log(`[INFO] Found price ${value.amount} for booking ${bookId} in request map`);
        return value.amount;
      }
    }
  
    console.log(`[INFO] No accurate price found for booking ${bookId} after exhaustive check`);
    return null;
  }

  async _fetchLatestBookingsInfo() {
    try {
      if (this.bookingDataCache.data?.results && (Date.now() - this.bookingDataCache.timestamp < 60000)) {
        console.log(`[INFO] Using recent booking data from cache (${Math.round((Date.now() - this.bookingDataCache.timestamp)/1000)}s old)`);
        return this.bookingDataCache.data;
      }

      console.log(`[INFO] Fetching latest booking data`);
      const token = this.accessToken || await getAccessToken();
      const storeId = process.env.STORE_ID || this.maps.storeId;

      if (!storeId) {
        console.error(`[ERROR] Store ID not found for fetching booking data`);
        return null;
      }

      const url = `${process.env.API_BASE_URL}/stores/${storeId}/reservation/crawl`;
      const axios = require('axios');
      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data && response.data.results) {
        this.bookingDataCache.data = response.data;
        this.bookingDataCache.timestamp = Date.now();
        console.log(`[INFO] Successfully fetched ${response.data.results.length} bookings`);
        return response.data;
      }
    } catch (error) {
      console.error(`[ERROR] Failed to fetch latest booking data: ${error.message}`);
    }
    return null;
  }

  async _updateBooking(data) {
    const token = this.accessToken || await getAccessToken();
    console.log(`[INFO] Updating booking with data:`, JSON.stringify(data, null, 2));
    await sendTo24GolfApi('Booking_Update', '', {}, data, token, 
      this.maps.processedBookings, this.maps.paymentAmounts, this.maps.paymentStatus);
  }

  async _checkAndUpdateExistingBookings(data) {
    const results = data.results || [];
    for (const booking of results) {
      const bookId = booking.book_id;
      if (this.processedAppBookings.has(bookId)) {
        const cachedAmount = this.maps.paymentAmounts.get(bookId) || 0;
        const latestAmount = parseInt(booking.amount || 0, 10);
        const latestFinished = booking.is_paid === true || booking.revenue_detail?.finished === true;
  
        // 매핑된 revenue 데이터 확인
        let mappedAmount = latestAmount;
        for (const [key, value] of this.maps.requestMap.entries()) {
          if (key.includes(bookId) && value && value.amount > mappedAmount) {
            mappedAmount = value.amount;
            console.log(`[INFO] Found higher mapped amount ${mappedAmount} for ${bookId} in requestMap`);
            break;
          }
        }
  
        if (mappedAmount > cachedAmount) {
          console.log(`[INFO] Amount mismatch for ${bookId}: cached=${cachedAmount}, latest=${mappedAmount}, updating booking`);
          const apiData = {
            externalId: bookId,
            paymentAmount: mappedAmount,
            paymented: latestFinished,
            crawlingSite: 'KimCaddie'
          };
          await this._updateBooking(apiData);
          this.maps.paymentAmounts.set(bookId, mappedAmount);
          this.maps.paymentStatus.set(bookId, latestFinished);
        }
      }
    }
  }

  async handleBookingList(response, customerService) {
    console.log(`[INFO] Detected GET /owner/booking/ - will process pending updates after response`);
    
    // 중요: 이미 예약 목록 처리 중인 경우 중복 처리 방지
    if (this.bookingListProcessing) {
      console.log(`[INFO] Already processing booking list - skipping duplicate processing`);
      return;
    }
    
    this.bookingListProcessing = true;
    
    try {
      const responseJson = await response.json();
      console.log(`[DEBUG] Received booking data, caching it for future use`);
    
      this.bookingDataCache.data = responseJson;
      this.bookingDataCache.timestamp = Date.now();
    
      // 1. 대기 중인 예약 처리
      await this._processPendingCreations(responseJson);
    
      // 2. 이미 생성된 예약의 금액 확인 및 업데이트
      await this._checkAndUpdateExistingBookings(responseJson);
    
      // 3. 앱 예약 처리 (취소 감지는 제거됨)
      // await this._handleCancelingBookings(responseJson, customerService); // 기존 취소 감지 로직 비활성화
      await handleBookingListingResponse(response, this.maps);
      await this._processAppBookings(responseJson, customerService);
      
      // 4. 처리 순서 변경: 모든 예약 정보 처리 완료 후 대기 중인 업데이트 처리
      await processPendingBookingUpdates(this.accessToken, this.maps);
    
      if (customerService) {
        console.log(`[INFO] Processing ${customerService.recentCustomerIds?.size || 0} pending customer IDs with fresh booking data`);
        if (customerService.recentCustomerIds) {
          for (const customerId of customerService.recentCustomerIds) {
            customerService.processCustomerBookings(customerId, responseJson);
          }
        }
      }
    } catch (error) {
      console.error(`[ERROR] Failed to process booking list: ${error.message}`);
    } finally {
      // 처리 완료 후 flag 초기화
      this.bookingListProcessing = false;
    }
  }

  // 대기 중인 예약 생성 처리
  async _processPendingCreations(data) {
    if (!this.pendingBookingCreations.size) return;
  
    console.log(`[INFO] Processing ${this.pendingBookingCreations.size} pending booking creations with latest data`);
    const results = data.results || [];
  
    for (const [bookId, pendingData] of this.pendingBookingCreations.entries()) {
      let foundAmount = pendingData.currentAmount;
      let foundFinished = pendingData.apiData.paymented;
  
      // 1. 예약 목록에서 최신 금액 확인
      const booking = results.find(b => b.book_id === bookId);
      if (booking && booking.amount > foundAmount) {
        foundAmount = booking.amount;
        foundFinished = booking.is_paid === true || booking.revenue_detail?.finished === true;
        console.log(`[INFO] Updated amount ${foundAmount} and finished ${foundFinished} for ${bookId} from booking list`);
      }
  
      // 2. 매핑된 금액 확인
      for (const [key, value] of this.maps.requestMap.entries()) {
        if (key.includes(bookId) && value && value.amount > foundAmount) {
          foundAmount = value.amount;
          foundFinished = value.finished === true;
          console.log(`[INFO] Updated amount ${foundAmount} and finished ${foundFinished} for ${bookId} from request map`);
          break;
        }
      }
  
      // 3. 금액 및 결제 상태 업데이트 후 예약 생성
      if (foundAmount > pendingData.currentAmount || foundFinished !== pendingData.apiData.paymented) {
        pendingData.apiData.paymentAmount = foundAmount;
        pendingData.apiData.paymented = foundFinished;
        console.log(`[INFO] Creating booking ${bookId} with updated amount: ${foundAmount}, paymented: ${foundFinished}`);
        
        // 이미 처리 중인지 확인 - 추가
        if (this.processingBookingRequests.has(bookId) || this.processedAppBookings.has(bookId)) {
          console.log(`[INFO] Skipping pending creation for ${bookId} - already being processed or completed`);
          this.pendingBookingCreations.delete(bookId);
          continue;
        }
        
        // 처리 중 상태로 표시 - 추가
        this.processingBookingRequests.add(bookId);
        this.processedAppBookings.add(bookId);
        
        try {
          await this._createBooking(pendingData.apiData);
          console.log(`[INFO] Successfully created booking from pending: ${bookId}`);
        } catch (error) {
          if (error.response?.status === 500 && error.response?.data?.message?.includes('duplicate key error')) {
            console.log(`[INFO] Pending booking ${bookId} already exists, treating as successful`);
          } else {
            console.error(`[ERROR] Failed to create pending booking: ${error.message}`);
            // 실패 시 처리된 목록에서 제거
            this.processedAppBookings.delete(bookId);
          }
        } finally {
          // 처리 완료 후 처리 중 상태 및 대기 목록에서 제거
          this.processingBookingRequests.delete(bookId);
          this.pendingBookingCreations.delete(bookId);
        }
      } else if (Date.now() - pendingData.timestamp > 120000) {
        // 2분 타임아웃 시 현재 데이터로 생성
        console.log(`[WARN] Booking ${bookId} timed out, creating with current amount: ${pendingData.apiData.paymentAmount}`);
        
        // 이미 처리 중인지 확인 - 추가
        if (this.processingBookingRequests.has(bookId) || this.processedAppBookings.has(bookId)) {
          console.log(`[INFO] Skipping timed-out pending creation for ${bookId} - already being processed or completed`);
          this.pendingBookingCreations.delete(bookId);
          continue;
        }
        
        // 처리 중 상태로 표시 - 추가
        this.processingBookingRequests.add(bookId);
        this.processedAppBookings.add(bookId);
        
        try {
          await this._createBooking(pendingData.apiData);
          console.log(`[INFO] Successfully created timed-out booking: ${bookId}`);
        } catch (error) {
          if (error.response?.status === 500 && error.response?.data?.message?.includes('duplicate key error')) {
            console.log(`[INFO] Timed-out booking ${bookId} already exists, treating as successful`);
          } else {
            console.error(`[ERROR] Failed to create timed-out booking: ${error.message}`);
            // 실패 시 처리된 목록에서 제거
            this.processedAppBookings.delete(bookId);
          }
        } finally {
          // 처리 완료 후 처리 중 상태 및 대기 목록에서 제거
          this.processingBookingRequests.delete(bookId);
          this.pendingBookingCreations.delete(bookId);
        }
      }
    }
  }

  /**
 * 고객 ID와 업데이트 시간을 기반으로 관련 예약을 찾습니다.
 * @param {Array} bookings - 예약 객체 배열
 * @param {String} customerId - 고객 ID
 * @param {String} updateTime - 고객 정보 업데이트 시간
 * @returns {Object} - 가장 적합한 예약 객체
 */
findRelevantBooking(bookings, customerId, updateTime) {
    // UTC 시간으로 변환 (updateTime은 이미 UTC일 수 있음)
    const targetTime = new Date(updateTime).getTime();
    
    // 고객 ID가 일치하는 예약들 필터링
    const customerBookings = bookings.filter(booking => 
      booking.customer === customerId || 
      (booking.customer_detail && booking.customer_detail.id === customerId)
    );
    
    logger.info(`고객 ID ${customerId}에 대한 예약 후보 ${customerBookings.length}개 발견`);
    
    // 업데이트 시간이 가장 근접한 예약 찾기
    let bestMatch = null;
    let minTimeDiff = Infinity;
    
    for (const booking of customerBookings) {
      // 고객 정보의 upd_date와 target 시간 비교
      if (booking.customer_detail && booking.customer_detail.customerinfo_set && 
          booking.customer_detail.customerinfo_set.length > 0) {
        const customerInfo = booking.customer_detail.customerinfo_set[0];
        if (customerInfo && customerInfo.upd_date) {
          // KST를 UTC로 변환 (9시간 차이)
          // 앱에서 사용하는 시간대에 맞게 조정 필요
          const updTimeStr = customerInfo.upd_date;
          const updTime = new Date(updTimeStr).getTime();
          const timeDiff = Math.abs(updTime - targetTime);
          
          logger.debug(`예약 ID ${booking.book_id} 시간 차이: ${timeDiff}ms`);
          
          if (timeDiff < minTimeDiff) {
            minTimeDiff = timeDiff;
            bestMatch = booking;
          }
        }
      }
    }
    
    if (bestMatch) {
      logger.info(`고객 ID ${customerId}에 대한 최적 예약 매치 찾음: ${bestMatch.book_id}, 시간 차이: ${minTimeDiff}ms`);
    } else {
      logger.info(`고객 ID ${customerId}에 대한 적합한 예약을 찾지 못했습니다.`);
    }
    
    return bestMatch;
  }

  async handleBookingCreation(response, request) {
    await handleBookingCreateResponse(response.url(), response, this.maps.requestMap, this.accessToken, this.maps);
  }

  async _handleCancelingBookings(data, customerService) {
    console.log(`[INFO] 자동 취소 기능이 자동 팝업 클릭 방식으로 변경되었습니다. /owner/booking 응답에서 취소 예약 감지는 비활성화되었습니다.`);
    // 이 기능은 autoCancelService._clickCancelConfirmButton()로 대체되었으며,
    // 취소 팝업이 감지되면 직접 취소 버튼을 클릭하는 방식으로 변경되었습니다.
    return;
  }

  async _processAppBookings(data, customerService) {
    if (!data.results || !Array.isArray(data.results)) return;

    // window 대신 global 사용 (메인 프로세스 환경)
    if (global.currentProcessingModalType === 'cancel') {
        console.log(`[INFO] 취소 모달 처리 중, 앱 예약 생성 처리 건너뛰기`);
        return;
    }
    
    // customerService에 최근 업데이트된 고객 ID가 없으면 처리하지 않음
    if (!customerService || !customerService.recentCustomerIds || customerService.recentCustomerIds.size === 0) {
      console.log(`[INFO] 최근 업데이트된 고객 정보 없음, 앱 예약 처리 건너뛰기`);
      return;
    }
    
    console.log(`[INFO] 최근 업데이트된 고객(${Array.from(customerService.recentCustomerIds).join(', ')})에 대한 예약 확인 중...`);
    
    // 시간 기반 매칭을 위한 최대 시간 차이 (밀리초)
    const MAX_TIME_DIFF = 60 * 1000; // 60초
    
    // 이미 처리된 예약 ID를 추적하는 Set
    const processedBookIds = new Set();
    
    // 고객 ID 목록을 복사 (처리 중 삭제를 위해)
    const customerIds = Array.from(customerService.recentCustomerIds);
    
    for (const customerId of customerIds) {
      const customerUpdate = customerService.customerUpdates?.get(customerId);
      if (!customerUpdate) continue;
      
      // 최근 업데이트 시간
      const updateTime = customerUpdate.updateTime;
      console.log(`[INFO] 고객 ID ${customerId}의 최근 업데이트 시간: ${new Date(updateTime).toISOString()}`);
      
      // 해당 고객 ID와 관련된 예약 찾기
      const customerBookings = data.results.filter(booking => 
        booking.book_id && 
        booking.customer == customerId && 
        !this.maps.processedBookings.has(booking.book_id) && 
        !this.processedAppBookings.has(booking.book_id) && 
        !this.processingBookingRequests.has(booking.book_id) &&
        !processedBookIds.has(booking.book_id) &&  // 이미 처리된 예약 제외
        (booking.state === 'success' || booking.confirmed_by === 'IM' || booking.immediate_booked === true) &&
        booking.state !== 'canceling' && booking.state !== 'canceled' // 취소 중이거나 취소된 예약 명시적 제외
      );
      
      if (customerBookings.length === 0) {
        console.log(`[INFO] 고객 ID ${customerId}에 대한 처리 가능한 예약 없음`);
        customerService.recentCustomerIds.delete(customerId);  // 처리할 예약이 없는 경우도 고객 ID 제거
        continue;
      }
      
      console.log(`[INFO] 고객 ID ${customerId}에 대한 예약 후보 ${customerBookings.length}개 발견`);
      
      // 시간 기반 매칭: 고객 정보 업데이트 시간과 가장 가까운 예약 찾기
      let bestMatch = null;
      let minTimeDiff = Infinity;
      let bestPriority = -Infinity;  // 우선순위 비교용
      
      for (const booking of customerBookings) {
        // 예약의 업데이트 시간 추출
        let bookingUpdTime = null;
        if (booking.customer_detail?.customerinfo_set?.length > 0) {
          bookingUpdTime = new Date(booking.customer_detail.customerinfo_set[0].upd_date).getTime();
        } else if (booking.updated_at) {
          bookingUpdTime = new Date(booking.updated_at).getTime();
        } else {
          console.log(`[WARN] 예약 ID ${booking.book_id}에 업데이트 시간 정보 없음, 건너뛰기`);
          continue;
        }
        
        const timeDiff = Math.abs(bookingUpdTime - updateTime);
        console.log(`[DEBUG] 예약 ID ${booking.book_id} 시간 차이: ${timeDiff}ms`);
        
        if (timeDiff < MAX_TIME_DIFF) {
          // 시간 차이가 같은 경우 우선순위로 결정
          let priority = 0;
          
          // 1. 즉시확정 예약이 우선
          if (booking.immediate_booked === true) priority += 10;
          if (booking.confirmed_by === 'IM') priority += 5;
          
          // 2. 예약 ID 길이가 짧을수록 우선 (최근 예약일 가능성)
          priority -= booking.book_id.length;
          
          // 3. room 번호가 작을수록 우선
          if (booking.room) {
            priority -= parseInt(booking.room, 10) || 0;
          }
          
          if (timeDiff < minTimeDiff || (timeDiff === minTimeDiff && priority > bestPriority)) {
            minTimeDiff = timeDiff;
            bestPriority = priority;
            bestMatch = booking;
          }
        }
      }
      
      if (bestMatch && minTimeDiff < MAX_TIME_DIFF) {
        console.log(`[INFO] 고객 ID ${customerId}에 대한 최적 예약 매치 찾음: ${bestMatch.book_id}, 시간 차이: ${minTimeDiff}ms`);


        // 이미 처리된 예약인지 글로벌 변수로 확인
        if (global.alreadyCreatedBookings && global.alreadyCreatedBookings.has(bestMatch.book_id)) {
            console.log(`[INFO] 이미 생성된 예약 ${bestMatch.book_id}에 대한 중복 처리 방지`);
            // 고객 ID를 처리 목록에서 제거
            customerService.recentCustomerIds.delete(customerId);
            console.log(`[INFO] 이미 생성된 예약으로 인해 고객 ID ${customerId} 목록에서 제거`);
            continue;
        }

        // 고객 ID를 처리 전에 즉시 제거 (중복 호출 방지)
        customerService.recentCustomerIds.delete(customerId);
        console.log(`[INFO] 고객 ID ${customerId} 처리 중이므로 목록에서 제거`);
        
        // 중복 요청 체크 강화 (직전 확인)
        if (this.processingBookingRequests.has(bestMatch.book_id) || 
            this.processedAppBookings.has(bestMatch.book_id) ||
            this.maps.processedBookings.has(bestMatch.book_id)) {
          console.log(`[INFO] 최종 중복 체크 - 예약 ID ${bestMatch.book_id}에 대한 요청 skip (이미 처리 중/완료)`);
          continue;
        }
        
        // 처리 중 상태로 표시
        this.processingBookingRequests.add(bestMatch.book_id);
        processedBookIds.add(bestMatch.book_id);  // 처리된 예약 목록에 추가
        
        const startDate = bestMatch.start_datetime ? convertKSTtoUTC(bestMatch.start_datetime) : null;
        const endDate = bestMatch.end_datetime ? convertKSTtoUTC(bestMatch.end_datetime) : null;
        
        // 결제 정보 계산 (is_paid 필드 우선)
        let amount = parseInt(bestMatch.amount || 0, 10);
        let finished = false;
        
        if (bestMatch.is_paid !== undefined) {
          finished = bestMatch.is_paid === true;
          console.log(`[DEBUG] book_id ${bestMatch.book_id}에 대해 is_paid 필드 사용: is_paid=${bestMatch.is_paid}, finished=${finished}`);
        } else if (bestMatch.revenue_detail?.finished !== undefined) {
          finished = bestMatch.revenue_detail.finished === true || bestMatch.revenue_detail.finished === 'true';
          console.log(`[DEBUG] book_id ${bestMatch.book_id}에 대해 revenue_detail.finished 사용: revenue_detail.finished=${bestMatch.revenue_detail.finished}, finished=${finished}`);
        } else if (bestMatch.payment) {
          amount = parseInt(bestMatch.payment.amount || bestMatch.amount || 0, 10);
          finished = true;
          console.log(`[DEBUG] book_id ${bestMatch.book_id}에 대해 payment 객체 존재: payment exists, finished=${finished}`);
        }
        
        const bookingData = {
          externalId: bestMatch.book_id,
          name: bestMatch.name || 'Unknown',
          phone: bestMatch.phone || '010-0000-0000',
          partySize: parseInt(bestMatch.person || 1, 10),
          startDate: startDate,
          endDate: endDate,
          roomId: bestMatch.room?.toString() || 'unknown',
          hole: bestMatch.hole,
          paymented: finished,
          paymentAmount: amount,
          crawlingSite: 'KimCaddie',
          immediate: bestMatch.immediate_booked === true || bestMatch.confirmed_by === 'IM'
        };
        
        console.log(`[DEBUG] 즉시확정 예약에 대한 최종 API 데이터:`, JSON.stringify(bookingData, null, 2));
        
        // -- 중요 변경사항: 로그 출력만 하고 실제 API 호출은 하지 않도록 수정 --
        // 실제 API 호출은 _createBookingWithLock 함수를 통해 수행
        try {
          // 예약 생성 전에 처리 완료로 표시 (중복 호출 방지)
          this.processedAppBookings.add(bestMatch.book_id);
          
          // 락 메커니즘을 통한 예약 생성 - 중복 호출 방지
          await this._createBookingWithLock(bookingData);
          console.log(`[INFO] 앱 예약 생성 처리됨. book_id: ${bestMatch.book_id}, 고객 ID: ${customerId}`);
        } catch (error) {
          if (error.response?.status === 500 && error.response?.data?.message?.includes('duplicate key error')) {
            console.log(`[INFO] 예약 ${bestMatch.book_id} 이미 존재함 (duplicate key), 성공으로 처리`);
          } else {
            console.error(`[ERROR] 예약 생성 실패: ${error.message}`);
            // 실패한 경우 processedAppBookings에서 제거하여 재시도 가능하게 함
            this.processedAppBookings.delete(bestMatch.book_id);
          }
        } finally {
          // 처리 중 상태 해제
          this.processingBookingRequests.delete(bestMatch.book_id);
        }
      } else {
        console.log(`[INFO] 고객 ID ${customerId}에 대한 시간 기반 매칭 예약 없음`);
        // 시간 기반 매칭 예약이 없는 경우도 고객 ID 제거
        customerService.recentCustomerIds.delete(customerId);
        console.log(`[INFO] 고객 ID ${customerId} 매칭 예약 없어 목록에서 제거`);
      }
    }
  }

  async _createBooking(data) {

    // 3번 수정사항: 취소된 예약 ID 체크
    if (this.canceledBookingIds.has(data.externalId)) {
        console.log(`[INFO] Skipping creation for recently canceled booking: ${data.externalId}`);
        return; // 이미 취소된 예약이면 생성 건너뛰기
    }

    // 추가: 이미 등록 API가 호출된 예약인지 확인
    if (global.alreadyCreatedBookings && global.alreadyCreatedBookings.has(data.externalId)) {
        console.log(`[INFO] Skipping duplicate API call for already created booking: ${data.externalId}`);
        return;
    }

    const token = this.accessToken || await getAccessToken();
    console.log(`[DEBUG] Original apiData (before corrections):`, JSON.stringify(data, null, 2));
    
    // 시간 데이터 모든 필드에 대해 타임존 정보 확인 및 보정
    const correctedData = {...data};
    
    if (correctedData.startDate) {
      console.log(`[DEBUG] Checking time data format: ${correctedData.startDate}`);
      const hasTimezone = correctedData.startDate.endsWith('Z') || 
                          correctedData.startDate.includes('+') || 
                          correctedData.startDate.includes('-', 10);  // DateTime 중간에 오는 - 제외
      
      if (!hasTimezone) {
        console.log(`[DEBUG] Adding timezone info to startDate: ${correctedData.startDate}`);
        correctedData.startDate = new Date(correctedData.startDate).toISOString();
      } else {
        console.log(`[DEBUG] Time data already has timezone info: ${correctedData.startDate}`);
      }
      console.log(`[DEBUG] StartDate corrected: ${data.startDate} -> ${correctedData.startDate}`);
    }
    
    if (correctedData.endDate) {
      console.log(`[DEBUG] Checking time data format: ${correctedData.endDate}`);
      const hasTimezone = correctedData.endDate.endsWith('Z') || 
                          correctedData.endDate.includes('+') || 
                          correctedData.endDate.includes('-', 10);
      
      if (!hasTimezone) {
        console.log(`[DEBUG] Adding timezone info to endDate: ${correctedData.endDate}`);
        correctedData.endDate = new Date(correctedData.endDate).toISOString();
      } else {
        console.log(`[DEBUG] Time data already has timezone info: ${correctedData.endDate}`);
      }
      console.log(`[DEBUG] EndDate corrected: ${data.endDate} -> ${correctedData.endDate}`);
    }
    
    // immediate 필드 제거 (API 호환성)
    if (correctedData.immediate !== undefined) {
      delete correctedData.immediate;
    }
    
    console.log(`[DEBUG] Final Booking_Create API data:`, JSON.stringify(correctedData, null, 2));
    
    await sendTo24GolfApi('Booking_Create', '', {}, correctedData, token, 
      this.maps.processedBookings, this.maps.paymentAmounts, this.maps.paymentStatus);
  }

  async _cancelBooking(bookId) {
    const token = this.accessToken || await getAccessToken();
    console.log(`[INFO] Processing Booking_Cancel for book_id: ${bookId}`);
    try {
      await sendTo24GolfApi('Booking_Cancel', '', { 
        canceled_by: 'App User', 
        externalId: bookId 
      }, null, token, this.maps.processedBookings, 
      this.maps.paymentAmounts, this.maps.paymentStatus);
      console.log(`[INFO] Successfully canceled booking: ${bookId}`);


        // 여기에 2번 수정사항 추가
        console.log(`[INFO] Fetching latest booking data after cancellation`);
        await this._fetchLatestBookingsInfo(); // 최신 예약 데이터 강제 로드

        // 여기에 3번 수정사항 추가
        this.canceledBookingIds.add(bookId); // 취소된 예약 ID를 Set에 추가
        console.log(`[INFO] Added ${bookId} to canceled bookings list to prevent recreation`);

    } catch (error) {
      if (error.response?.status === 400 && error.response?.data?.error === 'ALREADY_CANCELLED') {
        console.log(`[INFO] Booking ${bookId} was already canceled, marking as processed`);
      } else {
        console.error(`[ERROR] Failed to cancel booking ${bookId}: ${error.message}`);
        throw error; // 에러를 다시 던져서 호출자가 처리할 수 있도록 함
      }
    }
  }

  async _checkLatestBookingData(bookId) {
    if (!this.bookingDataCache.data?.results) return false;

    const booking = this.bookingDataCache.data.results.find(item => item.book_id === bookId);
    if (booking) {
      const revenueDetail = booking.revenue_detail || {};
      let amount = parseInt(revenueDetail.amount || booking.amount || 0, 10);
      let finished = revenueDetail.finished === true || revenueDetail.finished === 'true';

      if (!booking.revenue_detail && booking.payment) {
        amount = parseInt(booking.payment.amount || booking.amount || 0, 10);
        finished = booking.is_paid === true;
      } else if (booking.revenue_detail && booking.is_paid) {
        finished = booking.is_paid === true;
      }

      console.log(`[INFO] Found latest booking data for book_id ${bookId} in cache: amount=${amount}, finished=${finished}`);
      if (amount > 0) {
        this.maps.paymentAmounts.set(bookId, amount);
        console.log(`[INFO] Updated payment amount for book_id ${bookId} from cached data: ${amount}`);
      }
      this.maps.paymentStatus.set(bookId, finished);
      return true;
    }

    console.log(`[DEBUG] No latest booking data found in cache for book_id ${bookId}`);
    return false;
  }
}

module.exports = BookingService;