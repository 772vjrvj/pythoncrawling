const puppeteer = require('puppeteer-core');
const { CHROME_PATH, getUserCredentials } = require('../config/env');
const AutoCancelService = require('./autoCancelService');
const path = require('path');
const fs = require('fs');

// 자동 취소 서비스 인스턴스 생성 (싱글톤)
const autoCancelService = new AutoCancelService();

/**
 * 강제 스크롤 기능 적용 (특히 예약 페이지용)
 * @param {Object} page - Puppeteer 페이지 인스턴스
 */
const forcePageScrollable = async (page) => {
  try {
    console.log('[INFO] 강제 스크롤 기능을 적용합니다...');

    // 현재 URL 확인
    const url = await page.url();
    const isBookingPage = url.includes('/booking');
    console.log(`[INFO] 현재 페이지: ${url}, 예약 페이지: ${isBookingPage ? '예' : '아니오'}`);

    // 최소한의 스크롤 활성화만 적용 (다른 스타일에 영향 안 주도록)
    await page.evaluate(() => {
      console.log('[Browser] 스크롤 기능을 활성화합니다.');
      
      // 기존 스크롤 요소 제거
      const existingElement = document.getElementById('scroll-force');
      if (existingElement) {
        existingElement.remove();
      }
      
      // body/html 스크롤 허용 (최소한의 변경만)
      if (document.body.style.overflow === 'hidden') {
        document.body.style.overflow = 'auto';
      }
      if (document.documentElement.style.overflow === 'hidden') {
        document.documentElement.style.overflow = 'auto';
      }
      
      // 페이지 컨텐츠 높이에 따라 적절한 스크롤 영역 계산
      const bodyHeight = document.body.scrollHeight || 0;
      const htmlHeight = document.documentElement.scrollHeight || 0;
      const pageHeight = Math.max(bodyHeight, htmlHeight);
      
      // 현재 화면 높이 (뷰포트)
      const viewportHeight = window.innerHeight;
      
      // 페이지 높이의 10%만큼 추가 스크롤 영역 제공 (최소 50px, 최대 300px)
      const extraScrollHeight = Math.min(Math.max(Math.round(pageHeight * 0.1), 50), 300);
      
      console.log(`[Browser] 페이지 높이: ${pageHeight}px, 뷰포트 높이: ${viewportHeight}px, 추가 스크롤 영역: ${extraScrollHeight}px`);
      
      // 최소한의 스크롤 요소 추가 (클릭 방해 최소화)
      const scrollForce = document.createElement('div');
      scrollForce.id = 'scroll-force';
      scrollForce.style.cssText = `height: ${extraScrollHeight}px; width: 100%; position: relative; z-index: -1; pointer-events: none;`;
      document.body.appendChild(scrollForce);
      
      // 추가 디버깅 정보
      setTimeout(() => {
        const finalBodyHeight = document.body.scrollHeight || 0;
        console.log(`[Browser] 스크롤 요소 추가 후 최종 높이: ${finalBodyHeight}px (증가: ${finalBodyHeight - pageHeight}px)`);
      }, 100);
      
      console.log('[Browser] 스크롤 기능 활성화 완료');
    });

    console.log('[INFO] 강제 스크롤 기능 적용 완료');
  } catch (error) {
    console.error(`[ERROR] 강제 스크롤 적용 실패: ${error.message}`);
  }
};

/**
 * 모달 관련 설정을 조정하지 않는 함수 (기본 웹사이트 동작 유지)
 * @param {Object} page - Puppeteer 페이지 인스턴스
 */
const fixModalPositions = async (page) => {
  // 이 함수는 의도적으로 아무것도 하지 않습니다.
  // 기본 웹사이트 동작을 그대로 유지하기 위함입니다.
  console.log('[INFO] 모달 위치 조정이 비활성화되었습니다. 웹사이트 기본 동작을 유지합니다.');
};

/**
 * 로그인 후 예약 페이지로 자동 이동
 * @param {Object} page - Puppeteer 페이지 인스턴스
 */
const navigateToBookingPage = async (page) => {
  try {
    console.log('[INFO] Navigating to booking page...');
    await page.goto('https://owner.kimcaddie.com/booking', { waitUntil: 'networkidle2', timeout: 30000 });
    console.log('[INFO] Successfully navigated to booking page');
    
    // 최소한의 스크롤 기능만 적용
    await forcePageScrollable(page);
  } catch (error) {
    console.error(`[ERROR] Failed to navigate to booking page: ${error.message}`);
    
    // 다른 방식으로 예약 페이지로 이동 시도
    try {
      console.log('[INFO] Trying alternative navigation method...');
      await page.evaluate(() => {
        // 브라우저 콘솔에서 직접 이동
        window.location.href = 'https://owner.kimcaddie.com/booking';
      });
      
      // 페이지 로드 대기
      await page.waitForNavigation({ timeout: 10000 });
      console.log('[INFO] Alternative navigation successful');
      
      // 최소한의 스크롤 기능만 적용
      await forcePageScrollable(page);
    } catch (e) {
      console.error(`[ERROR] Alternative navigation also failed: ${e.message}`);
    }
  }
};

