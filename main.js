const axios = require('axios');
const cheerio = require('cheerio');
const xlsx = require('xlsx');
const puppeteer = require('puppeteer');

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

async function fetchHtml(url) {
    try {
        const { data } = await axios.get(url);
        return data;
    } catch (error) {
        console.error('Error fetching HTML:', error);
        return null;
    }
}

async function extractMetaTags($) {
    const ogSiteName = $('meta[property="og:site_name"]').attr('content');
    const ogUrl = $('meta[property="og:url"]').attr('content');
    const uidScript = $('script[src*="cfa.html"]').attr('src');
    const favicon = $('link[rel="shortcut icon"]').attr('href');
    const bodyStyle = $('body').css('background');

    const representativeImageElement = $(`a img[src*="logo"], a img[alt*="로고"], a img[alt*="${ogSiteName ? ogSiteName : ''}"], a img[alt="logo"]`);
    const representativeImage = representativeImageElement.attr('src');

    return {
        siteName: ogSiteName || null,
        siteUrl: ogUrl || null,
        uid: uidScript ? new URLSearchParams(new URL(uidScript).search).get('uid') : null,
        favicon: favicon || null,
        themeColor: bodyStyle || '',
        representativeImage: representativeImage || null
    };
}

async function extractFooterInfo($, baseUrl) {
    const footer = $('.xans-element-.xans-layout.xans-layout-footer');
    if (!footer.length) return null;

    const extractText = (selector) => {
        const element = footer.find(selector);
        return element.length ? element.text().replace(/.*:/, '').trim() : null;
    };

    const extractTextByLabel = (label) => {
        const elements = footer.find('span, li').toArray();
        const element = elements.find(el => $(el).text().includes(label));
        return element ? $(element).text().replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;
    };

    const companyName = extractText('.address li:first-child') ||
        extractTextByLabel('Company:');
    const ceo = extractText('.address li:nth-child(2)') ||
        extractTextByLabel('Ceo:');
    const businessLicense = extractText('.address li:nth-child(3)') ||
        extractTextByLabel('Company Reg.No:');
    const onlineBusinessLicenseElement = footer.find('span, li').toArray().find(el => $(el).text().includes('통신판매업신고'));
    const onlineBusinessLicense = onlineBusinessLicenseElement ? $(onlineBusinessLicenseElement).text().replace(/.*:/, '').replace(/\[.*\]/, '').trim() : null;
    const customerServicePhoneElement = footer.find('span, li').toArray().find(el => $(el).text().includes('tel:'));
    const customerServicePhone = customerServicePhoneElement ? $(customerServicePhoneElement).text().split('E-mail:')[0].replace('tel:', '').trim() : null;

    return {
        companyName,
        ceo,
        businessLicense,
        onlineBusinessLicense,
        customerServicePhone
    };
}

async function extractBannerInfo($, baseUrl) {
    const banners = [];
    const topBanners = $('#topbanner, [app4you-smart-banner]');

    topBanners.each((_, banner) => {
        const img = $(banner).find('img');
        const aTag = $(banner).find('a');

        if (img.length && aTag.length) {
            const imgUrl = img.attr('src').startsWith('http') ? img.attr('src') : new URL(img.attr('src'), baseUrl).href;
            const linkUrl = aTag.attr('href').startsWith('http') ? aTag.attr('href') : new URL(aTag.attr('href'), baseUrl).href;
            banners.push({ '배너이미지 URL': imgUrl, '배너 링크': linkUrl });
        }
    });

    return banners.length > 0 ? banners : [{ '배너이미지 URL': '', '배너 링크': '' }];
}

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

async function fetchCategoryData(url) {
    try {
        const response = await axios.get(url + '/exec/front/Product/SubCategory');
        return response.data;
    } catch (error) {
        console.error('Error fetching category data:', error);
        return [];
    }
}

