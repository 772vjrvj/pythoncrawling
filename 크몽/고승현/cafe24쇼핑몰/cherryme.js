const axios = require('axios');
const xlsx = require('xlsx');
const puppeteer = require('puppeteer');
const moment = require('moment');

/**
 * Puppeteer 브라우저 인스턴스를 시작합니다.
 * @returns {Promise<Browser>} 시작된 브라우저 인스턴스.
 */
async function launchBrowser() {
    return await puppeteer.launch({
        headless: true,
        args: [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--incognito',
            '--disable-extensions',
            '--proxy-server="direct://"',
            '--proxy-bypass-list=*',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ],
        ignoreDefaultArgs: ['--enable-automation'],
    });
}

/**
 * 주어진 Puppeteer 페이지에서 메타 태그와 UID를 추출합니다.
 * @param {Page} page - Puppeteer 페이지 인스턴스.
 * @returns {Promise<Object>} 추출된 메타 태그와 UID를 포함하는 객체.
 */
async function extractMetaTags(page) {
    try {
        const metaTags = await page.evaluate(() => {
            const getMetaContent = (property) => {
                const element = document.querySelector(`meta[property="${property}"]`);
                return element ? element.getAttribute('content') : null;
            };

            const getLinkHref = (rel) => {
                const element = document.querySelector(`link[rel="${rel}"]`);
                return element ? element.getAttribute('href') : null;
            };

            const getCssStyle = (selector, property) => {
                const element = document.querySelector(selector);
                return element ? window.getComputedStyle(element).getPropertyValue(property) : '';
            };

            const rgbToHex = (rgb) => {
                const result = rgb.match(/\d+/g).map((num) => {
                    const hex = parseInt(num, 10).toString(16).padStart(2, '0');
                    return hex;
                });
                return `#${result.join('')}`;
            };

            const getImageSrc = (selectors) => {
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return element.getAttribute('src');
                    }
                }
                return null;
            };

            const ogSiteName = getMetaContent('og:site_name');
            const ogUrl = getMetaContent('og:url');
            const favicon = getLinkHref('shortcut icon');
            const bodyStyle = getCssStyle('body#main', 'background-color');
            const themeColor = bodyStyle ? rgbToHex(bodyStyle) : '';
            const representativeImage = getImageSrc([
                'a img[src*="logo"]',
                'a img[alt*="로고"]',
                `a img[alt*="${ogSiteName ? ogSiteName : ''}"]`,
                'a img[alt="logo"]'
            ]);

            return {
                siteName: ogSiteName || null,
                siteUrl: ogUrl || null,
                favicon: favicon || null,
                themeColor: themeColor,
                representativeImage: representativeImage || null
            };
        });

        const uid = await page.evaluate(() => {
            const scripts = Array.from(document.querySelectorAll('script[src*="cfa.html"]'));
            for (const script of scripts) {
                const src = script.getAttribute('src');
                const matches = src.match(/uid=([^&]*)/);
                if (matches) {
                    return matches[1];
                }
            }
            return null;
        });

        return { ...metaTags, uid };
    } catch (error) {
        console.error('메타 태그 추출 중 오류 발생:', error);
        return {};
    }
}

/**
 * 주어진 Puppeteer 페이지에서 푸터 정보를 추출합니다.
 * @param {Page} page - Puppeteer 페이지 인스턴스.
 * @returns {Promise<Object>} 추출된 푸터 정보를 포함하는 객체.
 */
async function extractFooterInfo(page) {
    try {
        return await page.evaluate(() => {
            const footer = document.querySelector('.xans-element-.xans-layout.xans-layout-footer');
            if (!footer) return null;

            const extractText = (selector) => {
                const element = footer.querySelector(selector);
                return element ? element.textContent.replace(/.*:/, '').trim() : null;
            };

            const extractTextByLabel = (label) => {
                const elements = Array.from(footer.querySelectorAll('span, li'));
                const element = elements.find(el => el.textContent.includes(label));
                return element ? element.textContent.replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;
            };

            const companyName = extractText('.address li:first-child') || extractTextByLabel('Company:');
            const ceo = extractText('.address li:nth-child(2)') || extractTextByLabel('Ceo:');
            const businessLicense = extractText('.address li:nth-child(3)') || extractTextByLabel('Company Reg.No:');
            const onlineBusinessLicenseElement = Array.from(footer.querySelectorAll('span, li')).find(el => el.textContent.includes('통신판매업신고'));
            const onlineBusinessLicense = onlineBusinessLicenseElement ? onlineBusinessLicenseElement.textContent.replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;
            const customerServicePhoneElement = Array.from(footer.querySelectorAll('span, li')).find(el => el.textContent.includes('tel:'));
            const customerServicePhone = customerServicePhoneElement ? customerServicePhoneElement.textContent.split('E-mail:')[0].replace('tel:', '').trim() : null;

            return {
                companyName,
                ceo,
                businessLicense,
                onlineBusinessLicense,
                customerServicePhone
            };
        });
    } catch (error) {
        console.error('푸터 정보 추출 중 오류 발생:', error);
        return {};
    }
}