// 대시보드(메인 페이지)인지 확인하는 함수 (로그인 페이지와 URL은 같지만 내용은 다름)
const isOnDashboard = async (page) => {
  try {
    // 로그인 페이지 또는 대시보드 여부를 DOM 내용으로 확인
    const result = await page.evaluate(() => {
      // 대시보드에 있는 특징적인 요소들 확인
      const hasSidebar = document.querySelector('.MuiDrawer-root') !== null;
      const hasAppBar = document.querySelector('.MuiAppBar-root') !== null;
      const hasLoginForm = document.querySelector('form input[type="password"]') !== null;
      
      // 로그인 폼이 없고, 사이드바나 앱바가 있으면 대시보드로 판단
      const isDashboard = !hasLoginForm && (hasSidebar || hasAppBar);
      
      return {
        isDashboard,
        hasSidebar,
        hasAppBar,
        hasLoginForm
      };
    });
    
    console.log(`[INFO] Page detection: isDashboard=${result.isDashboard}, hasSidebar=${result.hasSidebar}, hasAppBar=${result.hasAppBar}, hasLoginForm=${result.hasLoginForm}`);
    
    return result.isDashboard;
  } catch (error) {
    console.error(`[ERROR] Failed to detect dashboard: ${error.message}`);
    return false;
  }
};

const launchBrowser = async () => {
  // 화면 크기 가져오기
  const { width, height } = require('ko/kimcady-main/src/services/electron').screen.getPrimaryDisplay().workAreaSize;
  console.log(`[INFO] Detected screen size: ${width}x${height}`);
  
  // 실제 사용할 브라우저 창 크기 계산 (작업 표시줄 등을 고려하여 약간 줄임)
  const browserWidth = Math.floor(width * 1.00);
  const browserHeight = Math.floor(height * 1.00);
  console.log(`[INFO] Setting browser size to: ${browserWidth}x${browserHeight}`);

  // 일반 브라우저와 유사한 설정으로 Puppeteer 실행
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: false,
    defaultViewport: null,  // 중요: 뷰포트를 null로 설정하여 창 크기에 맞게 자동 조정
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      `--window-size=${browserWidth},${browserHeight}`,
      '--window-position=0,0',
      '--disable-notifications',
      '--disable-infobars',
      '--disable-features=site-per-process',
      '--enable-features=NetworkServiceInProcess',
    ],
  });

  const page = (await browser.pages())[0] || await browser.newPage();
  
  // 일반 브라우저처럼 동작하도록 설정
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
  
  // 브라우저 창 최대화
  try {
    console.log('[INFO] Attempting to maximize browser window...');
    
    try {
      await page._client.send('Browser.setWindowBounds', { 
        windowId: 1, 
        bounds: { windowState: 'maximized' } 
      });
      console.log('[INFO] Browser window maximized using client API');
    } catch (e) {
      console.log('[DEBUG] First maximize failed, using fallback');
      
      // 대체 방법: window.resizeTo 사용
      await page.evaluate((w, h) => {
        window.resizeTo(w, h);
        return { 
          width: window.outerWidth, 
          height: window.outerHeight 
        };
      }, browserWidth, browserHeight).then(size => {
        console.log(`[INFO] Browser resized to: ${size.width}x${size.height}`);
      }).catch(err => {
        console.log(`[WARN] Resize method failed: ${err.message}`);
      });
    }
  } catch (e) {
    console.error(`[ERROR] Failed to set up responsive browser: ${e.message}`);
  }

  // 페이지 내비게이션 로깅 및 최소한의 스크롤 적용
  page.on('framenavigated', async frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      console.log(`[INFO] Page navigated to: ${url}`);
      
      // 페이지 로드 후 강제 스크롤만 적용
      setTimeout(async () => {
        await forcePageScrollable(page).catch(err => {
          console.error(`[ERROR] Failed to force scroll after navigation: ${err.message}`);
        });
        
        /* 주석 처리: 대시보드에서 예약 페이지로 자동 이동 기능 비활성화
        // URL만으로는 구분이 어려우므로 페이지 내용으로 대시보드 여부 판단
        const onDashboard = await isOnDashboard(page);
        
        // 대시보드(메인 페이지)에 있고 booking 페이지가 아니면 예약 페이지로 이동
        if (onDashboard && !url.includes('/booking')) {
          console.log('[INFO] Detected dashboard page, redirecting to booking page...');
          await navigateToBookingPage(page).catch(err => {
            console.error(`[ERROR] Failed to redirect to booking page: ${err.message}`);
          });
        }
        */
      }, 1500);
    }
  });

  // 페이지 오류 로깅
  page.on('error', err => {
    console.error(`[ERROR] Page error: ${err.message}`);
  });

  // 콘솔 메시지 로깅
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error(`[Browser Error] ${msg.text()}`);
    } else if (msg.text().includes('[Browser]')) {
      console.log(msg.text());
    }
  });

  // 로그인 페이지로 직접 이동
  console.log('[INFO] Navigating to KimCaddie login page...');
  await page.goto('https://owner.kimcaddie.com/login', { 
    waitUntil: 'networkidle2', 
    timeout: 60000 
  });
  console.log('[INFO] Browser launched and navigated to KimCaddie login page');
  
  // 최소한의 스크롤만 활성화
  await forcePageScrollable(page);
  
  // 자동 취소 서비스에 페이지 인스턴스 설정
  autoCancelService.setCurrentPage(page);
  console.log('[INFO] Puppeteer page registered with auto-cancel service');
  
  // 자동 로그인 시도
  const loginSuccess = await tryAutoLogin(page);

  console.log('[INFO] loginSuccess is : ' + loginSuccess);
  
  // 로그인 성공 시 예약 페이지로 이동
  if (loginSuccess) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('[INFO] call navigateToBookingPage');
    await navigateToBookingPage(page);
  } else {
    // 수동 로그인 감지 및 페이지 이동 기능 추가
    // 주석 처리: 수동 로그인 후 자동 리다이렉트 비활성화
    // await setupLoginDetection(page);
    console.log('[INFO] Manual login redirect disabled - user will remain on the main dashboard after login');
  }
  
  return { browser, page, autoCancelService };
};

