const { app, BrowserWindow, screen } = require('electron');
// Electron의 주요 객체를 불러옵니다:
// app: 애플리케이션 생명주기 제어
// BrowserWindow: 윈도우 생성
// screen: 모니터 해상도 및 다중 디스플레이 관련 정보 제공

const path = require('path');

//Electron 메인 브라우저 창을 생성하는 함수
const createWindow = () => {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  console.log(`[INFO] Screen dimensions: ${width}x${height}`);
  //현재 사용하는 주 디스플레이의 작업 가능한 화면 영역(작업표시줄 제외)의 해상도를 가져옴

  //좌상단 (0, 0) 위치에서 전체 화면 크기로 창 생성
  const win = new BrowserWindow({
    width,
    height,
    x: 0,
    y: 0,
    webPreferences: {
      nodeIntegration: true,   //렌더러에서 require 가능
      contextIsolation: false, //브라우저와 Node.js 환경이 같은 컨텍스트에서 동작 (보안상은 권장되지 않음)
      webSecurity: false       //CORS 보안 무시 (스크래핑 목적 등일 때 사용)
    },
    show: false, //창을 생성하되, 바로 보여주지 않고 ready-to-show 이벤트에서 보여줍니다
  });


  win.once('ready-to-show', () => {
    win.show();
    win.maximize();
    console.log('[INFO] Electron window maximized');
  });
  //DOM이 준비되면 창을 보여주고 최대화

  win.loadFile(path.join(__dirname, '../../index.html'));
  //index.html을 로드합니다 (상위 디렉토리 기준 경로)
  return win;
};

const setupElectron = () => {
  let mainWindow = null;

  // 이미 준비된 경우 바로 창 생성
  // 준비되지 않았으면 app.whenReady()를 통해 기다렸다가 생성
  if (app.isReady()) {
    mainWindow = createWindow();
  } else {
    app.whenReady().then(() => {
      mainWindow = createWindow();

      //macOS에서 Dock 아이콘 클릭 시 창이 없는 경우 새 창을 생성
      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          mainWindow = createWindow();
        }
      });
    });
  }

  app.on('window-all-closed', () => app.quit());
  //모든 창이 닫히면 앱 종료 (macOS 제외)

  return mainWindow;
};

module.exports = {
  setupElectron,
  screen // ✅ 이거 추가해야 puppeteer.js에서 사용할 수 있습니다
};