function writeToExcel(shopInfo, bannerInfo, productDetails, productRepls) {
    const workbook = xlsx.utils.book_new();

    const shopSheet = xlsx.utils.json_to_sheet([shopInfo]);
    xlsx.utils.book_append_sheet(workbook, shopSheet, '쇼핑몰 정보');

    const bannerSheet = xlsx.utils.json_to_sheet(bannerInfo);
    xlsx.utils.book_append_sheet(workbook, bannerSheet, '메인배너');

    const productSheet = xlsx.utils.json_to_sheet(productDetails);
    xlsx.utils.book_append_sheet(workbook, productSheet, '상품정보');

    const replSheet = xlsx.utils.json_to_sheet(productRepls);
    xlsx.utils.book_append_sheet(workbook, replSheet, '리뷰정보');

    xlsx.writeFile(workbook, 'shop_info.xlsx');
}

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

                const nowTime1 = getCurrentFormattedTime();
                console.log('Script now1 time:', nowTime1);

                const delay = Math.floor(Math.random() * (5000 - 2000 + 1)) + 2000;
                await new Promise(resolve => setTimeout(resolve, delay));

                const nowTime2 = getCurrentFormattedTime();
                console.log('Script now2 time:', nowTime2);

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

                        const reviews = await fetchProductDetails(productDetail, url);

                        productDetails.push(productDetail);

                        productRepls.push(...reviews);
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

async function retry(fn, retries = 4, delay = 2000, defaultValue = null) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (error) {
            console.log(`Retrying... (${i + 1}/${retries})`);
            await new Promise(res => setTimeout(res, delay));
        }
    }
    console.log('Max retries reached, returning default value.');
    return defaultValue;
}

async function fetchProductDetails(productDetail, url) {
    const browser = await launchBrowser();

    const page = await browser.newPage();

    console.log("상품 상세화면 URL* : ", productDetail["상품 상세화면 URL*"]);
    await page.goto(productDetail["상품 상세화면 URL*"], { waitUntil: 'networkidle2', timeout: 60000 });

    await page.waitForSelector('#prdDetail', { timeout: 30000 });

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
    productDetail["상품 이미지*"] = productImages;
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
    productDetail["옵션 정보"] = options;
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
    }, 3, 2000, {});
    productDetail["상품 고지 정보"] = productNotice;
    console.log("상품 고지 정보 : ", JSON.stringify(productNotice, null, 2));

    const optionTitles = options.map(option => Object.keys(option)[0]);
    productDetail["옵션"] = optionTitles;
    console.log("옵션 : ", JSON.stringify(optionTitles, null, 2));

    const reviews = await fetchProductReviews(page, productDetail, url);

    await browser.close();

    return reviews;
}

async function fetchProductReviews(page, productDetail, url) {
    const reviews = [];

    await new Promise(res => setTimeout(res, 2000));

    const iframeElement = await retry(async () => {
        return await page.$('#prdReview iframe#review_widget3_0');
    }, 3, 2000, null);

    if (iframeElement) {
        const frame = await iframeElement.contentFrame();
        if (frame) {
            await frame.waitForSelector('.sf_review_user_info.blindTextArea.review_wrapper_info.set_report', { timeout: 10000 });
            const reviewElements = await retry(async () => {
                return await frame.$$('.sf_review_user_info.blindTextArea.review_wrapper_info.set_report');
            }, 3, 2000, []);
            for (const reviewElement of reviewElements) {
                const imageElement = await reviewElement.$('.sf_review_user_photo img');
                const image = imageElement ? await frame.evaluate(img => img.src, imageElement) : '';

                const scoreElement = await reviewElement.$('.sf_review_user_score');
                const score = scoreElement ? await frame.evaluate(el => el.innerText.trim(), scoreElement) : '';

                const reviewTextElement = await reviewElement.$('.sf_text_overflow.value');
                const reviewText = reviewTextElement ? await frame.evaluate(el => el.innerText.trim(), reviewTextElement) : '';

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

    console.log("reviews : ", JSON.stringify(reviews, null, 2));

    return reviews;
}

function getCurrentFormattedTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `${year}.${month}.${day} ${hours}:${minutes}:${seconds}`;
}

async function main(url) {
    const startTime = getCurrentFormattedTime();
    console.log('Script start time:', startTime);

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    const html = await fetchHtml(url);
    if (!html) return;

    const $ = cheerio.load(html);

    const metaTags = await extractMetaTags($);
    const footerInfo = await extractFooterInfo($, url);
    const bannerInfo = await extractBannerInfo($, url);

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

    console.log('shopInfo : ', shopInfo);

    const productDetails = [];
    const productRepls = [];

    await logCategoryInfo(url, categoryInfo, productDetails, productRepls);

    writeToExcel(shopInfo, bannerInfo, productDetails, productRepls);

    const endTime = getCurrentFormattedTime();
    console.log('Script end time:', endTime);
    console.log('Total execution time:', (new Date() - new Date(startTime.replace(/\./g, '-').replace(/ /, 'T'))) / 1000, 'seconds');
}

const url = 'dailyjou.com';
main(url);