// 수동 로그인 감지 및 페이지 이동 기능
const setupLoginDetection = async (page) => {
  try {
    console.log('[INFO] Setting up login detection...');
    
    // 페이지에 이벤트 리스너 추가 - fetch API 감시
    await page.evaluate(() => {
      // 네트워크 요청 감시
      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const result = await originalFetch.apply(this, args);
        
        /* 주석 처리: 로그인 API 감지 및 자동 이동 비활성화
        // 로그인 API 요청 감지
        if (args[0] && (args[0].includes('/api/login') || args[0].includes('/api/auth/token'))) {
          // 로그인 응답 확인
          result.clone().json().then(data => {
            if (data && (data.token || data.access_token)) {
              console.log('[Browser] Login detected from API, will navigate to booking page');
              
              // 잠시 대기 후 예약 페이지로 이동 (로그인 처리 완료 대기)
              setTimeout(() => {
                console.log('[Browser] Navigating to booking page after login');
                window.location.href = 'https://owner.kimcaddie.com/booking';
              }, 2000);
            }
          }).catch(e => {
            console.error('[Browser] Error checking login response:', e);
          });
        }
        */
        
        return result;
      };
      
      console.log('[Browser] Fetch API monitoring setup complete');
    });
    
    // 로그인 버튼 클릭 이벤트 감지
    await page.evaluate(() => {
      console.log('[Browser] Setting up login button click detection');
      
      /* 주석 처리: 로그인 버튼 클릭 감지 및 자동 이동 비활성화
      // 로그인 버튼 이벤트 리스너 추가
      document.addEventListener('click', function loginButtonClickHandler(event) {
        // 클릭된 요소 또는 부모 요소 중 로그인 버튼 찾기
        const button = event.target.closest('button[type="submit"]');
        if (button) {
          const buttonText = button.textContent.toLowerCase();
          if (buttonText.includes('로그인') || buttonText.includes('login') || buttonText.includes('sign in')) {
            console.log('[Browser] Login button clicked, setting up redirect detection');
            
            // 로그인 버튼 클릭 후 DOM 변화를 감지하는 MutationObserver 설정
            let dashboardCheckTimer = setInterval(() => {
              // 로그인 폼이 사라졌는지 확인
              const loginForm = document.querySelector('form input[type="password"]');
              // 대시보드 요소가 나타났는지 확인
              const dashboardElements = document.querySelector('.MuiDrawer-root, .MuiAppBar-root');
              
              if (!loginForm && dashboardElements) {
                console.log('[Browser] Dashboard detected after login, redirecting to booking');
                clearInterval(dashboardCheckTimer);
                
                // 예약 페이지로 리다이렉트
                setTimeout(() => {
                  window.location.href = 'https://owner.kimcaddie.com/booking';
                }, 1000);
              }
            }, 500);
            
            // 10초 후에는 타이머 종료 (안전장치)
            setTimeout(() => {
              clearInterval(dashboardCheckTimer);
            }, 10000);
          }
        }
      });
      */
    });
    
    // DOM 변화 감지하여 로그인 상태 변화 확인
    await page.evaluate(() => {
      /* 주석 처리: DOM 변화 감지 및 자동 이동 비활성화
      // MutationObserver 설정으로 DOM 변화 감지
      if (!window.__loginObserver) {
        const observer = new MutationObserver(function(mutations) {
          // 사이드바나 앱바가 나타났는지 확인 (로그인 성공 징후)
          const dashboardElements = document.querySelector('.MuiDrawer-root, .MuiAppBar-root');
          const loginForm = document.querySelector('form input[type="password"]');
          
          if (dashboardElements && !loginForm && !window.location.pathname.includes('/booking')) {
            console.log('[Browser] DOM changes detected, dashboard elements found, redirecting to booking');
            // 예약 페이지로 이동
            setTimeout(() => {
              window.location.href = 'https://owner.kimcaddie.com/booking';
            }, 1000);
          }
        });
        
        // 문서 전체 변화 감시
        observer.observe(document.documentElement, { childList: true, subtree: true });
        window.__loginObserver = observer;
        console.log('[Browser] DOM change observer setup complete');
      }
      */
    });
    
    console.log('[INFO] Login detection setup complete');
  } catch (error) {
    console.error(`[ERROR] Failed to set up login detection: ${error.message}`);
  }
};

