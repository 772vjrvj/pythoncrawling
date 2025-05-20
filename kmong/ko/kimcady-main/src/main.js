const {app, ipcMain} = require('electron');
// Electron의 핵심 객체 불러오기
// app: Electron 애플리케이션의 생명주기 관리
// ipcMain: 렌더러 ↔ 메인 프로세스 간 통신 처리

const {setupElectron} = require('./services/electron');
//브라우저 윈도우 생성 등 Electron 관련 설정 함수

const {launchBrowser} = require('./services/puppeteer');
//Puppeteer 브라우저 실행 함수 (Headless 아님)

const {getAccessToken, getStoreInfo} = require('./utils/api');
//API 통신용 함수: 인증 토큰, 매장 정보 요청

const {setupRequestHandler} = require('./handlers/request');
const {setupResponseHandler} = require('./handlers/response');
//Puppeteer 네트워크 요청/응답을 감지하고 가공 처리하는 핸들러들

const {
    getStoreId,
    saveStoreId,
    getUserCredentials,
    saveUserCredentials,
    clearUserCredentials,
    TIMEOUT_MS
} = require('./config/env');
//설정 파일에서 계정, 매장 ID, 기본값 등 불러오기


const path = require('path');
const ModalDetectionService = require('./services/modalDetectionService');
//모달 감지 서비스 클래스 로딩


// 글로벌 변수
let accessToken = null;
let mainWindow = null;
let appStatus = 'initializing';
let modalDetectionService = null;

// 모달 처리 상태를 위한 전역 변수 초기화 
global.currentProcessingModalType = null;

// Puppeteer의 page 객체를 통해 브라우저 컨텍스트에 전달하는 함수
//Puppeteer의 page.evaluate를 통해 브라우저
// 내 window.currentProcessingModalType에 값을 전달
async function syncModalStateWithBrowser(page) {
    if (!page) return;

    try {
        // Node.js의 global에서 브라우저의 window로 상태 전달
        await page.evaluate((modalType) => {
            window.currentProcessingModalType = modalType;
            console.log(`[Browser] 모달 처리 상태 동기화됨: ${modalType || 'null'}`);
        }, global.currentProcessingModalType);
    } catch (error) {
        console.error(`[ERROR] 모달 상태 동기화 실패: ${error.message}`);
    }
}

