/**
 * @file env.js
 * @description
 * 애플리케이션 설정(config.json)을 관리하는 유틸리티 모듈.
 * 사용자 정보, 매장 ID, Chrome 실행 경로, 기본 API URL 등 환경설정 데이터를
 * OS별 로컬 저장소(Windows: %APPDATA%, macOS/Linux: ~/.config 등)에 JSON으로 저장하고 불러옵니다.
 *
 * 주요 기능:
 * - 설정 파일 읽기/쓰기 (storeId, user credentials)
 * - Chrome 실행 경로 반환
 * - API 베이스 URL 및 타임아웃 설정 제공
 *
 * 사용 예:
 * const { getStoreId, saveUserCredentials, CHROME_PATH } = require('./config/env');
 */



// Node.js의 내장 모듈 path를 불러옵니다. 운영체제에 맞는 파일 경로를 안전하게 생성할 때 사용합니다.
const path = require('path');

//파일 시스템(fs) 모듈을 불러옵니다. 파일 읽기/쓰기, 존재 여부 확인 등에 사용됩니다.
const fs = require('fs');

//.env 파일을 자동으로 읽고 환경변수로 등록합니다.
// 예: .env에 있는 API_KEY=1234 → process.env.API_KEY로 접근 가능.
require('dotenv').config();

// 설정 파일 경로
// OS에 따라 설정 저장 경로를 다르게 지정합니다:
// Windows: %APPDATA%/kimcady
// macOS: ~/Library/Application Support/kimcady
// Linux: ~/.config/kimcady

//C:\Users\772vj\AppData\Roaming\kimcady
//C:\Users\사용자이름\AppData\Roaming\kimcady
const CONFIG_PATH = path.join(process.env.APPDATA || (process.platform === 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + '/.config'), 'kimcady');
const CONFIG_FILE = path.join(CONFIG_PATH, 'config.json');

// 기본 StoreID (처음 실행하거나 설정 파일이 없는 경우 사용)
const DEFAULT_STORE_ID = '6690d7ea750ff9a6689e9af3';

// 설정 파일에서 읽기
const getConfig = () => {
    try {
        // 설정 디렉토리가 없으면 생성
        // 설정 폴더가 없으면 새로 만듭니다. recursive: true로 중첩 폴더까지 생성 가능.
        if (!fs.existsSync(CONFIG_PATH)) {
            fs.mkdirSync(CONFIG_PATH, {recursive: true});
        }

        // 설정 파일이 있으면 읽기
        if (fs.existsSync(CONFIG_FILE)) {
            return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
        }
    } catch (error) {
        console.error(`[ERROR] Failed to read config file: ${error.message}`);
    }

    return {storeId: DEFAULT_STORE_ID};
};

// 설정 파일에 저장
const saveConfig = (config) => {
    try {
        // 설정 디렉토리가 없으면 생성
        if (!fs.existsSync(CONFIG_PATH)) {
            fs.mkdirSync(CONFIG_PATH, {recursive: true});
        }

        //설정 파일을 예쁘게(2칸 들여쓰기) JSON 형식으로 저장합니다.
        // {
        //     "storeId": "6809c437fd32e99404824e40",
        //     "userPhone": "01025370280",
        //     "userPassword": "ok1228326@"
        // }
        fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');

        console.log(`[INFO] Config saved successfully`);
        return true;
    } catch (error) {
        console.error(`[ERROR] Failed to save config: ${error.message}`);
        return false;
    }
};

// 매장 ID 가져오기
const getStoreId = () => {
    const config = getConfig();
    return config.storeId || DEFAULT_STORE_ID;
};

// 매장 ID 저장
const saveStoreId = (storeId) => {
    const config = getConfig();
    config.storeId = storeId;
    return saveConfig(config);
};

// 사용자 계정 정보 가져오기
const getUserCredentials = () => {
    const config = getConfig();

    if (config.userPhone && config.userPassword) {
        return {
            phone: config.userPhone,
            password: config.userPassword,
            hasCredentials: true
        };
    }

    return {
        phone: '',
        password: '',
        hasCredentials: false
    };
};

// 사용자 계정 정보 저장
const saveUserCredentials = (phone, password) => {
    const config = getConfig();

    config.userPhone = phone;
    config.userPassword = password;

    return saveConfig(config);
};

// 사용자 계정 정보 삭제
const clearUserCredentials = () => {
    const config = getConfig();

    delete config.userPhone;
    delete config.userPassword;

    return saveConfig(config);
};

//크롬 경로 확인
const getChromePath = () => {
    if (process.platform === 'win32') {
        const defaultPath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
        return fs.existsSync(defaultPath) ? defaultPath : 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
    } else if (process.platform === 'darwin') {
        return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    } else {
        return '/usr/bin/google-chrome';
    }
};

module.exports = {
    getStoreId,
    saveStoreId,
    getUserCredentials,
    saveUserCredentials,
    clearUserCredentials,
    CHROME_PATH: getChromePath(),
    TIMEOUT_MS: 5 * 60 * 1000, // 5분 타임아웃
    API_BASE_URL: 'https://api.dev.24golf.co.kr',
    //API_BASE_URL: 'https://api.anytimegolf24.com',
    //API_BASE_URL: 'https://api.24golf.co.kr',
};