/**
 * 주어진 Puppeteer 페이지에서 배너 정보를 추출합니다.
 * @param {Page} page - Puppeteer 페이지 인스턴스.
 * @param {string} baseUrl - 기본 URL.
 * @returns {Promise<Array>} 추출된 배너 정보를 포함하는 배열.
 */
async function extractBannerInfo(page, baseUrl) {
    try {
        return await page.evaluate((baseUrl) => {
            const banners = [];
            const topBanners = document.querySelectorAll('#topbanner, [app4you-smart-banner]');

            topBanners.forEach(banner => {
                const img = banner.querySelector('img');
                const aTag = banner.querySelector('a');

                if (img && aTag) {
                    const imgUrl = img.getAttribute('src').startsWith('http') ? img.getAttribute('src') : new URL(img.getAttribute('src'), baseUrl).href;
                    const linkUrl = aTag.getAttribute('href').startsWith('http') ? aTag.getAttribute('href') : new URL(aTag.getAttribute('href'), baseUrl).href;
                    banners.push({ '배너이미지 URL': imgUrl, '배너 링크': linkUrl });
                }
            });

            return banners.length > 0 ? banners : [{ '배너이미지 URL': '', '배너 링크': '' }];
        }, baseUrl);
    } catch (error) {
        console.error('배너 정보 추출 중 오류 발생:', error);
        return [];
    }
}

/**
 * 카테고리 이름을 업데이트합니다.
 * @param {Array} data - 카테고리 데이터 배열.
 * @returns {Array} 업데이트된 카테고리 데이터 배열.
 */
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

/**
 * 부모 참조를 포함한 카테고리 계층 구조를 구축합니다.
 * @param {Array} data - 카테고리 데이터 배열.
 * @returns {Array} 부모 참조를 포함한 카테고리 계층 배열.
 */
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

/**
 * 카테고리 데이터를 가져옵니다.
 * @param {string} url - API 요청을 위한 기본 URL.
 * @returns {Promise<Array>} 가져온 카테고리 데이터 배열.
 */
async function fetchCategoryData(url) {
    try {
        const response = await axios.get(url + '/exec/front/Product/SubCategory');
        return response.data;
    } catch (error) {
        console.error('카테고리 데이터 가져오기 중 오류 발생:', error);
        return [];
    }
}

/**
 * 텍스트를 지정된 길이로 자릅니다.
 * @param {string} text - 자를 텍스트.
 * @param {number} maxLength - 최대 길이.
 * @returns {string} 자른 텍스트.
 */
function truncateText(text, maxLength = 32767) {
    if (typeof text === 'string' && text.length > maxLength) {
        return text.substring(0, maxLength);
    }
    return text;
}

/**
 * 추출된 정보를 Excel 파일에 씁니다.
 * @param {Object} shopInfo - 쇼핑몰 정보.
 * @param {Array} bannerInfo - 배너 정보.
 * @param {Array} productDetails - 상품 상세 정보.
 * @param {Array} productRepls - 리뷰 정보.
 */