const main = async () => {
    try {
        console.log('[INFO] Starting PandoK application...');
        mainWindow = setupElectron();
        updateAppStatus('초기화 중...');

        // src/main.js - main 함수 내부 모달 감지 서비스 관련 부분 수정

// 모달 감지 서비스 초기화 및 관리 강화
        try {
            modalDetectionService = new ModalDetectionService();
            console.log('[INFO] Modal detection service initialized');

            // 서비스 인스턴스에 상태 동기화 함수 연결
            if (modalDetectionService) {
                modalDetectionService.syncStateWithBrowser = value => {
                    global.currentProcessingModalType = value;
                    syncModalStateWithBrowser(page).catch(err => {
                        console.error(`[ERROR] 브라우저와 상태 동기화 실패: ${err.message}`);
                    });
                };

                // 자동 복구 메커니즘 추가
                modalDetectionService.setAutoRecoveryEnabled = true;

                // 일정 간격으로 모달 감지 시스템 상태 확인 및 필요시 복구
                setInterval(async () => {
                    if (!page) return;

                    try {
                        // 현재 페이지 URL 확인
                        const currentUrl = await page.url();

                        // 예약 페이지에서만 확인
                        if (currentUrl.includes('/booking')) {
                            console.log('[INFO] Checking modal detection system health...');

                            // 모달 감지 스크립트 존재 여부 확인
                            const scriptActive = await page.evaluate(() => {
                                return window.__modalObserverSetup === true;
                            }).catch(() => false);

                            if (!scriptActive) {
                                console.warn('[WARN] Modal detection system inactive, reinitializing...');
                                await modalDetectionService._reinitializeModalDetection();
                            } else {
                                console.log('[INFO] Modal detection system healthy');
                            }
                        }
                    } catch (error) {
                        console.error(`[ERROR] Modal detection health check failed: ${error.message}`);
                    }
                }, 60000); // 1분마다 확인
            }
        } catch (error) {
            console.error(`[ERROR] Failed to initialize modal detection service: ${error.message}`);
            console.error(error.stack);
            // 오류가 발생해도 계속 진행
        }

        // HTML 캡처 디렉토리 관련 코드 완전 제거

        // 액세스 토큰 가져오기
        try {
            console.log('[INFO] Attempting to get access token...');
            accessToken = await getAccessToken();
            console.log('[INFO] Successfully obtained access token');
        } catch (error) {
            console.error('[ERROR] Failed to start due to token error:', error.message);
            updateAppStatus('토큰 오류: ' + error.message);
            return;
        }

        // 브라우저 시작
        let browserData;
        try {
            updateAppStatus('브라우저 시작 중...');
            console.log('[INFO] Launching browser...');
            browserData = await launchBrowser();
            console.log('[INFO] Browser launched successfully');
        } catch (error) {
            console.error('[ERROR] Failed to launch browser:', error.message);
            updateAppStatus('브라우저 오류: ' + error.message);
            return;
        }

        const {page} = browserData;

        // 모달 감지 서비스에 현재 페이지 설정
        try {
            if (modalDetectionService) {
                modalDetectionService.setCurrentPage(page);
            }
        } catch (error) {
            console.error(`[ERROR] Failed to set page in modal detection service: ${error.message}`);
            // 오류가 발생해도 계속 진행
        }

        // 맵 객체 초기화
        const maps = {
            requestMap: new Map(),
            processedBookings: new Set(),
            paymentAmounts: new Map(),
            paymentStatus: new Map(),
            bookIdToIdxMap: new Map(),
            revenueToBookingMap: new Map(),
            bookingDataMap: new Map(), // 타임아웃 관리용 추가
        };

        // 정기적인 토큰 갱신 설정 (1시간마다)
        let tokenRefreshInterval = setInterval(async () => {
            try {
                console.log('[INFO] Refreshing access token...');
                accessToken = await getAccessToken();
                console.log('[INFO] Token refreshed successfully');
            } catch (error) {
                console.error('[ERROR] Failed to refresh token:', error.message);
                updateAppStatus('토큰 갱신 오류');
            }
        }, 60 * 60 * 1000); // 1시간마다

        // 핸들러 설정 - 모달 감지 서비스 전달
        setupRequestHandler(page, accessToken, maps, modalDetectionService);
        setupResponseHandler(page, accessToken, maps, modalDetectionService);

        // 타임아웃 관리 (5분마다 확인)
        const cleanupInterval = setInterval(() => {
            const now = Date.now();
            let expiredCount = 0;

            for (const [key, {timestamp}] of maps.bookingDataMap.entries()) {
                if (now - timestamp > TIMEOUT_MS) {
                    console.log(`[INFO] Timeout: Removing booking data for ${key}`);
                    maps.bookingDataMap.delete(key);
                    expiredCount++;
                }
            }

            if (expiredCount > 0) {
                console.log(`[INFO] Cleaned up ${expiredCount} expired booking data entries`);
            }

            // 매일 자정에 processedBookings 초기화
            const currentHour = new Date().getHours();
            const currentMinute = new Date().getMinutes();
            if (currentHour === 0 && currentMinute < 5) { // 자정~12:05 사이
                console.log('[INFO] Daily cleanup: Clearing processed bookings sets');
                maps.processedBookings.clear();
            }
        }, 60000); // 1분마다 확인

        // 매장 정보 로딩
        try {
            const storeId = getStoreId();
            const storeInfo = await getStoreInfo(storeId);
            if (storeInfo.success) {
                console.log(`[INFO] Store information loaded: ${storeInfo.name}${storeInfo.branch ? ` (${storeInfo.branch})` : ''}`);
                updateAppStatus('수집 중...');
            } else {
                console.warn(`[WARN] Failed to load store information: ${storeInfo.error}`);
                updateAppStatus('매장 정보 오류');
            }
        } catch (error) {
            console.error(`[ERROR] Error loading store information: ${error.message}`);
            updateAppStatus('매장 정보 오류');
        }

        // 애플리케이션 종료 시 정리
        app.on('will-quit', () => {
            console.log('[INFO] Application closing, cleaning up...');
            clearInterval(tokenRefreshInterval);
            clearInterval(cleanupInterval);
        });

        console.log('[INFO] Setup complete. Browser opened. Proceed with login and reservation management.');
    } catch (error) {
        console.error('[CRITICAL] Main process failed with unexpected error:', error);
        updateAppStatus('치명적 오류');
        app.quit();
    }
};

// 앱 상태 업데이트 함수
// 상태 전송 함수
function updateAppStatus(status) {
    appStatus = status;
    if (mainWindow) {
        mainWindow.webContents.send('app-status', status);
    }
}

// IPC 이벤트 핸들러 추가 - 모달 감지 서비스 관련
function setupAdditionalIpcHandlers() {

    // 모달 감지 서비스 상태 요청 처리
    ipcMain.on('get-modal-detection-status', (event) => {
        if (modalDetectionService) {
            event.reply('modal-detection-status', {
                active: modalDetectionService.isObserverSetup,
                counts: {} // 캡처 기능 비활성화로 인해 counts 객체 비움
            });
        } else {
            event.reply('modal-detection-status', {
                active: false,
                counts: {}
            });
        }
    });

    // HTML 캡처 관련 코드 완전 제거
}

