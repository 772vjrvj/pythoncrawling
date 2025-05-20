/**
 * 자동 취소 서비스
 * 취소 팝업이 감지되면 자동으로 취소 확인 버튼을 클릭하는 기능 제공
 */

class AutoCancelService {
  constructor() {
    this.isObserverSetup = false;   // DOM 감시 설정 여부
    this.currentPage = null;       // 현재 Puppeteer 페이지 인스턴스
    this.autoCancelEnabled = true; // 자동 취소 기능 활성화 여부
    this.isProcessing = false;     // 클릭 처리 중 여부 (중복 방지용)
  }

  /**
   * 현재 활성화된 Puppeteer 페이지 설정
   * @param {Object} page - Puppeteer 페이지 인스턴스
   */
  setCurrentPage(page) {
    this.currentPage = page;
    console.log('[INFO] Puppeteer page set for auto-cancel service');
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
      await this.currentPage.evaluate(() => {
        if (window.__modalObserverSetup) return;

        window.__modalDetected = function(includesCancel, isKimCaddyCancelModal) {
          window.__modalInfo = {
            includesCancel,
            isKimCaddyCancelModal,
            timestamp: new Date().toISOString()
          };
        };

        const observer = new MutationObserver((mutations) => {
          for (const mutation of mutations) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
              for (const node of mutation.addedNodes) {
                if (node.nodeType === 1) {
                  // '김캐디 취소 접수' 모달만 감지
                  const isModal =
                    (node.classList && node.classList.contains('MuiPaper-root') && node.classList.contains('MuiCard-root') &&
                     node.querySelector('.sc-kHzJqM') && node.querySelector('.sc-kHzJqM').textContent.includes('김캐디 취소 접수'));

                  if (isModal) {
                    console.log('[Browser] KimCaddy cancel modal detected');
                    const modalText = node.textContent.toLowerCase();
                    const includesCancel = modalText.includes('취소') || modalText.includes('cancel');
                    window.__modalDetected(includesCancel, true);
                  }
                }
              }
            }
          }
        });

        observer.observe(document.documentElement, { childList: true, subtree: true });
        window.__modalObserverSetup = true;
        console.log('[Browser] Modal detection observer setup complete');
      });

      this.currentPage.on('console', async (msg) => {
        const text = msg.text();
        if (text.includes('[Browser] KimCaddy cancel modal detected')) {
          const modalInfo = await this.currentPage.evaluate(() => {
            const info = window.__modalInfo;
            window.__modalInfo = null;
            return info;
          });

          if (modalInfo && (modalInfo.includesCancel || modalInfo.isKimCaddyCancelModal) && this.autoCancelEnabled) {
            await this._handleCancelModalInPuppeteer();
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
   * 고객 정보 접근 감지 시 취소 버튼 확인
   * @param {string} customerId - 고객 ID
   * @param {string} name - 고객 이름 (로깅용)
   */
  async checkOnCustomerAccess(customerId, name) {
    console.log(`[INFO] Customer info access detected - customerId: ${customerId}, name: ${name}`);
    if (this.currentPage && this.autoCancelEnabled) {
      await this._checkForCancelButton();
    }
  }

  /**
   * 현재 페이지에서 취소 버튼 확인
   */
  async _checkForCancelButton() {
    if (!this.currentPage || !this.autoCancelEnabled || this.isProcessing) return;

    try {
      const foundCancelButton = await this.currentPage.evaluate(() => {
        const cancelModals = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).filter(modal => {
          const title = modal.querySelector('.sc-kHzJqM');
          return title && title.textContent.includes('김캐디 취소 접수');
        });

        if (cancelModals.length > 0) {
          console.log('[Browser] Found cancel modal during customer access check');
          return true;
        }

        const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
          const label = btn.querySelector('.MuiButton-label');
          return label && label.textContent.includes('예약 취소 확인');
        });

        if (cancelButtons.length > 0) {
          console.log('[Browser] Found cancel button during customer access check');
          return true;
        }

        return false;
      });

      if (foundCancelButton) {
        console.log('[INFO] Cancel button found in current page, attempting auto-click');
        await this._clickCancelConfirmButton();
      }
    } catch (error) {
      console.error(`[ERROR] Error checking for cancel button: ${error.message}`);
    }
  }

  /**
   * Puppeteer를 통한 취소 모달 처리
   */
  async _handleCancelModalInPuppeteer() {
    console.log('[INFO] Handling cancel modal with auto-click');
    if (!this.currentPage || !this.autoCancelEnabled || this.isProcessing) return;

    try {
      await this._clickCancelConfirmButton();
    } catch (error) {
      console.error(`[ERROR] Error handling cancel modal: ${error.message}`);
    }
  }

  /**
   * 취소 확인 버튼 클릭 수행
   */
  async _clickCancelConfirmButton() {
    if (this.isProcessing) {
      console.log('[INFO] Cancel click already in progress, skipping');
      return;
    }

    this.isProcessing = true;
    try {
      console.log('[INFO] Attempting to click cancel confirm button');
      const clicked = await this.currentPage.evaluate(() => {
        try {
          const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const label = btn.querySelector('.MuiButton-label');
            return label && label.textContent.includes('예약 취소 확인');
          });

          if (cancelButtons.length > 0) {
            console.log('[Browser] Found cancel confirm button:', cancelButtons[0].outerHTML);
            cancelButtons[0].click();
            return true;
          }

          const cancelModals = Array.from(document.querySelectorAll('.MuiPaper-root.MuiCard-root')).filter(modal => {
            const title = modal.querySelector('.sc-kHzJqM');
            return title && title.textContent.includes('김캐디 취소 접수');
          });

          if (cancelModals.length > 0) {
            const modal = cancelModals[0];
            const buttonArea = modal.querySelector('.sc-kNiUwJ');
            if (buttonArea) {
              const button = buttonArea.querySelector('button');
              if (button) {
                console.log('[Browser] Found cancel button in modal footer:', button.outerHTML);
                button.click();
                return true;
              }
            }
          }

          return false;
        } catch (e) {
          console.error('[Browser] Error clicking cancel button:', e.message);
          return false;
        }
      });

      if (clicked) {
        console.log('[INFO] Successfully clicked cancel confirm button');
        await this.currentPage.waitForTimeout(2000); // 모달 닫힘 대기
      } else {
        console.log('[WARN] Failed to find and click cancel confirm button');
      }
    } catch (error) {
      console.error(`[ERROR] Error clicking cancel confirm button: ${error.message}`);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * 특정 ID의 예약 취소 (customerId와 bookId로 직접 취소)
   * @param {string} customerId - 고객 ID
   * @param {string} bookId - 예약 ID
   */
  async cancelBookingById(customerId, bookId) {
    if (!this.currentPage || !this.autoCancelEnabled || this.isProcessing) {
      console.log('[WARN] Cannot cancel booking: Page not available, auto-cancel disabled, or processing');
      return false;
    }

    console.log(`[INFO] Attempting to cancel booking: customerId=${customerId}, bookId=${bookId}`);

    try {
      const found = await this.currentPage.evaluate((bookIdToFind) => {
        const elements = Array.from(document.querySelectorAll('*')).filter(el => {
          return el.textContent.includes(bookIdToFind);
        });

        if (elements.length > 0) {
          let cancelButton = null;
          for (const el of elements) {
            let current = el;
            for (let i = 0; i < 5; i++) {
              if (!current) break;
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
            console.log('[Browser] Found cancel button for booking:', cancelButton.outerHTML);
            cancelButton.click();
            return true;
          }
        }
        return false;
      }, bookId);

      if (found) {
        console.log(`[INFO] Found and clicked cancel button for booking ${bookId}`);
        await this.currentPage.waitForTimeout(1000);

        const confirmed = await this.currentPage.evaluate(() => {
          const textareas = document.querySelectorAll('textarea');
          let reasonTextarea = null;
          for (const textarea of textareas) {
            if (textarea.getAttribute('name') === 'comment' || textarea.className.includes('sc-jCDoxP')) {
              reasonTextarea = textarea;
              break;
            }
          }
          if (reasonTextarea) {
            reasonTextarea.value = '앱에서 자동 취소 처리됨';
            console.log('[Browser] Entered cancellation reason');
            const event = new Event('input', { bubbles: true });
            reasonTextarea.dispatchEvent(event);
          }

          const cancelButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
            const label = btn.querySelector('.MuiButton-label');
            return label && label.textContent.includes('예약 취소 확인');
          });

          if (cancelButtons.length > 0) {
            console.log('[Browser] Clicking cancel confirm button:', cancelButtons[0].outerHTML);
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
}

module.exports = AutoCancelService;