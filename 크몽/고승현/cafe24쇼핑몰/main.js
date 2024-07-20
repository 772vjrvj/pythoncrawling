const puppeteer = require('puppeteer');
const xlsx = require('xlsx');

// Function to set up browser and page
async function setupBrowser() {
    const browser = await puppeteer.launch({
        headless: false, // 브라우저가 백그라운드에서 실행되지 않도록 설정 (디버깅용)
        args: [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--incognito',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ],
        ignoreDefaultArgs: ['--enable-automation'], // Disable automation flags
    });

    const page = await browser.newPage();

    // Bypass the detection of automated software
    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    });

    await page.setViewport({ width: 1280, height: 800 });
    return { browser, page };
}

// Function to extract meta tags information
async function extractMetaTags(page) {
    const metaTags = await page.evaluate(() => {
        const ogSiteName = document.querySelector('meta[property="og:site_name"]');
        const ogUrl = document.querySelector('meta[property="og:url"]');
        const uidScript = document.querySelector('script[src*="cfa.html"]');
        const favicon = document.querySelector('link[rel="shortcut icon"]');
        const bodyStyle = document.querySelector('body').style.background;

        return {
            siteName: ogSiteName ? ogSiteName.content : null,
            siteUrl: ogUrl ? ogUrl.content : null,
            uid: uidScript ? new URLSearchParams(new URL(uidScript.src).search).get('uid') : null,
            favicon: favicon ? favicon.href : null,
            themeColor: bodyStyle || null
        };
    });
    return metaTags;
}

// Function to extract footer information
async function extractFooterInfo(page, baseUrl) {
    const footerInfo = await page.evaluate((baseUrl) => {
        const footer = document.querySelector('.xans-element-.xans-layout.xans-layout-footer');
        if (!footer) return null;

        const extractText = (selector) => {
            const element = footer.querySelector(selector);
            return element ? element.innerText.replace(/.*:/, '').trim() : null;
        };

        const extractTextByLabel = (label) => {
            const elements = Array.from(footer.querySelectorAll('span, li'));
            const element = elements.find(el => el.innerText.includes(label));
            return element ? element.innerText.replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;
        };

        const companyName = extractText('.address li:first-child') ||
            extractTextByLabel('Company:');

        const ceo = extractText('.address li:nth-child(2)') ||
            extractTextByLabel('Ceo:');

        const businessLicense = extractText('.address li:nth-child(3)') ||
            extractTextByLabel('Company Reg.No:');

        const onlineBusinessLicense = extractText('.address li:nth-child(4)') ||
            extractTextByLabel('Network Reg.No:');

        const customerServicePhoneElement = Array.from(footer.querySelectorAll('span, li')).find(el => el.innerText.includes('tel:'));
        const customerServicePhone = customerServicePhoneElement ? customerServicePhoneElement.innerText.split('E-mail:')[0].replace('tel:', '').trim() : null;

        let representativeImage = footer.querySelector('.대표_이미지_클래스명 img')?.src || null;
        if (!representativeImage) {
            const logoImage = document.querySelector('a img[src*="logo"], a img[alt*="로고"], a img[alt*="베이델리"], a img[alt="logo"]');
            representativeImage = logoImage ? logoImage.src : null;
        }

        if (representativeImage && !representativeImage.startsWith('http')) {
            representativeImage = new URL(representativeImage, baseUrl).href;
        }

        return {
            companyName,
            ceo,
            businessLicense,
            onlineBusinessLicense,
            customerServicePhone,
            representativeImage
        };
    }, baseUrl);
    return footerInfo;
}

// Function to write data to Excel
function writeToExcel(data) {
    const workbook = xlsx.utils.book_new();
    const worksheet = xlsx.utils.json_to_sheet(data);
    xlsx.utils.book_append_sheet(workbook, worksheet, 'Shop Info');
    xlsx.writeFile(workbook, 'shop_info.xlsx');
}

// Main function
async function main(url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    const { browser, page } = await setupBrowser();

    await page.goto(url, { waitUntil: 'networkidle0' });

    const metaTags = await extractMetaTags(page);
    const footerInfo = await extractFooterInfo(page, url);

    const shopInfo = {
        쇼핑몰이름: metaTags.siteName,
        쇼핑몰UID: metaTags.uid,
        쇼핑몰URL: metaTags.siteUrl,
        파비콘이미지: metaTags.favicon ? new URL(metaTags.favicon, metaTags.siteUrl).href : null,
        테마컬러: metaTags.themeColor,
        회사명: footerInfo?.companyName,
        쇼핑몰대표자: footerInfo?.ceo,
        쇼핑몰대표이미지: footerInfo?.representativeImage,
        고객센터전화번호: footerInfo?.customerServicePhone,
        사업자등록번호: footerInfo?.businessLicense,
        통신판매번호: footerInfo?.onlineBusinessLicense
    };

    console.log(shopInfo);
    writeToExcel([shopInfo]);

    await browser.close();
}

// Replace 'YOUR_URL_HERE' with the actual URL you want to scrape
const url = 'dailyjou.com';
main(url);