function writeToExcel(shopInfo, bannerInfo, productDetails, productRepls) {
    const workbook = xlsx.utils.book_new();

    // 긴 텍스트 자르기
    const truncatedShopInfo = {};
    for (const key in shopInfo) {
        if (Object.hasOwnProperty.call(shopInfo, key)) {
            truncatedShopInfo[key] = truncateText(shopInfo[key]);
        }
    }

    const shopSheet = xlsx.utils.json_to_sheet([truncatedShopInfo]);
    xlsx.utils.book_append_sheet(workbook, shopSheet, '쇼핑몰 정보');

    const bannerSheet = xlsx.utils.json_to_sheet(bannerInfo);
    xlsx.utils.book_append_sheet(workbook, bannerSheet, '메인배너');

    // 긴 텍스트 자르기
    const truncatedProductDetails = productDetails.map(product => {
        const truncatedProduct = {};
        for (const key in product) {
            if (Object.hasOwnProperty.call(product, key)) {
                truncatedProduct[key] = truncateText(product[key]);
            }
        }
        return truncatedProduct;
    });

    const productSheet = xlsx.utils.json_to_sheet(truncatedProductDetails);
    xlsx.utils.book_append_sheet(workbook, productSheet, '상품정보');

    // 긴 텍스트 자르기
    const truncatedProductRepls = productRepls.map(repl => {
        const truncatedRepl = {};
        for (const key in repl) {
            if (Object.hasOwnProperty.call(repl, key)) {
                truncatedRepl[key] = truncateText(repl[key]);
            }
        }
        return truncatedRepl;
    });

    const replSheet = xlsx.utils.json_to_sheet(truncatedProductRepls);
    xlsx.utils.book_append_sheet(workbook, replSheet, '리뷰정보');

    xlsx.writeFile(workbook, 'shop_info.xlsx');
}

/**
 * 카테고리 정보를 로그로 기록하고, 상품 정보를 추출합니다.
 * @param {string} url - 기본 URL.
 * @param {Array} categories - 카테고리 정보 배열.
 * @param {Array} productDetails - 상품 상세 정보 배열.
 * @param {Array} productRepls - 리뷰 정보 배열.
 */
async function logCategoryInfo(url, categories, productDetails, productRepls) {
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

                await new Promise(resolve => setTimeout(resolve, 2000));

                try {
                    const response = await axios.get(detail_url, { timeout: 20000 });
                    const data = response.data.rtn_data.data;

                    if (!data || data.length === 0) {
                        hasMoreData = false;
                        console.log('data length 없음');
                    } else {
                        console.log('data length: ', data.length);
                        for (const [index, product] of data.entries()) {
                            const productDetail = {
                                "상품ID": product.product_no,
                                "상품명*": product.product_name_tag,
                                "카테고리(메뉴)*": category_menu,
                                "상품 상세(html)*": "",
                                "상품가격*": product.product_custom || product.product_price,
                                "상품 할인가격*": product.origin_prd_price_sale || product.product_price,
                                "상품 이미지*": "",
                                "상품 잔여수량": product.stock_number,
                                "상품 태그": product.product_tag,
                                "상품 상세화면 URL*": product.seo_url,
                                "옵션": [],
                                "옵션 정보": [],
                                "상품 고지 정보": "",
                                "카테고리(URL)": category_url
                            };

                            const reviews = await fetchProductDetails(productDetail, url);
                            productDetails.push(productDetail);
                            productRepls.push(...reviews);
                            if(index === 1){
                                hasMoreData = false;
                                break;
                            }
                        }
                        pageNum++;


                    }
                } catch (error) {
                    console.error('상품 상세 정보 가져오기 중 오류 발생:', error);
                    hasMoreData = false;
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

/**
 * 주어진 함수에 대해 재시도합니다.
 * @param {Function} fn - 재시도할 함수.
 * @param {number} [retries=4] - 재시도 횟수.
 * @param {number} [delay=2000] - 재시도 사이의 지연 시간.
 * @param {*} [defaultValue=null] - 재시도 실패 시 반환할 기본 값.
 * @returns {Promise<*>} 함수 실행 결과 또는 기본 값.
 */
async function retry(fn, retries = 4, delay = 2000, defaultValue = null) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (error) {
            console.log(`재시도 중... (${i + 1}/${retries})`);
            await new Promise(res => setTimeout(res, delay));
        }
    }
    console.log('최대 재시도 횟수 도달, 기본 값 반환.');
    return defaultValue;
}

/**
 * 주어진 상품에 대한 상세 정보를 추출합니다.
 * @param {Object} productDetail - 상품 상세 정보 객체.
 * @param {string} url - 기본 URL.
 * @returns {Promise<Array>} 리뷰 정보 배열.
 */
