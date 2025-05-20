/**
 * cleanup.js - 프로그램 제거 시 실행되는 정리 스크립트
 */

const fs = require('fs');
const path = require('path');

try {
  console.log('Starting cleanup at:', new Date().toISOString());

  // 앱 데이터 디렉토리 찾기
  const appDataPath =
    process.env.APPDATA ||
    (process.platform === 'darwin'
      ? path.join(process.env.HOME, 'Library/Application Support')
      : path.join(process.env.HOME, '.config'));

  // 앱 데이터 폴더 삭제
  const appFolder = path.join(appDataPath, 'PandoK');
  console.log(`Checking app data folder: ${appFolder}`);
  if (fs.existsSync(appFolder)) {
    console.log(`Removing app data folder: ${appFolder}`);
    fs.rmSync(appFolder, { recursive: true, force: true });
    console.log(`Successfully removed: ${appFolder}`);
  } else {
    console.log(`App data folder does not exist: ${appFolder}`);
  }

  console.log('Cleanup completed successfully at:', new Date().toISOString());
} catch (error) {
  console.error('Error during cleanup:', error.message);
}