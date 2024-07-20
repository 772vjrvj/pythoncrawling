const puppeteer = require('puppeteer');
const xlsx = require('xlsx');
const axios = require('axios');

// Function to set up browser and page
async function setupBrowser() {
    const browser = await puppeteer.launch({
        headless: false, // 디버깅용
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

        const representativeImageElement = document.querySelector(`a img[src*="logo"], a img[alt*="로고"], a img[alt*="${ogSiteName ? ogSiteName.content : ''}"], a img[alt="logo"]`);
        const representativeImage = representativeImageElement ? representativeImageElement.src : null;

        return {
            siteName: ogSiteName ? ogSiteName.content : null,
            siteUrl: ogUrl ? ogUrl.content : null,
            uid: uidScript ? new URLSearchParams(new URL(uidScript.src).search).get('uid') : null,
            favicon: favicon ? favicon.href : null,
            themeColor: bodyStyle || '',
            representativeImage
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

        const elements = Array.from(footer.querySelectorAll('span, li'));
        const onlineBusinessLicenseElement = elements.find(el => el.innerText.includes('통신판매업신고'));
        const onlineBusinessLicense = onlineBusinessLicenseElement ? onlineBusinessLicenseElement.innerText.replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;

        const customerServicePhoneElement = elements.find(el => el.innerText.includes('tel:'));
        const customerServicePhone = customerServicePhoneElement ? customerServicePhoneElement.innerText.split('E-mail:')[0].replace('tel:', '').trim() : null;

        return {
            companyName,
            ceo,
            businessLicense,
            onlineBusinessLicense,
            customerServicePhone
        };
    }, baseUrl);
    return footerInfo;
}

// Function to extract banner information
async function extractBannerInfo(page, baseUrl) {
    const bannerInfo = await page.evaluate((baseUrl) => {
        const banners = [];
        const topBanners = document.querySelectorAll('#topbanner, [app4you-smart-banner]');

        topBanners.forEach(banner => {
            const img = banner.querySelector('img');
            const aTag = banner.querySelector('a');

            if (img && aTag) {
                const imgUrl = img.src.startsWith('http') ? img.src : new URL(img.src, baseUrl).href;
                const linkUrl = aTag.href.startsWith('http') ? aTag.href : new URL(aTag.href, baseUrl).href;
                banners.push({ '배너이미지 URL': imgUrl, '배너 링크': linkUrl });
            }
        });

        return banners.length > 0 ? banners : [{ '배너이미지 URL': '', '배너 링크': '' }];
    }, baseUrl);
    return bannerInfo;
}

// Function to update category names and build hierarchy with parent references
function updateCategoryNames(data) {
    return data.map(item => {
        if (item.name.startsWith('<font')) {
            const nameMatch = item.name.match(/>([^<]+)</);
            if (nameMatch && nameMatch[1]) {
                item.name = nameMatch[1];
            }
        }
        return item;
    });
}

function buildHierarchyWithParentReferences(data) {
    const updatedData = updateCategoryNames(data);
    const categories = updatedData.reduce((acc, item) => {
        acc[item.cate_no] = { ...item, data_list: [] };
        return acc;
    }, {});

    const result = [];

    updatedData.forEach(item => {
        if (item.parent_cate_no !== 1) {
            const parent = categories[item.parent_cate_no];
            if (parent) {
                parent.data_list.push(categories[item.cate_no]);
            }
        } else {
            result.push(categories[item.cate_no]);
        }
    });

    return result;
}

// Function to fetch category data from the given URL
async function fetchCategoryData(url) {
    try {
        const response = await axios.get(url + '/exec/front/Product/SubCategory');
        return response.data;
    } catch (error) {
        console.error('Error fetching category data:', error);
        return [];
    }
}

// Function to write data to Excel
function writeToExcel(shopInfo, bannerInfo, productDetails) {
    const workbook = xlsx.utils.book_new();

    // Write shop info
    const shopSheet = xlsx.utils.json_to_sheet([shopInfo]);
    xlsx.utils.book_append_sheet(workbook, shopSheet, '쇼핑몰 정보');

    // Write banner info
    const bannerSheet = xlsx.utils.json_to_sheet(bannerInfo);
    xlsx.utils.book_append_sheet(workbook, bannerSheet, '메인배너');

    // Write product details
    const productSheet = xlsx.utils.json_to_sheet(productDetails);
    xlsx.utils.book_append_sheet(workbook, productSheet, '상품정보');

    xlsx.writeFile(workbook, 'shop_info.xlsx');
}

// Function to log category information
async function logCategoryInfo(url, categories, productDetails) {
    const logCategory = async (category, parentNames = []) => {
        const currentPath = parentNames.concat({ name: category.name });

        if (category.data_list.length === 0) {
            const category_menu = JSON.stringify(currentPath, null, 2);
            const category_url = `${url}/${category.design_page_url}${category.param}`;

            let pageNum = 1;
            const count = 200;
            let hasMoreData = true;

            while (hasMoreData) {
                const detail_url = `${url}/exec/front/Product/ApiProductNormal${category.param}&supplier_code=S0000000&page=${pageNum}&bInitMore=F&count=${count}`;
                console.log('"카테고리(메뉴)*": ', category_menu);
                console.log('detail_url: ', detail_url);

                const delay = Math.floor(Math.random() * (5000 - 2000 + 1)) + 2000;
                await new Promise(resolve => setTimeout(resolve, delay));

                const response = await axios.get(detail_url, { timeout: 20000 });
                const data = response.data.rtn_data.data;

                if (!data || data.length === 0) {
                    hasMoreData = false;
                    console.log('data length 없음');
                } else {
                    console.log('data length: ', data.length);
                    for (const product of data) {
                        const productDetail = {
                            "상품ID": product.product_no,
                            "상품명*": product.product_name_tag,
                            "카테고리(메뉴)*": category_menu,
                            "상품 상세(html)*": "",
                            "상품가격*": product.product_price,
                            "상품 할인가격*": product.origin_prd_price_sale,
                            "상품 이미지*": "",
                            "상품 잔여수량": product.stock_number,
                            "상품 태그": product.product_tag,
                            "상품 상세화면 URL*": product.seo_url,
                            "옵션": [],
                            "옵션 정보": [],
                            "상품 고지 정보": "",
                            "카테고리(URL)": category_url
                        };

                        // Fetch additional product details
                        await fetchProductDetails(productDetail, url);

                        productDetails.push(productDetail);
                    }
                    pageNum++;
                }
            }
        } else {
            for (const subCategory of category.data_list) {
                await logCategory(subCategory, currentPath);
            }
        }
    };

    for (const [index, category] of categories.entries()) {
        await logCategory(category);
    }
}

// Function to fetch product details
async function fetchProductDetails(productDetail, url) {
    const { browser, page } = await setupBrowser();
    await page.goto(productDetail["상품 상세화면 URL*"], { waitUntil: 'networkidle2', timeout: 60000 });

    // Extract product detail HTML
    const productDetailHtml = await page.evaluate(() => {
        const detailElement = document.querySelector('#prdDetail');
        return detailElement ? detailElement.innerHTML : '';
    });
    productDetail["상품 상세(html)*"] = productDetailHtml;

    // Extract product images
    const productImages = await page.evaluate(() => {
        const imgElements = document.querySelectorAll('.xans-element-.xans-product.xans-product-image img');
        const imgUrls = [];
        imgElements.forEach(img => {
            const src = img.getAttribute('src');
            if (src) {
                imgUrls.push(src);
            }
        });
        return imgUrls;
    });
    productDetail["상품 이미지*"] = productImages;

    // Extract option information
    const options = await page.evaluate(() => {
        const optionElements = document.querySelectorAll('.xans-element-.xans-product.xans-product-option.xans-record-');
        const options = new Map();
        optionElements.forEach(optionElement => {
            const th = optionElement.querySelector('th');
            const select = optionElement.querySelector('select');
            if (th && select) {
                const optionTitle = th.innerText.trim();
                const optionValues = [];
                const optionItems = select.querySelectorAll('option');
                optionItems.forEach(optionItem => {
                    const value = optionItem.innerText.trim();
                    if (value !== '*' && value !== '**' && value !== '- [필수] 옵션을 선택해 주세요 -' && !optionItem.hasAttribute('disabled')) {
                        optionValues.push(value);
                    }
                });
                if (options.has(optionTitle)) {
                    options.set(optionTitle, [...options.get(optionTitle), ...optionValues]);
                } else {
                    options.set(optionTitle, optionValues);
                }
            }
        });
        return Array.from(options.entries()).map(([key, value]) => ({ [key]: value }));
    });
    productDetail["옵션 정보"] = options;

    // Extract product notice information
    const productNotice = await page.evaluate(() => {
        const noticeElement = document.querySelector('#prdInfo');
        const notice = {};
        if (noticeElement) {
            const paymentInfo = noticeElement.querySelector('.ec-base-table.table-th-left.mgt10 tbody tr td:contains("상품결제정보") + td');
            const exchangeInfo = noticeElement.querySelector('.ec-base-table.table-th-left.mgt10 tbody tr td:contains("교환 및 반품정보") + td');
            const shippingInfo = noticeElement.querySelector('.ec-base-table.table-th-left.mgt10 tbody tr td:contains("배송정보") + td');

            if (paymentInfo) notice["상품결제정보"] = paymentInfo.innerText.trim();
            if (exchangeInfo) notice["교환 및 반품정보"] = exchangeInfo.innerText.trim();
            if (shippingInfo) notice["배송정보"] = shippingInfo.innerText.trim();

            const imgElements = noticeElement.querySelectorAll('img');
            const imgUrls = [];
            imgElements.forEach(img => {
                const src = img.getAttribute('src');
                if (src) {
                    imgUrls.push({ url: src });
                }
            });
            if (imgUrls.length > 0) notice["이미지"] = imgUrls;
        }
        return notice;
    });
    productDetail["상품 고지 정보"] = productNotice;

    // Store option titles
    const optionTitles = options.map(option => Object.keys(option)[0]);
    productDetail["옵션"] = optionTitles;

    console.log("productDetail : ", JSON.stringify(productDetail, null, 2));

    await browser.close();
}

// Main function
async function main(url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    const { browser, page } = await setupBrowser();

    await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });

    const metaTags = await extractMetaTags(page);
    const footerInfo = await extractFooterInfo(page, url);
    const bannerInfo = await extractBannerInfo(page, url);

    // Fetch category data from the given URL
    const categoryData = await fetchCategoryData(url);
    const categoryInfo = buildHierarchyWithParentReferences(categoryData);

    const shopInfo = {
        '쇼핑몰 이름': metaTags.siteName,
        '쇼핑몰 UID': metaTags.uid,
        '쇼핑몰 URL': metaTags.siteUrl,
        '파비콘 이미지': metaTags.favicon ? new URL(metaTags.favicon, metaTags.siteUrl).href : null,
        '테마컬러': metaTags.themeColor,
        '회사명': footerInfo?.companyName,
        '쇼핑몰 대표자': footerInfo?.ceo,
        '쇼핑몰 대표 이미지': metaTags.representativeImage ? new URL(metaTags.representativeImage, metaTags.siteUrl).href : null,
        '고객센터 전화번호': footerInfo?.customerServicePhone,
        '사업자등록번호': footerInfo?.businessLicense,
        '통신판매번호': footerInfo?.onlineBusinessLicense
    };

    const productDetails = [];

    await logCategoryInfo(url, categoryInfo, productDetails);

    writeToExcel(shopInfo, bannerInfo, productDetails);

    await browser.close();
}

// Replace 'YOUR_URL_HERE' with the actual URL you want to scrape
const url = 'dailyjou.com';
main(url);
