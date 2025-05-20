/**
 * 모달 감지 서비스
 * 취소 모달 처리 유지, 예약 모달은 API 호출 기반 감지
 * 시스템 부하 최소화
 */
const fs = require('fs');
const path = require('path');

class ModalDetectionService {
  constructor() {
    this.currentPage = null;
    this.isObserverSetup = false;
    this.isProcessing = false;
    this.autoCancelEnabled = true;
    this.debugMode = false; // 로깅 레벨 제어
    this.closeButtonClicked = new Set(); // 닫기 버튼 클릭 추적을 위한 Set 추가
  }

  // 캡처 디렉토리 생성 함수 비활성화
  _createCaptureDirectories() {
    // 파일 시스템 접근 관련 코드 비활성화
    console.log('[INFO] HTML capture directories creation disabled');
  }

  async _safeWait(ms) {
    try {
      await new Promise(resolve => setTimeout(resolve, ms));
    } catch (error) {
      console.warn(`[WARN] Wait failed: ${error.message}`);
    }
  }

  setCurrentPage(page) {
    this.currentPage = page;
    console.log('[INFO] Puppeteer page set');
    // 캡처 디렉토리 생성 함수 호출 비활성화
    //this._createCaptureDirectories();
    this._setupPuppeteerPageMonitoring();
  }

  setAutoCancelEnabled(enabled) {
    this.autoCancelEnabled = enabled;
    console.log(`[INFO] Auto-cancel ${enabled ? 'enabled' : 'disabled'}`);
  }

