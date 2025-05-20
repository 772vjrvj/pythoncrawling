// response.js
const { sendTo24GolfApi, getAccessToken } = require('../utils/api');
const BookingService = require('../services/bookingService');
const CustomerService = require('../services/customerService');
const RevenueService = require('../services/revenueService');
const { parseMultipartFormData } = require('../utils/parser');

// 전역 상태 관리
let processedCustomerRequests = new Set();
let bookingDataCache = { timestamp: 0, data: null };

/**
 * 응답 핸들러 설정
 * @param {Object} page - Puppeteer 페이지 인스턴스
 * @param {string} accessToken - 액세스 토큰
 * @param {Object} maps - 공유 맵 객체 
 * @param {Object} modalDetectionService - 모달 감지 서비스 (선택적)
 */
const setupResponseHandler = (page, accessToken, maps, modalDetectionService) => {
  const bookingService = new BookingService(maps, accessToken, bookingDataCache);
  const customerService = new CustomerService(maps, accessToken, processedCustomerRequests, bookingDataCache);
  const revenueService = new RevenueService(maps, accessToken);

  page.on('response', async (response) => {
    const url = response.url();
    const status = response.status();
    const request = response.request();
    const method = request.method();

    if (!url.includes('api.kimcaddie.com/api/')) return;
    
    // 오류 응답 감지 및 로깅
    if (status >= 400) {
      try {
        let responseText = '';
        try {
          const responseData = await response.json();
          responseText = JSON.stringify(responseData);
        } catch (e) {
          responseText = await response.text();
        }
        
        console.error(`[ERROR] API Error: ${url} (${status}) - ${responseText}`);
        
        // 오류 응답일 경우 페이지 HTML 캡처
        /*if (modalDetectionService) {
          await modalDetectionService.captureFullPageHTML('error_response', `${status}_${method}_${url.split('/').pop()}`);
        }*/
        
        return;
      } catch (error) {
        console.error(`[ERROR] Failed to capture error response: ${error.message}`);
        return;
      }
    }

    try {
      // 모달 감지 서비스를 BookingService와 CustomerService에 전달
      if (modalDetectionService) {
        if (!bookingService.modalDetectionService) {
          bookingService.modalDetectionService = modalDetectionService;
        }
        if (!customerService.modalDetectionService) {
          customerService.modalDetectionService = modalDetectionService;
        }
        if (!revenueService.modalDetectionService) {
          revenueService.modalDetectionService = modalDetectionService;
        }
      }

      // API 엔드포인트별 핸들러 매핑
      const handlers = {
        '/api/booking/confirm_state': async () => {
          if (method === 'PATCH') {
            /*if (modalDetectionService) {
              // 예약 상태 변경 응답 시 페이지 캡처
              await modalDetectionService.captureFullPageHTML('confirm_state_response', `${method}_${Date.now()}`);
            }*/
            return bookingService.handleBookingConfirmation(request);
          }
        },
        '/api/owner/customer/': async () => {
          if (method === 'GET') {
            // 고객 응답 데이터를 받으면 페이지 캡처
            if (modalDetectionService) {
              const requestUrl = request.url();
              const customerId = extractIdFromUrl(requestUrl, 'customer');
              /*if (customerId) {
                await modalDetectionService.captureFullPageHTML('customer_response', customerId);
              }*/
            }
            return customerService.handleCustomerResponse(response);
          }
        },
        '/owner/booking/': async () => {
          if (method === 'GET') {
            // 예약 목록 응답을 받으면 페이지 캡처
            /*if (modalDetectionService) {
              await modalDetectionService.captureFullPageHTML('booking_list', `${Date.now()}`);
            }*/
            return bookingService.handleBookingList(response, customerService);
          }
        },
        '/owner/revenue/': async () => {
          const requestUrl = request.url();
          const revenueId = extractIdFromUrl(requestUrl, 'revenue');
          
          /*if (modalDetectionService && revenueId) {
            await modalDetectionService.captureFullPageHTML('revenue_response', `${revenueId}_${method}`);
          }*/
          
          if (method === 'PATCH') return revenueService.handleRevenueUpdate(response, request);
          if (method === 'POST') return revenueService.handleRevenueCreation(response, request);
        },
        '/owner/booking': async () => {
          if (method === 'POST' && (status === 200 || status === 201)) {
            // 예약 생성 응답을 받으면 페이지 캡처
            if (modalDetectionService) {
              try {
                const responseData = await response.clone().json();
                const bookId = responseData.book_id || 'unknown';
                //await modalDetectionService.captureFullPageHTML('booking_created', bookId);
              } catch (error) {
                console.error(`[ERROR] Failed to capture booking creation response: ${error.message}`);
              }
            }
            return bookingService.handleBookingCreation(response, request);
          }
        }
      };

      // 매칭되는 핸들러 실행
      const handlerKey = Object.keys(handlers).find(key => url.includes(key));
      if (handlerKey) await handlers[handlerKey]();

    } catch (error) {
      console.error(`[ERROR] Error handling response for ${url}: ${error.message}`);
      console.error(`[ERROR] Stack trace:`, error.stack);
      
      // 예외 발생 시 페이지 캡처
      /*if (modalDetectionService) {
        await modalDetectionService.captureFullPageHTML('error_handler', `${url.split('/').pop()}_${Date.now()}`);
      }*/
    }
  });
};

/**
 * URL에서 ID 추출하는 유틸리티 함수
 * @param {string} url - API URL
 * @param {string} type - ID 유형 (customer, revenue, 등)
 * @returns {string|null} - 추출된 ID
 */
function extractIdFromUrl(url, type) {
  try {
    const regex = new RegExp(`/${type}/(\\d+)`);
    const match = url.match(regex);
    return match ? match[1] : null;
  } catch (error) {
    console.error(`[ERROR] Failed to extract ${type} ID from URL: ${url}`, error);
    return null;
  }
}

module.exports = { setupResponseHandler };