ipcMain.on('cancel-modal-detected', () => {
    global.currentProcessingModalType = 'cancel';
    console.log('[INFO] Cancel modal detected via IPC, global flag set');

    // 일정 시간 후 플래그 초기화
    setTimeout(() => {
        global.currentProcessingModalType = null;
        console.log('[INFO] Cancel modal processing complete, global flag reset');
    }, 15000); // 15초 후 초기화
});

// IPC 이벤트 핸들러 설정
function setupIpcHandlers() {
    // 현재 매장 정보 요청 처리
    ipcMain.on('get-store-info', async (event) => {
        try {
            const storeId = getStoreId();
            const storeInfo = await getStoreInfo(storeId);
            event.reply('store-info-response', storeInfo);
        } catch (error) {
            console.error(`[ERROR] Error fetching store info: ${error.message}`);
            event.reply('store-info-response', {
                success: false,
                error: '매장 정보를 불러오는 중 오류가 발생했습니다.'
            });
        }
    });

    // 현재 매장 ID 요청 처리
    ipcMain.on('get-current-store-id', (event) => {
        event.reply('current-store-id', getStoreId());
    });

    // 매장 ID 유효성 검사 처리
    ipcMain.on('validate-store-id', async (event, storeId) => {
        try {
            const storeInfo = await getStoreInfo(storeId);
            event.reply('validate-store-id-response', storeInfo);
        } catch (error) {
            console.error(`[ERROR] Error validating store ID: ${error.message}`);
            event.reply('validate-store-id-response', {
                success: false,
                error: '매장 ID 검증 중 오류가 발생했습니다.'
            });
        }
    });

    // 매장 ID 저장 처리
    ipcMain.on('save-store-id', (event, storeId) => {
        try {
            const result = saveStoreId(storeId);
            event.reply('save-store-id-response', {success: result});
        } catch (error) {
            console.error(`[ERROR] Error saving store ID: ${error.message}`);
            event.reply('save-store-id-response', {
                success: false,
                error: '매장 ID 저장 중 오류가 발생했습니다.'
            });
        }
    });

    // 로그인 상태 요청 처리
    ipcMain.on('get-login-status', (event) => {
        try {
            const {hasCredentials} = getUserCredentials();
            event.reply('login-status-response', hasCredentials);
        } catch (error) {
            console.error(`[ERROR] Error getting login status: ${error.message}`);
            event.reply('login-status-response', false);
        }
    });

    // 계정 정보 요청 처리
    ipcMain.on('get-credentials', (event) => {
        try {
            const credentials = getUserCredentials();
            event.reply('credentials-response', credentials);
        } catch (error) {
            console.error(`[ERROR] Error getting credentials: ${error.message}`);
            event.reply('credentials-response', {
                phone: '',
                password: '',
                hasCredentials: false
            });
        }
    });

    // 계정 정보 저장 처리
    ipcMain.on('save-credentials', (event, {phone, password}) => {
        try {
            const result = saveUserCredentials(phone, password);
            event.reply('save-credentials-response', {success: result});
        } catch (error) {
            console.error(`[ERROR] Error saving credentials: ${error.message}`);
            event.reply('save-credentials-response', {success: false});
        }
    });

    // 계정 정보 삭제 처리
    ipcMain.on('clear-credentials', (event) => {
        try {
            const result = clearUserCredentials();
            event.reply('clear-credentials-response', {success: result});
        } catch (error) {
            console.error(`[ERROR] Error clearing credentials: ${error.message}`);
            event.reply('clear-credentials-response', {success: false});
        }
    });

    // 앱 재시작 요청 처리
    ipcMain.on('restart-app', () => {
        app.relaunch();
        app.exit(0);
    });

    // 추가 IPC 핸들러 설정
    setupAdditionalIpcHandlers();
}

process.on('uncaughtException', (error) => {
    console.error('[CRITICAL] Uncaught exception:', error);
    updateAppStatus('오류 발생');
    // 오류 발생해도 프로세스는 계속 실행
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('[CRITICAL] Unhandled rejection at:', promise, 'reason:', reason);
    updateAppStatus('오류 발생');
    // 오류 발생해도 프로세스는 계속 실행
});

// IPC 핸들러 설정
setupIpcHandlers();

// 메인 프로세스 시작
main().catch(error => {
    console.error('[ERROR] Main process failed:', error);
    console.error(error.stack); // 스택 트레이스 출력
    updateAppStatus('시작 오류');
    // 앱을 즉시 종료하지 않고 오류 상태로 유지
});