// 자동 로그인 시도
const tryAutoLogin = async (page) => {
  const { phone, password, hasCredentials } = getUserCredentials();
  
  if (!hasCredentials) {
    console.log('[INFO] No saved credentials found. Waiting for manual login.');
    return false;
  }
  
  try {
    console.log('[INFO] Attempting auto-login...');
    
    // 페이지가 완전히 로드될 때까지 대기
    await page.waitForSelector('#phoneNumber', { timeout: 10000 });
    
    // 핸드폰 번호 입력
    await page.type('#phoneNumber', phone);
    console.log('[INFO] Entered phone number');
    
    // 비밀번호 입력
    await page.type('#password', password);
    console.log('[INFO] Entered password');
    
    // 로그인 버튼 클릭
    const loginButton = await page.$('button[type="submit"]');
    await loginButton.click();
    console.log('[INFO] Clicked login button');

    // 로그인 성공/실패 확인 - SPA에 최적화된 방식
    try {
    // 로그인 성공 시 나타나는 대시보드 요소를 기다림
    console.log('[INFO] Waiting for dashboard elements after login...');
    await page.waitForSelector('.MuiDrawer-root, .MuiAppBar-root', { timeout: 15000 });
    
    // 로그인 상태 확인
    console.log('[INFO] Dashboard elements appeared, confirming login...');
    // checkLoginState 함수 대신 직접 평가
    const isLoggedIn = await page.evaluate(() => {
        return document.querySelector('.MuiDrawer-root') != null || 
               document.querySelector('.MuiAppBar-root') != null;
      });
    
    if (isLoggedIn) {
      console.log('[INFO] Auto-login successful!');
      return true;
    } else {
      console.log('[WARN] Dashboard elements found but login verification failed');
      // URL로 추가 확인
      const currentUrl = await page.url();
      const loginSuccess = !currentUrl.includes('/login');
      console.log(`[INFO] Current URL: ${currentUrl}, Login successful based on URL: ${loginSuccess}`);
      return loginSuccess;
    }
    }catch (e) {
      console.log('[WARN] Auto-login may have failed: ' + e.message);
      
      // 로그인 오류 메시지가 있는지 확인
      const errorMessage = await page.evaluate(() => {
        const errorEl = document.querySelector('.error-message') || document.querySelector('.MuiAlert-message');
        return errorEl ? errorEl.textContent : '';
      });
      
      if (errorMessage) {
        console.log(`[ERROR] Login failed: ${errorMessage}`);
      }
      
      return false;
    }
  } catch (error) {
    console.error(`[ERROR] Auto-login error: ${error.message}`);
    return false;
  }
};

// 자동 취소 서비스 인스턴스 가져오기
const getAutoCancelService = () => {
  return autoCancelService;
};

module.exports = { launchBrowser, getAutoCancelService, navigateToBookingPage, fixModalPositions };