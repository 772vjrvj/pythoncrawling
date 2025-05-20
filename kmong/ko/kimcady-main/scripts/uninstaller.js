/**
 * uninstaller.js - 백업 언인스톨러 스크립트 (선택적)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 관리자 권한 확인
function isAdmin() {
  if (process.platform !== 'win32') return true;
  try {
    execSync('net session', { stdio: 'ignore' });
    return true;
  } catch (err) {
    return false;
  }
}

// 수동 제거 함수
function manualUninstall() {
  if (!isAdmin()) {
    console.error('This script requires administrator privileges.');
    process.exit(1);
  }

  console.log('Starting manual uninstallation at:', new Date().toISOString());

  // 앱 데이터 폴더
  const appDataPath =
    process.env.APPDATA ||
    (process.platform === 'darwin'
      ? path.join(process.env.HOME, 'Library/Application Support')
      : path.join(process.env.HOME, '.config'));
  const appFolder = path.join(appDataPath, 'PandoK');

  // 앱 데이터 삭제
  console.log(`Checking app data folder: ${appFolder}`);
  if (fs.existsSync(appFolder)) {
    console.log(`Removing app data folder: ${appFolder}`);
    try {
      fs.rmSync(appFolder, { recursive: true, force: true });
      console.log(`Successfully removed: ${appFolder}`);
    } catch (err) {
      console.error(`Failed to remove app data folder: ${appFolder}:`, err.message);
    }
  } else {
    console.log(`App data folder does not exist: ${appFolder}`);
  }

  console.log('Manual uninstallation completed at:', new Date().toISOString());
}

// 실행
try {
  manualUninstall();
} catch (error) {
  console.error('Error during uninstallation:', error.message);
  process.exit(1);
}