  setDebugMode(enabled) {
    this.debugMode = enabled;
    console.log(`[INFO] Debug mode ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Puppeteer 페이지 모니터링 설정
   * 수정: API 호출과 MutationObserver로 모달 감지
   */
  async _setupPuppeteerPageMonitoring() {
    if (!this.currentPage || this.isObserverSetup) return;

    try {
      await this._injectModalDetectionScript();

      this.currentPage.on('domcontentloaded', async () => {
        console.log('[INFO] DOM content loaded, reinitializing');
        await this._reinitializeModalDetection();
      });

      this.currentPage.on('framenavigated', async (frame) => {
        if (frame === this.currentPage.mainFrame()) {
          const url = await frame.url();
          console.log(`[INFO] Page navigated to: ${url}`);
          console.log('[INFO] Navigation detected, reinitializing');
          await this._reinitializeModalDetection();
        }
      });

      // 새로운 이벤트 리스너 추가
this.currentPage.on('console', async (msg) => {
  const text = msg.text();
  
  // 취소 모달 감지 이벤트 확인
  if (text.includes('[Browser] Cancel modal detection event received')) {
    console.log('[INFO] Cancel modal detection event detected from browser');
    
    // 전역 변수 설정 (Node.js 환경)
    global.currentProcessingModalType = 'cancel';
    console.log('[INFO] Global context: Set currentProcessingModalType to cancel');
    
    // 취소 모달 처리
    await this._handleCancelModal();
  }
  
  // 나머지 로그 처리
  if (text.includes('[Browser]')) {
    // 불필요한 로그는 출력하지 않음
    if (text.includes('Modal processing in progress, skipping') && !this.debugMode) {
      return;
    }
    // MutationObserver 관련 중복 로그는 출력하지 않음 
    if (text.includes('MutationObserver setup') && !this.debugMode) {
      return;
    }
    console.log(text);
  }
});

      await this.currentPage.evaluate((debugMode) => {
        window.__debugMode = debugMode;
        if (window.__checkForModals) window.__checkForModals();
      }, this.debugMode);

      this.isObserverSetup = true;
      console.log('[INFO] Modal detection setup complete');
    } catch (error) {
      console.error(`[ERROR] Setup failed: ${error.message}`);
    }
  }

  // src/services/modalDetectionService.js - _reinitializeModalDetection 함수 수정

async _reinitializeModalDetection() {
  try {
    await this.currentPage.waitForFunction(() => document.readyState === 'complete', { timeout: 5000 }).catch(() => {});
    await this.currentPage.waitForSelector('body', { timeout: 5000 }).catch(() => {
      console.log('[WARN] Main content not found, proceeding');
    });

    // 현재 URL 확인
    const currentUrl = await this.currentPage.url();
    console.log(`[INFO] Reinitializing modal detection on page: ${currentUrl}`);

    await this.currentPage.evaluate(() => {
      // 모달 관련 상태 초기화 (예약 버튼 클릭 상태는 초기화하지 않음)
      console.log('[Browser] 페이지 전환 감지 - 모달 감지 상태 초기화 (예약 버튼 클릭 상태 유지)', true);
      
      // 로컬 스토리지에서 예약 버튼 클릭 상태 로드
      try {
        const savedValue = localStorage.getItem('kimcaddie_reservation_button_clicked');
        window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = (savedValue === 'true');
        window.__hasClickedReservationButton = window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON; 
        console.log('[Browser] 로컬 스토리지에서 예약 버튼 클릭 상태 로드: ' + window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON, true);
      } catch (e) {
        // 로컬 스토리지 접근 실패 시 기존 값 유지
        console.log('[Browser] 로컬 스토리지 읽기 실패, 기존 클릭 상태 유지: ' + window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON, true);
      }
      
      // 전역 예약 버튼 클릭 상태는 유지하되 로그 출력
      console.log('[Browser] 전역 예약 버튼 클릭 상태 유지: ' + (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON ? 'true' : 'false'), true);
      
      // 모달 관련 상태 초기화
      window.__modalProcessing = false;
      window.__lastModalHTML = ''; 
      window.__lastModalTextFingerprint = null;
      window.__modalProcessingStartTime = null;
      window.__modalObserverSetup = false;
      window.__closeButtonClicked = {}; // 중요: 닫기 버튼 클릭 상태 객체 초기화 추가
      
      // 타이머 클리어
      if (window.__modalProcessingTimer) {
        clearTimeout(window.__modalProcessingTimer);
        window.__modalProcessingTimer = null;
      }
    });

    // 모달 감지 스크립트 다시 주입 및 초기 검사
    await this._injectModalDetectionScript();
    
    // 중요: API 응답 모니터링을 위한 스크립트 추가
    await this.currentPage.evaluate(() => {
      // 예약 목록 API 응답 및 클릭 후 모달 감지 강화
      const originalXhrOpen = window.XMLHttpRequest.prototype.open;
      const originalXhrSend = window.XMLHttpRequest.prototype.send;
      
      // 이미 인터셉터가 설정되어 있는지 확인 (중복 방지)
      if (!window.__enhancedXhrMonitoringSetup) {
        window.XMLHttpRequest.prototype.open = function(...args) {
          this._enhancedUrl = args[1]; // URL 저장
          return originalXhrOpen.apply(this, args);
        };
        
        window.XMLHttpRequest.prototype.send = function(...args) {
          const xhr = this;
          const url = xhr._enhancedUrl;
          
          // 예약 목록 API 응답 후 모달 감지 강화
          if (url && url.includes('/owner/booking/')) {
            xhr.addEventListener('load', function() {
              if (xhr.status === 200) {
                console.log('[Browser] 예약 목록 API 응답 감지, 모달 체크 예약', true);
                
                // 여러 시점에 반복 체크 (연속 모달 처리 강화)
                [500, 1500, 3000, 5000].forEach(delay => {
                  setTimeout(() => {
                    if (typeof window.__checkForModals === 'function' && !window.__modalProcessing) {
                      console.log(`[Browser] 예약 목록 API 응답 후 ${delay}ms 모달 체크 실행`, true);
                      window.__checkForModals();
                    }
                  }, delay);
                });
              }
            });
          }
          
          // 예약 취소 API 응답 후 특별 처리
          if (url && url.includes('/booking/change_info/')) {
            xhr.addEventListener('load', function() {
              if (xhr.status === 200) {
                console.log('[Browser] 예약 취소 API 응답 감지, 모달 감지 강화', true);
                
                // 예약 버튼 클릭 상태 초기화 (안전 조치)
                window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = false;
                try {
                  localStorage.setItem('kimcaddie_reservation_button_clicked', 'false');
                } catch (e) {}
                
                // 강화된 모달 체크 일정
                [300, 1000, 2000, 3000, 5000, 8000].forEach(delay => {
                  setTimeout(() => {
                    if (typeof window.__checkForModals === 'function' && !window.__modalProcessing) {
                      console.log(`[Browser] 예약 취소 API 응답 후 ${delay}ms 모달 체크 실행`, true);
                      window.__checkForModals();
                    }
                  }, delay);
                });
              }
            });
          }
          
          return originalXhrSend.apply(this, args);
        };
        
        window.__enhancedXhrMonitoringSetup = true;
        console.log('[Browser] 강화된 API 응답 모니터링 설정 완료', true);
      }
    });
    
    await this.currentPage.evaluate((debugMode) => {
      window.__debugMode = debugMode;
      
      // 강제로 모달 검사 실행
      if (window.__checkForModals) {
        console.log('[Browser] 페이지 전환 후 모달 강제 검사 실행', true);
        window.__checkForModals();
      }
    }, this.debugMode);

    console.log('[INFO] Modal detection completely reinitialized');
  } catch (error) {
    console.error(`[ERROR] Reinitialization failed: ${error.message}`);
  }
}

  /**
   * 모달 감지 스크립트 주입
   * 수정:
   * - 예약 모달: customer API 호출 감지 개선
   * - 취소 모달: 텍스트 기반 MutationObserver 감지
   * - 불필요한 로깅 제거
   */
  async _injectModalDetectionScript() {
    try {
      await this.currentPage.evaluate(() => {
        if (window.__modalObserverSetup) return;
  
        // window 전역 객체에 직접 설정하여 함수 호출 간에도 유지되도록 함
        window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON || false;
   

        // 예약 접수 모달 감지 후 페이지 이동 여부 확인 (무한 루프 방지)
try {
  // 마지막 예약 접수 처리 시간 확인 (5초 이내라면 무시)
  const lastBookingRequestTimestamp = parseInt(localStorage.getItem('kimcaddie_booking_request_timestamp') || '0');
  const currentTime = Date.now();
  
  // 5초 이내에 처리된 요청이라면 초기화
  if (currentTime - lastBookingRequestTimestamp < 5000) {
    window.__log('[Browser] Recently processed booking request detected, clearing state', true);
    localStorage.removeItem('kimcaddie_booking_request_processed');
    localStorage.removeItem('kimcaddie_booking_request_timestamp');
  }
} catch (e) {
  // 로컬 스토리지 접근 실패 시 무시
  console.error('[Browser] Error checking booking request state:', e);
}

        // 로컬 스토리지에서 상태 로드
        try {
          const savedValue = localStorage.getItem('kimcaddie_reservation_button_clicked');
          window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = (savedValue === 'true');
          console.log('[Browser] 로컬 스토리지에서 예약 버튼 클릭 상태 로드: ' + window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON, true);
        } catch (e) {
          // 로컬 스토리지 접근 실패 시 기존 값 유지
          console.log('[Browser] 로컬 스토리지 읽기 실패, 기존 클릭 상태 유지: ' + (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON ? 'true' : 'false'), true);
        }
  
        // 디버그 모드 전역 변수 설정 (기본값: false)
        if (typeof window.__debugMode === 'undefined') {
          window.__debugMode = false;
        }

        // 닫기 버튼 클릭 추적을 위한 변수 추가
        window.__closeButtonClicked = window.__closeButtonClicked || {};
  
        console.log('[Browser] 전역 예약 버튼 클릭 상태: ' + (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON ? 'true' : 'false'), true);
  
        // 예약 페이지 이동 버튼을 클릭했는지 추적하는 플래그 추가 (여기에 추가)
        if (typeof window.__hasClickedReservationButton === 'undefined') {
          window.__hasClickedReservationButton = window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON;
        }
  
        // 예약 버튼 클릭 플래그 저장 함수
        window.__saveReservationButtonClicked = function(clicked) {
          window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = clicked;
          window.__hasClickedReservationButton = clicked;
          try {
            localStorage.setItem('kimcaddie_reservation_button_clicked', clicked ? 'true' : 'false');
            console.log('[Browser] 예약 버튼 클릭 상태를 저장했습니다: ' + clicked, true);
          } catch (e) {
            console.error('[Browser] 예약 버튼 클릭 상태 저장 실패: ', e);
          }
        };
  
        // 조건부 로깅 함수
        window.__log = function(message, force = false) {
          if (window.__debugMode || force) {
            console.log(message);
          }
        };
  
        window.__modalDetected = function(modalHTML, modalType) {
          window.__modalInfo = {
            html: modalHTML,
            type: modalType,
            timestamp: new Date().toISOString()
          };
          window.__log(`[Browser] Modal detected: ${modalType}`, true);
        };
  
        window.__checkForBookingModal = function() {
          // 전역 변수 확인
          console.log('[Browser] 현재 예약 버튼 클릭 상태: ' + (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON ? 'true' : 'false'), true);
          
          // 처리 중인 상태라면 건너뛰기
          if (window.__modalProcessing) {
            window.__log('[Browser] 이미 모달 처리 중, 건너뛰기');
            return false;
          }
        
          window.__log('[Browser] 김캐디 즉시확정 예약 모달 확인 중...');
          try {
            const modalSelectors = [
              '.MuiPaper-root.MuiCard-root',
              '[role="dialog"]',
              '[role="presentation"]',
              '.MuiModal-root',
              '[class*="modal"]',
              'body > div:not([id="root"])' // 포털 감지
            ];
        
            let foundModal = false;
        
            for (const selector of modalSelectors) {
              const elements = Array.from(document.querySelectorAll(selector));
              for (const el of elements) {
                // 모달 텍스트를 통한 김캐디 즉시확정 모달 식별
                if (el.textContent && el.textContent.includes('김캐디 즉시확정 예약')) {
                  console.log('[Browser] 김캐디 즉시확정 예약 모달 감지됨!', true);
                  
                  // 모달 감지 시 즉시 상태 설정
                  window.__modalProcessing = true;
                  window.__modalProcessingStartTime = Date.now();
                  
                  // 모달 ID 생성 (시간 기반)
                  const modalId = 'modal_' + Date.now();
                  
                  // 이미 버튼을 클릭했다면 닫기 버튼만 처리
                  if (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON) {
                    console.log('[Browser] 이미 예약 페이지 이동 버튼을 클릭했습니다. 닫기 버튼만 처리합니다.', true);
                    
                    // SVG 닫기 버튼 클릭 (5초 지연)
                    const svgElements = document.querySelectorAll('.MuiPaper-root svg.MuiSvgIcon-root');
                    if (svgElements && svgElements.length > 1) {
                      console.log('[Browser] 닫기 버튼을 5초 후에 클릭하도록 예약', true);
                      
                      // 닫기 버튼 클릭 상태 추적 (중복 클릭 방지)
                      if (window.__closeButtonClicked[modalId]) {
                        console.log('[Browser] 이 모달의 닫기 버튼은 이미 클릭 예약되었습니다. 중복 클릭 방지.', true);
                      } else {
                        window.__closeButtonClicked[modalId] = true;
                        
                        setTimeout(() => {
                          // 모달이 여전히 존재하는지 확인
                          const modalStillExists = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).some(
                            modal => modal.textContent && modal.textContent.includes('김캐디 즉시확정 예약')
                          );
                          if (modalStillExists) {
                            // 버튼 클릭 상태 재확인
                            if (window.__closeButtonClicked[modalId]) {
                              svgElements[1].dispatchEvent(new MouseEvent('click', { bubbles: true }));
                              console.log('[Browser] 5초 후 닫기 버튼을 클릭했습니다.', true);
                              
                              // *** 중요 수정: 닫기 버튼 클릭 후 상태 초기화 ***
                              // 닫기 버튼 클릭 후 약간의 지연 후 상태 초기화 (1초)
                              setTimeout(() => {
                                window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = false;
                                window.__saveReservationButtonClicked(false); // 로컬 스토리지에도 저장
                                console.log('[Browser] 모달 닫기 완료 후 예약 버튼 클릭 상태 초기화: false', true);
                                window.__modalProcessing = false;
                                delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                              }, 1000);
                            } else {
                              console.log('[Browser] 닫기 버튼 클릭이 취소되었습니다.', true);
                              window.__modalProcessing = false;
                            }
                          } else {
                            console.log('[Browser] 5초 후 모달이 이미 닫혀 있어 클릭하지 않음', true);
                            
                            // *** 중요 수정: 모달이 이미 닫혀 있어도 상태 초기화 ***
                            window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = false;
                            window.__saveReservationButtonClicked(false); // 로컬 스토리지에도 저장
                            console.log('[Browser] 모달이 이미 닫혀있어 예약 버튼 클릭 상태 초기화: false', true);
                            window.__modalProcessing = false;
                            delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                          }
                        }, 5000); // 5초
                      }
                    } else {
                      console.log('[Browser] 닫기 버튼을 찾지 못했습니다.', true);
                      // 닫기 버튼을 찾지 못한 경우에도 타이머로 상태 초기화
                      setTimeout(() => {
                        window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = false;
                        window.__saveReservationButtonClicked(false); // 로컬 스토리지에도 저장
                        console.log('[Browser] 닫기 버튼을 찾지 못해 예약 버튼 클릭 상태 초기화: false', true);
                        window.__modalProcessing = false;
                        delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                      }, 5000);
                    }
                    
                    foundModal = true;
                    break;
                  }
        
                  // 여기서부터 예약 페이지 이동 버튼 처리 로직 
                  let foundReservationButton = false;
                  
                  // 1. a 태그 기반 버튼 찾기 (href 속성이 있는 경우 우선)
                  const allLinks = Array.from(el.querySelectorAll('a'));
                  const reservationLink = allLinks.find(link => {
                    const text = (link.textContent || link.innerText || '').trim();
                    return text.includes('예약 페이지 이동') || text.includes('예약 페이지') || text.includes('이동');
                  });
                  
                  if (reservationLink) {
                    foundReservationButton = true;
                    console.log('[Browser] 예약 링크 발견', true);
                    
                    // 링크 클릭 시도
                    console.log('[Browser] 예약 링크 클릭 시도', true);
                    reservationLink.click();
                  }
                  
                  // 2. 클래스 기반 버튼 찾기
                  if (!foundReservationButton) {
                    const reservationButton = el.querySelector('.sc-jRqOxM.bzqhOB, .sc-jRqOxM, [class*="jRqOxM"]');
                    if (reservationButton) {
                      foundReservationButton = true;
                      console.log('[Browser] 클래스 기반 예약 버튼 발견', true);
                      
                      // 클릭 시도
                      console.log('[Browser] 클래스 기반 예약 버튼 클릭 시도', true);
                      reservationButton.click();
                    }
                  }
                  
                  // 예약 버튼을 찾았다면 상태 설정 및 닫기 버튼 처리
                  if (foundReservationButton) {
                    // 상태 설정
                    window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = true;
                    window.__saveReservationButtonClicked(true); // 로컬 스토리지에 저장
                    console.log('[Browser] 예약 페이지 이동 버튼 클릭 플래그 설정: true', true);

                    // 추가: 전역 변수 설정 - 모달에서 처리 중인 예약 ID 기록
                    window.__modalProcessingBookingId = bookId || Date.now().toString();
                    console.log(`[Browser] 모달에서 처리 중인 예약 ID 설정: ${window.__modalProcessingBookingId}`, true);
                                      
                    // SVG 닫기 버튼 클릭 (30초 지연)
                    const svgElements = document.querySelectorAll('.MuiPaper-root svg.MuiSvgIcon-root');
                    if (svgElements && svgElements.length > 1) {
                      console.log('[Browser] 닫기 버튼을 30초 후에 클릭하도록 예약', true);
                      
                      // 닫기 버튼 클릭 상태 추적 (중복 클릭 방지)
                      if (window.__closeButtonClicked[modalId]) {
                        console.log('[Browser] 이 모달의 닫기 버튼은 이미 클릭 예약되었습니다. 중복 클릭 방지.', true);
                      } else {
                        window.__closeButtonClicked[modalId] = true;
                        
                        setTimeout(() => {
                          // 모달이 여전히 존재하는지 확인
                          const modalStillExists = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).some(
                            modal => modal.textContent && modal.textContent.includes('김캐디 즉시확정 예약')
                          );
                          if (modalStillExists) {
                            // 버튼 클릭 상태 재확인
                            if (window.__closeButtonClicked[modalId]) {
                              svgElements[1].dispatchEvent(new MouseEvent('click', { bubbles: true }));
                              console.log('[Browser] 30초 후 닫기 버튼을 클릭했습니다.', true);
                              
                              // *** 중요 수정: 닫기 버튼 클릭 후 상태 초기화하지 않음 (예약 페이지로 이동 중) ***
                              setTimeout(() => {
                                window.__modalProcessing = false;
                                delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                              }, 1000);
                            } else {
                              console.log('[Browser] 닫기 버튼 클릭이 취소되었습니다.', true);
                              window.__modalProcessing = false;
                            }
                          } else {
                            console.log('[Browser] 30초 후 모달이 이미 닫혀 있어 클릭하지 않음', true);
                            window.__modalProcessing = false;
                            delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                          }
                        }, 30000); // 30초
                      }
                    } else {
                      console.log('[Browser] 닫기 버튼을 찾지 못했습니다.', true);
                      setTimeout(() => {
                        window.__modalProcessing = false;
                        delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                      }, 30000);
                    }
                  } else {
                    // 예약 버튼을 찾지 못한 경우 모달 닫기 시도 및 상태 초기화
                    console.log('[Browser] 예약 버튼을 찾지 못함, 모달 닫기 시도', true);
                    const svgElements = document.querySelectorAll('.MuiPaper-root svg.MuiSvgIcon-root');
                    if (svgElements && svgElements.length > 0) {
                      svgElements[svgElements.length > 1 ? 1 : 0].click();
                      console.log('[Browser] 닫기 버튼 즉시 클릭', true);
                    }
                    
                    // 버튼을 찾지 못했으므로 상태 초기화
                    window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = false;
                    window.__saveReservationButtonClicked(false);
                    console.log('[Browser] 예약 버튼을 찾지 못해 상태 초기화: false', true);
                    window.__modalProcessing = false;
                    delete window.__closeButtonClicked[modalId]; // 클릭 상태 제거
                  }
                  
                  foundModal = true;
                  break;
                }
              }
              if (foundModal) break;
            }
            
            return foundModal;
          } catch (error) {
            console.error('[Browser] 예약 모달 감지 오류:', error);
            // 오류 발생 시 안전하게 상태 초기화
            window.__modalProcessing = false;
            window.__modalProcessingStartTime = null;
            
            return false;
          }
        }
  
        // 모달 닫기 시도 함수 추가
        window.__dismissBookingModal = function(modalElement) {
          try {
            // 1. SVG 경로 기반 닫기 버튼
            const svgCloseButtons = Array.from(document.querySelectorAll('svg'));
            window.__log('[Browser] 대체 닫기: 발견된 총 SVG 요소 수: ' + svgCloseButtons.length, true);
            const svgCloseButton = svgCloseButtons.find(btn => {
              const path = btn.querySelector('path');
              return path && path.getAttribute('d').includes('M19');
            });
  
            if (svgCloseButton) {
                window.__log('[Browser] 대체 닫기: SVG path-based close button found', true);
            // 상위 클릭 가능 요소 확인
            let clickableElement = svgCloseButton;
            while (clickableElement && !['BUTTON', 'A', 'DIV'].includes(clickableElement.tagName)) {
              clickableElement = clickableElement.parentElement;
            }
            if (clickableElement) {
              window.__log('[Browser] 상위 클릭 가능 요소 발견: ' + clickableElement.tagName, true);
              clickableElement.click();
              setTimeout(() => {
                const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                clickableElement.dispatchEvent(clickEvent);
                window.__log('[Browser] 추가 이벤트 기반 클릭 시도', true);
              }, 100);
              return true;
            } else {
              window.__log('[Browser] 상위 클릭 가능 요소 없음, SVG 직접 클릭 시도', true);
              svgCloseButton.click();
              return true;
            }
          }
          } catch (error) {
            console.error('[Browser] Modal dismiss error:', error);
            window.__modalProcessing = false;
            return false;
          }
        };
  
        window.__checkForCancelModal = function() {
          if (window.__modalProcessing) {
            window.__log('[Browser] Modal processing in progress, skipping');
            return false;
          }
      
          window.__log('[Browser] Checking for cancel modal...');
          try {
            const modalSelectors = [
              '.MuiPaper-root.MuiCard-root',
              '[role="dialog"]',
              '[role="presentation"]',
              '.MuiModal-root',
              '[class*="modal"]',
              'body > div:not([id="root"])'
            ];
      
            let foundModal = false;
      
            for (const selector of modalSelectors) {
              const elements = Array.from(document.querySelectorAll(selector));
              for (const el of elements) {
                if (el.textContent.includes('김캐디 취소 접수')) {
                  window.__log('[Browser] 김캐디 취소 접수 modal detected', true);
                  
                  // 상태 알림용 커스텀 이벤트 발생
                  const event = new CustomEvent('cancel_modal_detected', { 
                    detail: { type: 'cancel' } 
                  });
                  document.dispatchEvent(event);
                  
                  const modalHTML = el.outerHTML;
                  if (window.__lastModalHTML === modalHTML) {
                    window.__log('[Browser] Same cancel modal, skipping');
                    continue;
                  }
      
                  window.__lastModalHTML = modalHTML;
                  window.__modalProcessing = true;
                  
                  // 이전 타이머 클리어
                  if (window.__modalProcessingTimer) {
                    clearTimeout(window.__modalProcessingTimer);
                  }
                  
                  // 새 타이머 설정
                  window.__modalProcessingTimer = setTimeout(() => {
                    window.__modalProcessing = false;
                    window.__log('[Browser] Modal processing timeout cleared', true);
                  }, 5000); // 5초로 단축
                  
                  window.__modalDetected(modalHTML, 'cancel');
                  foundModal = true;
                  break;
                }
              }
              if (foundModal) break;
            }
      
            return foundModal;
          } catch (error) {
            console.error('[Browser] Cancel modal detection error:', error);
            window.__modalProcessing = false;
            return false;
          }
        };

        window.__checkForBookingRequestModal = function() {
          if (window.__modalProcessing) {
            window.__log('[Browser] Modal processing in progress, skipping');
            return false;
          }
        
          // 현재 URL이 이미 booking 페이지인지 확인
          if (window.location.href.includes('owner.kimcaddie.com/booking')) {
            window.__log('[Browser] Already on booking page, skipping booking request modal check', true);
            return false;
          }
        
          window.__log('[Browser] Checking for booking request modal...');
          try {
            const modalSelectors = [
              '.MuiPaper-root.MuiCard-root',
              '[role="dialog"]',
              '[role="presentation"]',
              '.MuiModal-root',
              '[class*="modal"]',
              'body > div:not([id="root"])'
            ];
        
            let foundModal = false;
        
            for (const selector of modalSelectors) {
              const elements = Array.from(document.querySelectorAll(selector));
              for (const el of elements) {
                if (el.textContent && el.textContent.includes('김캐디 예약 접수')) {
                  window.__log('[Browser] 김캐디 예약 접수 modal detected', true);
                  
                  const modalHTML = el.outerHTML;
                  if (window.__lastModalHTML === modalHTML) {
                    window.__log('[Browser] Same booking request modal, skipping');
                    continue;
                  }
        
                  window.__lastModalHTML = modalHTML;
                  window.__modalProcessing = true;
                  
                  // 이전 타이머 클리어
                  if (window.__modalProcessingTimer) {
                    clearTimeout(window.__modalProcessingTimer);
                  }
                  
                  // 새 타이머 설정
                  window.__modalProcessingTimer = setTimeout(() => {
                    window.__modalProcessing = false;
                    window.__log('[Browser] Modal processing timeout cleared', true);
                  }, 5000); // 5초로 단축
                  
                  window.__modalDetected(modalHTML, 'booking_request');
                  
                  // 모달 감지 플래그 저장 (다음 페이지에서 무한 루프 방지)
                  try {
                    localStorage.setItem('kimcaddie_booking_request_processed', 'true');
                    localStorage.setItem('kimcaddie_booking_request_timestamp', Date.now().toString());
                    window.__log('[Browser] Booking request modal processed flag saved', true);
                  } catch (e) {
                    console.error('[Browser] Error saving booking request state:', e);
                  }
                  
                  // 페이지 이동 로직: 닫기 없이 바로 booking 페이지로 이동
                  try {
                    window.__log('[Browser] booking 페이지로 직접 이동합니다: https://owner.kimcaddie.com/booking', true);
                    window.location.href = 'https://owner.kimcaddie.com/booking';
                  } catch (error) {
                    console.error('[Browser] Booking request modal handling error:', error);
                    window.__modalProcessing = false;
                  }
                  
                  foundModal = true;
                  break;
                }
              }
              if (foundModal) break;
            }
        
            return foundModal;
          } catch (error) {
            console.error('[Browser] Booking request modal detection error:', error);
            window.__modalProcessing = false;
            return false;
          }
        };

        // 이벤트 리스너 추가
        document.addEventListener('cancel_modal_detected', function(e) {
          console.log('[Browser] Cancel modal detection event received:', e.detail.type);
        });

        // 여기에 새 이벤트 리스너 추가
document.addEventListener('booking_request_modal_detected', function(e) {
  console.log('[Browser] Booking request modal detection event received:', e.detail.type);
});
  
window.__checkForModals = function() {
  return window.__checkForBookingModal() || window.__checkForCancelModal() || window.__checkForBookingRequestModal();
};
  
        // 페이지 URL에 따라 모달 감지 일시 중지
        window.__shouldSkipModalDetection = function() {
          // 즉시 확정 예약은 어떤 페이지에서도 감지해야 함 - 항상 false 반환
          return false;
        };
  
        const setupMutationObserver = () => {
          if (window.__modalObserver) {
            window.__modalObserver.disconnect();
            window.__modalObserver = null;
          }
  
          // 감지 불필요한 페이지면 Observer 설정 안함
          if (window.__shouldSkipModalDetection()) {
            window.__log('[Browser] Skipping mutation observer setup on booking page');
            return;
          }
  
          const observer = new MutationObserver((mutations) => {
            if (window.__modalProcessing) return;
            
            // URL 변경 감지시 감지 여부 재평가
            if (window.__shouldSkipModalDetection()) return;
  
            let shouldCheck = false;
  
            for (const mutation of mutations) {
              if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                  if (node.nodeType === 1) {
                    const text = node.textContent || '';
                    if (text.includes('김캐디 즉시확정 예약') || text.includes('김캐디 취소 접수') || text.includes('김캐디 예약 접수')) {
                      shouldCheck = true;
                      window.__log('[Browser] Detected potential modal by text');
                      break;
                    }
                  }
                }
              }
  
              if (shouldCheck) break;
            }
  
            if (shouldCheck) {
              window.__log('[Browser] DOM changes detected, checking modals...', true);
              setTimeout(() => {
                if (!window.__modalProcessing) {
                  window.__checkForBookingModal() || window.__checkForCancelModal() || window.__checkForBookingRequestModal();
                }
              }, 100);
            }
          });
  
          observer.observe(document.documentElement, {
            childList: true,
            subtree: true
          });
  
          window.__modalObserver = observer;
          window.__log('[Browser] MutationObserver setup for modals');
        };
  
        // 이전에 사용하던 API 호출 감지 로직 개선
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
          const response = await originalFetch.apply(window, args);
          const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
          
          if (url && !window.__shouldSkipModalDetection()) {
            // 새로운 감지 로직: 고객 정보 API 호출 패턴 정확히 매치
            const customerApiPattern = /api\.kimcaddie\.com\/api\/owner\/customer\/\d+\//;
            if (customerApiPattern.test(url)) {
              window.__log('[Browser] Customer API call detected:' + url, true);
              
              // 고객 ID 추출
              const customerId = url.match(/\/customer\/(\d+)\//)?.[1];
              if (customerId) {
                window.__log(`[Browser] Detected customer ID: ${customerId}`, true);
                
                // API 호출 후 모달 검사 (지연 적용)
                setTimeout(() => {
                  if (!window.__modalProcessing && !window.__shouldSkipModalDetection()) {
                    window.__log('[Browser] Checking for booking modal after customer API call', true);
                    window.__checkForBookingModal();
                  }
                }, 1000);
                
                // 응답 복제 및 내용 검사
                try {
                  const clonedResponse = response.clone();
                  clonedResponse.json().then(data => {
                    window.__log(`[Browser] Customer API response received for ID: ${customerId}`, true);
                    
                    // 추가 모달 검사 (API 응답 후)
                    setTimeout(() => {
                      if (!window.__modalProcessing && !window.__shouldSkipModalDetection()) {
                        window.__log('[Browser] Second check for booking modal after API response', true);
                        window.__checkForBookingModal();
                      }
                    }, 2000);
                  }).catch(err => {
                    console.error('[Browser] Error parsing customer API response:', err);
                  });
                } catch (error) {
                  console.error('[Browser] Error processing API response:', error);
                }
              }
            }
            
            // 기존 감지 로직 유지 (소리 파일)
            if (url.includes('static.kimcaddie.com/owner/sound_booking_confirmed.mp3')) {
              window.__log('[Browser] Booking sound API call detected:' + url, true);
              setTimeout(() => {
                if (!window.__modalProcessing && !window.__shouldSkipModalDetection()) window.__checkForBookingModal();
              }, 1000);
            }
          }
  
          return response;
        };
  
        // 네트워크 요청 인터셉터 설정 (XHR)
        const originalXhrOpen = XMLHttpRequest.prototype.open;
        const originalXhrSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(...args) {
          this._url = args[1]; // URL 저장
          return originalXhrOpen.apply(this, args);
        };
        
        XMLHttpRequest.prototype.send = function(...args) {
          const xhr = this;
          const url = xhr._url;
          
          if (url && !window.__shouldSkipModalDetection()) {
            // 고객 정보 API 호출 감지
            const customerApiPattern = /api\.kimcaddie\.com\/api\/owner\/customer\/\d+\//;
            if (customerApiPattern.test(url)) {
              //window.__log('[Browser] XHR Customer API call detected:' + url, true);
              
              // 응답 완료 이벤트 리스너
              xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                  //window.__log('[Browser] XHR Customer API response received', true);
                  setTimeout(() => {
                    if (!window.__modalProcessing && !window.__shouldSkipModalDetection()) window.__checkForBookingModal();
                  }, 1000);
                }
              });
            }
          }
          
          return originalXhrSend.apply(this, args);
        };
  
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
  
        history.pushState = function(...args) {
          const oldUrl = window.location.href;
          originalPushState.apply(history, args);
          const newUrl = window.location.href;
          
          // 불필요한 로그 제한: URL 변경 시에만 로그 출력
          if (oldUrl !== newUrl) {
            window.__log('[Browser] SPA navigation: pushState', true);
          }
          
          setupMutationObserver();
          if (!window.__shouldSkipModalDetection() && window.__checkForModals) window.__checkForModals();
        };
  
        history.replaceState = function(...args) {
          window.__log('[Browser] SPA navigation: replaceState');
          originalReplaceState.apply(history, args);
          setupMutationObserver();
          if (!window.__shouldSkipModalDetection() && window.__checkForModals) window.__checkForModals();
        };
  
        window.addEventListener('popstate', () => {
          window.__log('[Browser] SPA navigation: popstate', true);
          setupMutationObserver();
          if (!window.__shouldSkipModalDetection() && window.__checkForModals) window.__checkForModals();
        });
  
        // 페이지 가시성 변경 감지 (탭 전환 등)
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden && !window.__shouldSkipModalDetection()) {
            window.__log('[Browser] Page visibility changed to visible, checking modals');
            setTimeout(() => {
              if (!window.__modalProcessing && !window.__shouldSkipModalDetection()) window.__checkForModals();
            }, 1000);
          }
        });

        // 모달 처리 완료 이벤트 리스너 추가
        document.addEventListener('modalProcessingComplete', function(e) {
          console.log('[Browser] 모달 처리 완료 이벤트 감지, 모달 ID:', e.detail.modalId);
          
          // 모달 감지 시스템 재초기화
          window.__modalObserverSetup = false; // 재설정 트리거
          
          // 조금 지연 후 모달 감지 스크립트 재초기화 및 체크 재시작
          setTimeout(() => {
            // MutationObserver 재설정
            if (typeof setupMutationObserver === 'function') {
              setupMutationObserver();
              console.log('[Browser] 모달 처리 완료 후 MutationObserver 재설정됨');
            }
            
            // 즉시 모달 체크 다시 실행
            if (typeof window.__checkForModals === 'function') {
              console.log('[Browser] 모달 처리 완료 후 모달 체크 강제 실행');
              window.__checkForModals();
            }
          }, 1000);
        });
  
        setupMutationObserver();
        window.__modalObserverSetup = true;
        window.__log('[Browser] Modal detection script injected', true);
  
        // 초기 체크
        if (!window.__shouldSkipModalDetection() && window.__checkForModals) window.__checkForModals();
      });
  
      await this._safeWait(500);
    } catch (error) {
      console.error(`[ERROR] Script injection failed: ${error.message}`);
    }
  }

  async _reinitializeModalDetection() {
    try {
      await this.currentPage.waitForFunction(() => document.readyState === 'complete', { timeout: 5000 }).catch(() => {});
      await this.currentPage.waitForSelector('body', { timeout: 5000 }).catch(() => {
        console.log('[WARN] Main content not found, proceeding');
      });
  
      await this.currentPage.evaluate(() => {
        // 모달 관련 상태 초기화 (예약 버튼 클릭 상태는 초기화하지 않음)
        console.log('[Browser] 페이지 전환 감지 - 모달 감지 상태 초기화 (예약 버튼 클릭 상태 유지)', true);
        
        // 로컬 스토리지에서 예약 버튼 클릭 상태 로드
        try {
          const savedValue = localStorage.getItem('kimcaddie_reservation_button_clicked');
          window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON = (savedValue === 'true');
          window.__hasClickedReservationButton = window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON; 
          console.log('[Browser] 로컬 스토리지에서 예약 버튼 클릭 상태 로드: ' + window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON, true);
        } catch (e) {
          // 로컬 스토리지 접근 실패 시 기존 값 유지
          console.log('[Browser] 로컬 스토리지 읽기 실패, 기존 클릭 상태 유지: ' + window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON, true);
        }
        
        // 전역 예약 버튼 클릭 상태는 유지하되 로그 출력
        console.log('[Browser] 전역 예약 버튼 클릭 상태 유지: ' + (window.__GLOBAL_HAS_CLICKED_RESERVATION_BUTTON ? 'true' : 'false'), true);
        
        // 모달 관련 상태 초기화
        window.__modalProcessing = false;
        window.__lastModalHTML = ''; 
        window.__lastModalTextFingerprint = null;
        window.__modalProcessingStartTime = null;
        window.__modalObserverSetup = false;
        
        // 타이머 클리어
        if (window.__modalProcessingTimer) {
          clearTimeout(window.__modalProcessingTimer);
          window.__modalProcessingTimer = null;
        }
      });
  
      // 모달 감지 스크립트 다시 주입 및 초기 검사
      await this._injectModalDetectionScript();
      await this.currentPage.evaluate((debugMode) => {
        window.__debugMode = debugMode;
        
        // 강제로 모달 검사 실행
        if (window.__checkForModals) {
          console.log('[Browser] 페이지 전환 후 모달 강제 검사 실행', true);
          window.__checkForModals();
        }
      }, this.debugMode);
  
      console.log('[INFO] Modal detection completely reinitialized');
    } catch (error) {
      console.error(`[ERROR] Reinitialization failed: ${error.message}`);
    }
  }

  /**
   * 취소 모달 처리
   * 수정: 기존 로직 유지
   */
  // modalDetectionService.js의 _handleCancelModal 메소드 수정

async _handleCancelModal() {
  if (this.autoCancelEnabled) {
    try {
      // 취소 모달 처리 컨텍스트 설정
      if (this.syncStateWithBrowser) {
        this.syncStateWithBrowser('cancel');
      }
      console.log('[INFO] 취소 모달 처리 시작, 컨텍스트 설정: cancel');
      
      console.log('[INFO] Cancel modal detected, clicking confirm');
      await this._clickCancelConfirmButton();
      
      // 취소 처리 후 잠시 지연
      await new Promise(resolve => setTimeout(resolve, 5000)); // 5초 대기
    } finally {
      // 취소 모달 처리 완료 후 컨텍스트 초기화
      if (this.syncStateWithBrowser) {
        this.syncStateWithBrowser(null);
      }
      console.log('[INFO] 취소 모달 처리 완료, 컨텍스트 초기화');
    }
  } else {
    console.log('[INFO] Cancel modal detected, auto-cancel disabled');
  }
}

  /**
   * 취소 확인 버튼 클릭
   * 수정: 기존 로직 유지
   */
  async _clickCancelConfirmButton() {
    if (this.isProcessing) {
      console.log('[INFO] Cancel click in progress, skipping');
      return;
    }

    this.isProcessing = true;
    try {
      console.log('[INFO] Attempting to click cancel confirm');
      const clicked = await this.currentPage.evaluate(() => {
        try {
          const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const label = btn.querySelector('.MuiButton-label');
            return label && label.textContent.includes('예약 취소 확인');
          });

          if (cancelButtons.length > 0) {
            window.__log('[Browser] Found cancel button:' + cancelButtons[0].outerHTML, true);
            cancelButtons[0].click();
            return true;
          }

          const cancelModals = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).filter(modal => {
            return modal.textContent.includes('김캐디 취소 접수');
          });

          if (cancelModals.length > 0) {
            const modal = cancelModals[0];
            const buttonArea = modal.querySelector('.sc-kNiUwJ');
            if (buttonArea) {
              const button = buttonArea.querySelector('button');
              if (button) {
                window.__log('[Browser] Found cancel button in footer:' + button.outerHTML, true);
                button.click();
                return true;
              }
            }
          }

          return false;
        } catch (e) {
          console.error('[Browser] Cancel button error:', e.message);
          return false;
        }
      });

      if (clicked) {
        console.log('[INFO] Clicked cancel confirm button');
        await this._safeWait(2000);
      } else {
        console.log('[WARN] Failed to find cancel button');
        // 캡처 함수 비활성화
        //await this.captureFullPageHTML('debug', 'cancel_button_not_found');
      }
    } catch (error) {
      console.error(`[ERROR] Cancel click error: ${error.message}`);
    } finally {
      this.isProcessing = false;
      await this.currentPage.evaluate(() => {
        window.__modalProcessing = false;
        window.__lastModalHTML = '';
        
        // 기존 타이머 클리어
        if (window.__modalProcessingTimer) {
          clearTimeout(window.__modalProcessingTimer);
          window.__modalProcessingTimer = null;
        }
      }).catch(() => {});
    }
  }

  /**
   * 모달 처리
   * 수정: 취소 모달 처리 호출, HTML 저장 비활성화
   */
  async _handleDetectedModal(modalInfo) {
    try {
      const { type, html, timestamp } = modalInfo;
      // 캡처 함수 비활성화
      //const modalDir = type === 'cancel' ? 'cancel' : 'booking';
      //await this._saveModalHTML(modalDir, html, timestamp);
      if (type === 'cancel') {
        await this._handleCancelModal();
      }
    } catch (error) {
      console.error(`[ERROR] Modal handling error: ${error.message}`);
    }
  }

  // 캡처 함수 비활성화 - 실행되지 않도록 수정
  async _saveModalHTML(modalType, html, timestamp) {
    console.log(`[INFO] HTML capture disabled for ${modalType} modal`);
  }

  /**
   * 전체 페이지 HTML 캡처 - 비활성화
   */
  async captureFullPageHTML(prefix, context) {
    console.log(`[INFO] Full page HTML capture disabled: ${prefix}, ${context}`);
    return null;
  }
}

module.exports = ModalDetectionService;
