// src/services/htmlCaptureService.js
/**
 * HTML 캡처 서비스
 * 취소 팝업 등 특정 HTML 요소를 캡처하고 저장하는 기능 제공
 */

const fs = require('fs');
const path = require('path');

class HtmlCaptureService {
  constructor() {
    this.capturedHtmls = new Map(); // HTML 캡처 저장소
    this.isObserverSetup = false;   // DOM 감시 설정 여부
    this.currentPage = null;       // 현재 Puppeteer 페이지 인스턴스
    this.autoCancelEnabled = true; // 자동 취소 기능 활성화 여부
    
    // 캡처 파일 저장 디렉토리를 프로젝트 루트 폴더로 변경
    this.captureDir = path.join(process.cwd(), 'html_captures');
    this._createCaptureDirectories();
  }

  /**
   * 필요한 캡처 디렉토리 생성
   */
  _createCaptureDirectories() {
    try {
      if (!fs.existsSync(this.captureDir)) {
        fs.mkdirSync(this.captureDir, { recursive: true });
      }
      console.log(`[INFO] HTML captures will be saved to: ${this.captureDir}`);
      
      // 하위 디렉토리 생성
      const subDirs = ['modal', 'full_page', 'cancel', 'booking', 'call', 'notification', 'unknown'];
      for (const dir of subDirs) {
        const subDirPath = path.join(this.captureDir, dir);
        if (!fs.existsSync(subDirPath)) {
          fs.mkdirSync(subDirPath, { recursive: true });
          console.log(`[INFO] Created subdirectory: ${subDirPath}`);
        }
      }
    } catch (error) {
      console.error(`[ERROR] Failed to create capture directories: ${error.message}`);
    }
  }

  /**
   * 현재 활성화된 Puppeteer 페이지 설정
   * @param {Object} page - Puppeteer 페이지 인스턴스
   */
  setCurrentPage(page) {
    this.currentPage = page;
    console.log('[INFO] Puppeteer page set for HTML capture service');
    
    // 페이지가 설정되면 DOM 감시 설정
    this._setupPuppeteerPageMonitoring();
  }