async function fetchProductDetails(productDetail, url) {
    const browser = await launchBrowser();
    const page = await browser.newPage();

    console.log("상품 상세화면 URL* : ", productDetail["상품 상세화면 URL*"]);
    try {
        await page.goto(productDetail["상품 상세화면 URL*"], { waitUntil: 'domcontentloaded', timeout: 60000 });
    } catch (error) {
        console.error('상품 상세 페이지로 이동 중 오류 발생:', error);
    }

    //await new Promise(resolve => setTimeout(resolve, 3000)); // 5초 대기

    const productDetailHtml = await retry(async () => {
        return await page.evaluate(() => {
            const detailElement = document.querySelector('#prdDetail');
            return detailElement ? detailElement.outerHTML : '';
        });
    }, 3, 2000, '');
    productDetail["상품 상세(html)*"] = productDetailHtml;

    const productImages = await retry(async () => {
        return await page.evaluate(() => {
            const imgElements = document.querySelectorAll('.xans-element-.xans-product.xans-product-image img');
            const imgUrls = [];
            imgElements.forEach(img => {
                const src = img.getAttribute('src');
                if (src) {
                    imgUrls.push(`http:${src}`);
                }
            });
            return imgUrls;
        });
    }, 3, 2000, []);
    productDetail["상품 이미지*"] = JSON.stringify(productImages, null, 2);
    console.log("상품 이미지* : ", JSON.stringify(productImages, null, 2));

    const options = await retry(async () => {
        return await page.evaluate(() => {
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
                        options.set(optionTitle, [...new Set([...options.get(optionTitle), ...optionValues])]);
                    } else {
                        options.set(optionTitle, optionValues);
                    }
                }
            });
            return Array.from(options.entries()).map(([key, value]) => ({ [key]: value }));
        });
    }, 3, 2000, []);
    productDetail["옵션 정보"] = JSON.stringify(options, null, 2);
    console.log("옵션 정보 : ", JSON.stringify(options, null, 2));

    const productNotice = await retry(async () => {
        return await page.evaluate(() => {
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
    }, 1, 2000, {});
    productDetail["상품 고지 정보"] = productNotice;
    console.log("상품 고지 정보 : ", JSON.stringify(productNotice, null, 2));

    const optionTitles = options.map(option => Object.keys(option)[0]);
    productDetail["옵션"] = JSON.stringify(optionTitles, null, 2);
    console.log("옵션 : ", JSON.stringify(optionTitles, null, 2));

    const reviews = await fetchProductReviews(page, productDetail, url);

    await browser.close();

    return reviews;
}

/**
 * 주어진 상품에 대한 리뷰 정보를 추출합니다.
 * @param {Page} page - Puppeteer 페이지 인스턴스.
 * @param {Object} productDetail - 상품 상세 정보 객체.
 * @param {string} url - 기본 URL.
 * @returns {Promise<Array>} 리뷰 정보 배열.
 */
async function fetchProductReviews(page, productDetail, url) {
    const reviews = [];

    /* https://cherryme.kr */
    const reviewTableElement = await retry(async () => {
        return await page.$('#prdReview tbody.center.review_content');
    }, 3, 2000, null);
    if (reviewTableElement) {
        // 리뷰 테이블이 존재하는 경우
        const reviewRows = await reviewTableElement.$$('tr');
        for (const reviewRow of reviewRows) {
            const reviewData = await reviewRow.evaluate(row => {
                const getReviewText = (selector) => {
                    const element = row.querySelector(selector);
                    return element ? element.innerText.trim() : '';
                };

                const getReviewImage = (selector) => {
                    const element = row.querySelector(selector);
                    return element ? element.src : '';
                };

                const getReviewAlt = (selector) => {
                    const element = row.querySelector(selector);
                    return element ? element.alt.trim() : '';
                };

                const authorAndDateText = getReviewText('.rImg > span');
                const [author, date] = authorAndDateText.split(/\s+/); // 공백으로 분리하여 author와 date를 추출
                const image = getReviewImage('.review_img img');
                const score = getReviewAlt('.rPoint img').replace('점', ''); // alt 값을 가져와서 "점"을 제거
                let reviewText = getReviewText('.rContent');

                // "신고하기" 문구와 연속된 공백 제거
                reviewText = reviewText.replace(/[\r\n]+신고하기$/, '').trim();

                return {
                    author,
                    date,
                    image,
                    score,
                    reviewText
                };
            });

            reviews.push({
                "이미지": reviewData.image,
                "평점": reviewData.score,
                "리뷰": reviewData.reviewText,
                "작성날짜": reviewData.date,
                "작성자": reviewData.author,
                "상품ID": productDetail["상품ID"],
                // "상품명*": productDetail["상품명*"],
                // "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
            });
        }
    }
    else
    {
        /* https://dailyjou.com */
        // 리뷰 테이블이 존재하지 않는 경우, iframe 확인
        const iframeElement = await retry(async () => {
            return await page.$('#prdReview iframe#review_widget3_0');
        }, 3, 2000, null);

        if (iframeElement) {
            const frame = await iframeElement.contentFrame();
            if (frame) {
                await new Promise(resolve => setTimeout(resolve, 5000)); // iframe 내에서 5초 대기
                const reviewElements = await retry(async () => {
                    return await frame.$$('.sf_review_user_info.blindTextArea.review_wrapper_info.set_report');
                }, 3, 2000, []);
                for (const reviewElement of reviewElements) {
                    const imageElement = await reviewElement.$('.sf_review_user_photo img');
                    const image = imageElement ? await frame.evaluate(img => img.src, imageElement) : '';

                    const scoreElement = await reviewElement.$('.sf_review_user_score');
                    const score = scoreElement ? await frame.evaluate(el => el.innerText.trim(), scoreElement) : '';

                    const reviewTextElement = await reviewElement.$('.sf_text_overflow.value');
                    let reviewText = reviewTextElement ? await frame.evaluate(el => el.innerText.trim(), reviewTextElement) : '';

                    // "신고하기" 문구와 연속된 공백 제거
                    reviewText = reviewText.replace(/[\r\n]+신고하기$/, '').trim();

                    const dateElement = (await reviewElement.$$('.sf_review_user_write_date span'))[1];
                    const date = dateElement ? await frame.evaluate(el => el.innerText.trim(), dateElement) : '';

                    const authorElement = (await reviewElement.$$('.sf_review_user_writer_name span'))[1];
                    const author = authorElement ? await frame.evaluate(el => el.innerText.trim(), authorElement) : '';

                    reviews.push({
                        "상품ID": productDetail["상품ID"],
                        "상품명*": productDetail["상품명*"],
                        "이미지": image,
                        "평점": score,
                        "리뷰": reviewText,
                        "작성날짜": date,
                        "작성자": author,
                        "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
                    });
                }
            }
        }
    }

    console.log("reviews : ", JSON.stringify(reviews, null, 2));

    return reviews;
}


/**
 * 현재 시간을 포맷된 문자열로 반환합니다.
 * @returns {string} 포맷된 현재 시간 문자열.
 */
function getCurrentFormattedTime() {
    return moment().format('YYYY.MM.DD HH:mm:ss');
}

/**
 * 메인 함수입니다. 쇼핑몰 URL을 받아서 정보를 추출하고 Excel 파일로 저장합니다.
 * @param {string} url - 쇼핑몰 URL.
 */
async function main(url) {
    /* 시작 시간 세팅 */
    let startTime = getCurrentFormattedTime();
    console.log('Script start time:', startTime);
    startTime = moment();


    /* url 세팅*/
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    /* puppeteer 초기화 */
    const browser = await launchBrowser();
    const page = await browser.newPage();
    try {
        /* 네트워크 연결이 2개 이하로 줄어들 때까지 대기 */
        await page.goto(url, { waitUntil: 'domcontentloaded' });
    } catch (error) {
        console.error('메인 페이지로 이동 중 오류 발생:', error);
    }

    const metaTags = await extractMetaTags(page);
    const footerInfo = await extractFooterInfo(page);
    const bannerInfo = await extractBannerInfo(page, url);
    await browser.close();

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

    console.log('shopInfo : ', JSON.stringify(shopInfo, null, 2));

    const productDetails = [];
    const productRepls = [];

    await logCategoryInfo(url, categoryInfo, productDetails, productRepls);

    writeToExcel(shopInfo, bannerInfo, productDetails, productRepls);

    const endTime = getCurrentFormattedTime();
    console.log('Script end time:', endTime);

    const totalTime = moment.duration(moment().diff(startTime));
    console.log('Total execution time:', `${totalTime.hours()}시간 ${totalTime.minutes()}분 ${totalTime.seconds()}초`);
}

const url = 'cherryme.kr';
main(url);