  /**
   * 자동 취소 기능 켜기/끄기
   * @param {boolean} enabled - 활성화 여부
   */
  setAutoCancelEnabled(enabled) {
    this.autoCancelEnabled = enabled;
    console.log(`[INFO] Auto-cancel feature is now ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Puppeteer 페이지에 DOM 변화 감지 스크립트 추가
   */
  async _setupPuppeteerPageMonitoring() {
    if (!this.currentPage || this.isObserverSetup) return;
    
    try {
      // 페이지에 모달/팝업 감지 스크립트 추가
      await this.currentPage.evaluate(() => {
        // 이미 설정되어 있으면 건너뜀
        if (window.__modalObserverSetup) return;
        
        // 페이지에 모달 감지 로직 추가
        window.__modalDetected = function(modalHTML, type, includesCancel, info) {
          // 이 함수는 모달 감지 시 페이지에서 호출됨
          // 메시지로 정보를 전달함 (Puppeteer로 이 정보를 수신)
          window.__modalInfo = {
            html: modalHTML,
            type: type,
            includesCancel: includesCancel,
            timestamp: new Date().toISOString(),
            additionalInfo: info || {}
          };
        };
        
        // MutationObserver 설정
        const observer = new MutationObserver((mutations) => {
          for (const mutation of mutations) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
              for (const node of mutation.addedNodes) {
                if (node.nodeType === 1) { // ELEMENT_NODE
                  // 모달/팝업으로 보이는 요소 확인
                  const isModal = 
                    (node.classList && 
                     (node.classList.contains('modal') || 
                      node.classList.contains('popup') || 
                      node.classList.contains('dialog') ||
                      node.classList.contains('popup-wrapper') ||
                      node.classList.contains('overlay'))) ||
                    (node.getAttribute && node.getAttribute('role') === 'dialog') ||
                    (node.classList && node.classList.contains('MuiPaper-root') && 
                     node.classList.contains('MuiCard-root') && 
                     node.querySelector('.kwVFVz'));
                  
                  if (isModal) {
                    console.log('[Browser] Modal/popup detected');
                    const modalHTML = node.outerHTML;
                    const modalText = node.textContent.toLowerCase();
                    const includesCancel = modalText.includes('취소') || modalText.includes('cancel');
                    
                    // 김캐디 취소 접수 모달 확인
                    const isKimCaddyCancelModal = node.querySelector('.sc-kHzJqM') && 
                                                  node.querySelector('.sc-kHzJqM').textContent.includes('김캐디 취소 접수');
                    
                    // 취소 버튼 확인
                    let cancelButtonInfo = null;
                    if (includesCancel || isKimCaddyCancelModal) {
                      // 취소 확인 버튼 찾기
                      const cancelButton = node.querySelector('button span.MuiButton-label');
                      if (cancelButton && cancelButton.textContent.includes('예약 취소 확인')) {
                        cancelButtonInfo = {
                          exists: true,
                          text: cancelButton.textContent,
                          parentButtonClass: cancelButton.parentElement.className
                        };
                      }
                    }
                    
                    // 감지된 모달 정보 전달
                    window.__modalDetected(
                      modalHTML, 
                      'modal', 
                      includesCancel || isKimCaddyCancelModal,
                      {
                        isKimCaddyCancelModal,
                        cancelButtonInfo,
                        rawModalStructure: node.innerHTML.substring(0, 500) // 처음 500자만 전송
                      }
                    );
                  }
                  
                  // 내부에 모달/팝업이 있는지 확인
                  const innerModals = node.querySelectorAll && 
                                      node.querySelectorAll('.modal, .popup, .dialog, [role="dialog"], .popup-wrapper, .overlay');
                  if (innerModals && innerModals.length > 0) {
                    for (const modal of innerModals) {
                      console.log('[Browser] Inner modal/popup detected');
                      const modalHTML = modal.outerHTML;
                      const modalText = modal.textContent.toLowerCase();
                      const includesCancel = modalText.includes('취소') || modalText.includes('cancel');
                      
                      // 김캐디 취소 접수 모달 확인
                      const isKimCaddyCancelModal = modal.querySelector('.sc-kHzJqM') && 
                                                    modal.querySelector('.sc-kHzJqM').textContent.includes('김캐디 취소 접수');
                                                    
                      // 취소 버튼 확인
                      let cancelButtonInfo = null;
                      if (includesCancel || isKimCaddyCancelModal) {
                        // 취소 확인 버튼 찾기
                        const cancelButton = modal.querySelector('button span.MuiButton-label');
                        if (cancelButton && cancelButton.textContent.includes('예약 취소 확인')) {
                          cancelButtonInfo = {
                            exists: true,
                            text: cancelButton.textContent,
                            parentButtonClass: cancelButton.parentElement.className
                          };
                        }
                      }
                      
                      // 감지된 내부 모달 정보 전달
                      window.__modalDetected(
                        modalHTML, 
                        'inner_modal', 
                        includesCancel || isKimCaddyCancelModal,
                        {
                          isKimCaddyCancelModal,
                          cancelButtonInfo,
                          rawModalStructure: modal.innerHTML.substring(0, 500) // 처음 500자만 전송
                        }
                      );
                    }
                  }
                }
              }
            }
          }
        });
        
        // 문서 전체 변화 감지 시작
        observer.observe(document.documentElement, {
          childList: true,
          subtree: true
        });
        
        window.__modalObserverSetup = true;
        console.log('[Browser] Modal detection observer setup complete');
      });
      
      // 모달 감지 시 이벤트 리스너 설정
      this.currentPage.on('console', async (msg) => {
        const text = msg.text();
        if (text.includes('[Browser] Modal') || text.includes('[Browser] Inner modal')) {
          // 페이지에서 감지된 모달 정보 가져오기
          const modalInfo = await this.currentPage.evaluate(() => {
            const info = window.__modalInfo;
            // 정보를 가져온 후 초기화
            window.__modalInfo = null;
            return info;
          });
          
          if (modalInfo) {
            // 모달 정보 저장
            this._saveModalInfo(modalInfo);
            
            // 취소 모달인 경우 자동 클릭 수행
            if (modalInfo.includesCancel && modalInfo.additionalInfo && 
                modalInfo.additionalInfo.isKimCaddyCancelModal && 
                this.autoCancelEnabled) {
              await this._handleCancelModalInPuppeteer(modalInfo);
            }
          }
        }
      });
      
      this.isObserverSetup = true;
      console.log('[INFO] Puppeteer page modal monitoring setup complete');
    } catch (error) {
      console.error(`[ERROR] Failed to setup Puppeteer page monitoring: ${error.message}`);
    }
  }

  /**
   * 고객 정보 접근 감지 시 현재 페이지의 HTML을 캡처
   * @param {string} customerId - 고객 ID
   * @param {string} name - 고객 이름
   * @param {string|number} updateTime - 업데이트 시간
   */
  captureOnCustomerAccess(customerId, name, updateTime) {
    console.log(`[INFO] Capturing HTML for customer access - customerId: ${customerId}, name: ${name}, updateTime: ${updateTime}`);
    this.saveCurrentPageHTML(customerId, updateTime);
  }

  /**
   * 현재 페이지의 HTML을 저장
   * @param {string} customerId - 고객 ID
   * @param {string|number} updateTime - 업데이트 시간
   */
  async saveCurrentPageHTML(customerId, updateTime) {
    try {
      if (!this.currentPage) {
        console.log('[WARN] No Puppeteer page available for HTML capture');
        return;
      }

      // Puppeteer를 통해 현재 페이지 HTML 캡처
      const htmlData = await this.currentPage.evaluate(() => {
        // 전체 페이지 HTML
        const fullHTML = document.documentElement.outerHTML;
        
        // 모달 또는 팝업 요소 찾기
        const modalElements = Array.from(
          document.querySelectorAll('.modal, .popup, .dialog, [role="dialog"], .popup-wrapper, .overlay, .MuiPaper-root.MuiCard-root')
        ).map(el => el.outerHTML);
        
        // 취소 관련 텍스트가 포함된 모달 찾기
        const cancelModals = Array.from(
          document.querySelectorAll('.modal, .popup, .dialog, [role="dialog"], .popup-wrapper, .overlay, .MuiPaper-root.MuiCard-root')
        ).filter(el => {
          const text = el.textContent.toLowerCase();
          return text.includes('취소') || text.includes('cancel') || 
                 (el.querySelector('.sc-kHzJqM') && el.querySelector('.sc-kHzJqM').textContent.includes('김캐디 취소 접수'));
        }).map(el => el.outerHTML);
        
        // 취소 확인 버튼 찾기
        const cancelButtons = Array.from(
          document.querySelectorAll('button')
        ).filter(el => {
          const buttonLabel = el.querySelector('.MuiButton-label');
          return buttonLabel && buttonLabel.textContent.includes('예약 취소 확인');
        }).map(el => ({
          html: el.outerHTML,
          text: el.textContent,
          class: el.className
        }));
        
        return {
          fullHTML,
          modalElements,
          cancelModals,
          cancelButtons
        };
      });
      
      // 파일명 생성 및 저장
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `capture_${customerId}_${updateTime}_${timestamp}.json`;
      const filePath = path.join(this.captureDir, fileName);
      
      // 캡처 데이터 구성
      const captureData = {
        timestamp,
        customerId,
        updateTime,
        modalCount: htmlData.modalElements.length,
        cancelModalCount: htmlData.cancelModals.length,
        cancelButtonCount: htmlData.cancelButtons.length,
        modals: htmlData.modalElements,
        cancelModals: htmlData.cancelModals,
        cancelButtons: htmlData.cancelButtons,
        // 전체 HTML은 크기가 큰 경우가 많으므로 모달이 발견된 경우에는 저장하지 않음
        fullHTML: htmlData.modalElements.length > 0 ? null : htmlData.fullHTML
      };
      
      // 파일에 저장
      fs.writeFileSync(filePath, JSON.stringify(captureData, null, 2));
      console.log(`[INFO] HTML captured and saved to file: ${filePath}`);
      
      // 메모리에도 저장 (참조용)
      this.capturedHtmls.set(`${customerId}_${updateTime}`, {
        filePath,
        timestamp,
        hasModals: htmlData.modalElements.length > 0,
        hasCancelModals: htmlData.cancelModals.length > 0,
        hasCancelButtons: htmlData.cancelButtons.length > 0
      });
      
      // 취소 확인 버튼이 있으면 자동 클릭 수행
      if (htmlData.cancelButtons.length > 0 && this.autoCancelEnabled) {
        console.log('[INFO] Cancel button found in current page, attempting auto-click');
        await this._clickCancelConfirmButton();
      }
      
    } catch (error) {
      console.error(`[ERROR] Failed to save HTML: ${error.message}`);
    }
  }

  /**
   * 감지된 모달 정보 저장
   * @param {Object} modalInfo - 모달 정보 객체
   */
  _saveModalInfo(modalInfo) {
    try {
      const timestamp = modalInfo.timestamp || new Date().toISOString();
      const cleanTimestamp = timestamp.replace(/[:.]/g, '-');
      const modalType = modalInfo.type || 'unknown';
      const isCancelModal = modalInfo.includesCancel;
      
      const fileName = `modal_${modalType}_${isCancelModal ? 'cancel_' : ''}${cleanTimestamp}.json`;
      const filePath = path.join(this.captureDir, 'modal', fileName);
      
      // JSON 형식으로 저장
      fs.writeFileSync(filePath, JSON.stringify(modalInfo, null, 2));
      
      if (isCancelModal) {
        console.log(`[INFO] Cancel modal detected and saved to: ${filePath}`);
      } else {
        console.log(`[INFO] Modal detected and saved to: ${filePath}`);
      }
      
      return filePath;
    } catch (error) {
      console.error(`[ERROR] Failed to save modal info: ${error.message}`);
      return null;
    }
  }

  /**
   * Puppeteer를 통한 취소 모달 처리
   * @param {Object} modalInfo - 감지된 모달 정보
   */
  async _handleCancelModalInPuppeteer(modalInfo) {
    console.log('[INFO] Handling cancel modal with auto-click');
    
    if (!this.currentPage || !this.autoCancelEnabled) return;
    
    try {
      // 취소 확인 버튼 클릭
      await this._clickCancelConfirmButton();
    } catch (error) {
      console.error(`[ERROR] Error handling cancel modal: ${error.message}`);
    }
  }

  /**
   * 취소 확인 버튼 클릭 수행
   */
  async _clickCancelConfirmButton() {
    try {
      console.log('[INFO] Attempting to click cancel confirm button');
      
      // 방법 1: 특정 텍스트 포함 버튼 클릭
      const clicked = await this.currentPage.evaluate(() => {
        try {
          // 방법 1: 특정 클래스와 텍스트 포함 버튼 찾기 (제공된 HTML에서 확인한 구조 기반)
          const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const label = btn.querySelector('.MuiButton-label');
            return label && label.textContent.includes('예약 취소 확인');
          });
          
          if (cancelButtons.length > 0) {
            console.log('[Browser] Found cancel confirm button by text content');
            cancelButtons[0].click();
            return true;
          }
          
          // 방법 2: 김캐디 취소 접수 모달 내의 버튼 찾기
          const cancelModals = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).filter(modal => {
            const title = modal.querySelector('.sc-kHzJqM');
            return title && title.textContent.includes('김캐디 취소 접수');
          });
          
          if (cancelModals.length > 0) {
            console.log('[Browser] Found kim caddie cancel modal');
            const modal = cancelModals[0];
            const buttonArea = modal.querySelector('.sc-kNiUwJ');
            
            if (buttonArea) {
              const button = buttonArea.querySelector('button');
              if (button) {
                console.log('[Browser] Found cancel button in modal footer');
                button.click();
                return true;
              }
            }
          }
          
          // 방법 3: 특정 클래스 버튼 찾기
          const bCootWButtons = document.querySelectorAll('.sc-kOFNMu.bCootW');
          if (bCootWButtons.length > 0) {
            console.log('[Browser] Found cancel button by specific class');
            bCootWButtons[0].click();
            return true;
          }
          
          // 방법 4: 특정 구조를 가진 모달 내의 버튼 찾기
          const lastButton = document.querySelector('.sc-kNiUwJ button');
          if (lastButton) {
            console.log('[Browser] Found button in footer area');
            lastButton.click();
            return true;
          }
          
          return false;
        } catch (e) {
          console.error('[Browser] Error clicking cancel button:', e.message);
          return false;
        }
      });
      
      if (clicked) {
        console.log('[INFO] Successfully clicked cancel confirm button');
        
        // 확인 클릭 후 추가 확인 다이얼로그가 있을 수 있으므로 대기
        await this.currentPage.waitForTimeout(1000);
        
        // 추가 확인 다이얼로그 체크
        const additionalConfirmClicked = await this.currentPage.evaluate(() => {
          // 확인/예 버튼 찾기
          const confirmButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const text = btn.textContent.toLowerCase();
            return text.includes('확인') || text.includes('예') || 
                   text.includes('ok') || text.includes('yes');
          });
          
          if (confirmButtons.length > 0) {
            console.log('[Browser] Found additional confirm button');
            confirmButtons[0].click();
            return true;
          }
          
          return false;
        });
        
        if (additionalConfirmClicked) {
          console.log('[INFO] Clicked additional confirmation dialog button');
        }
        
      } else {
        console.log('[WARN] Failed to find and click cancel confirm button');
      }
      
    } catch (error) {
      console.error(`[ERROR] Error clicking cancel confirm button: ${error.message}`);
    }
  }

  /**
   * 특정 ID의 예약 취소 (customerId와 bookId로 직접 취소)
   * @param {string} customerId - 고객 ID
   * @param {string} bookId - 예약 ID
   */
  async cancelBookingById(customerId, bookId) {
    if (!this.currentPage || !this.autoCancelEnabled) {
      console.log('[WARN] Cannot cancel booking: Page not available or auto-cancel disabled');
      return false;
    }
    
    console.log(`[INFO] Attempting to cancel booking: customerId=${customerId}, bookId=${bookId}`);
    
    try {
      // 현재 페이지 내에서 해당 예약 버튼 찾기
      const found = await this.currentPage.evaluate((bookIdToFind) => {
        // 예약 ID가 포함된 요소 찾기
        const elements = Array.from(document.querySelectorAll('*')).filter(el => {
          return el.textContent.includes(bookIdToFind);
        });
        
        if (elements.length > 0) {
          // 가장 가까운 취소 버튼 찾기
          let cancelButton = null;
          
          for (const el of elements) {
            // 현재 요소 주변에서 취소 버튼 찾기
            let current = el;
            for (let i = 0; i < 5; i++) { // 부모 계층 5단계까지 확인
              if (!current) break;
              
              // 현재 요소 내에서 취소 버튼 찾기
              const buttons = current.querySelectorAll('button');
              for (const btn of buttons) {
                if (btn.textContent.toLowerCase().includes('취소')) {
                  cancelButton = btn;
                  break;
                }
              }
              
              if (cancelButton) break;
              current = current.parentElement;
            }
            
            if (cancelButton) break;
          }
          
          if (cancelButton) {
            console.log('[Browser] Found cancel button for booking:', bookIdToFind);
            cancelButton.click();
            return true;
          }
        }
        
        return false;
      }, bookId);
      
      if (found) {
        console.log(`[INFO] Found and clicked cancel button for booking ${bookId}`);
        
        // 취소 팝업이 나타날 때까지 대기
        await this.currentPage.waitForTimeout(1000);
        
        // 취소 사유 입력 및 확인 버튼 클릭
        const confirmed = await this.currentPage.evaluate(() => {
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
          
          // 취소 확인 버튼 찾기 및 클릭
          const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const label = btn.querySelector('.MuiButton-label');
            return label && label.textContent.includes('예약 취소 확인');
          });
          
          if (cancelButtons.length > 0) {
            console.log('[Browser] Clicking cancel confirm button');
            cancelButtons[0].click();
            return true;
          }
          
          return false;
        });
        
        if (confirmed) {
          console.log(`[INFO] Successfully submitted cancellation for booking ${bookId}`);
          return true;
        } else {
          console.log(`[WARN] Could not find cancel confirm button for booking ${bookId}`);
        }
      } else {
        console.log(`[WARN] Could not find booking ${bookId} in current page`);
      }
      
      return false;
    } catch (error) {
      console.error(`[ERROR] Error cancelling booking ${bookId}: ${error.message}`);
      return false;
    }
  }

  /**
   * 캡처된 HTML 데이터 내보내기 (디버깅용)
   * @returns {Object} 캡처된 HTML 데이터
   */
  exportCapturedData() {
    // 캡처된 파일 목록
    let capturedFiles = [];
    try {
      capturedFiles = fs.readdirSync(this.captureDir)
        .filter(file => file.endsWith('.json') || file.endsWith('.html'))
        .map(file => path.join(this.captureDir, file));
    } catch (e) {
      console.error(`[ERROR] Failed to read capture directory: ${e.message}`);
    }
    
    return {
      memoryReferences: Object.fromEntries(this.capturedHtmls),
      captureDirectory: this.captureDir,
      capturedFileCount: capturedFiles.length,
      capturedFiles: capturedFiles.slice(0, 10), // 처음 10개만 반환 (너무 많을 수 있음)
      autoCancelEnabled: this.autoCancelEnabled
    };
  }
}

module.exports = HtmlCaptureService;