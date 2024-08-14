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
        headless: false,
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
                return element ? element.getAttribute('content') : '';
            };

            const getLinkHref = (rel) => {
                const element = document.querySelector(`link[rel="${rel}"]`);
                return element ? element.getAttribute('href') : '';
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
                return '';
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
                siteName: ogSiteName || '',
                siteUrl: ogUrl || '',
                favicon: favicon || '',
                themeColor: themeColor || '',
                representativeImage: representativeImage || ''
            };
        });

        // 여러 위치에서 UID 추출 시도
        const uid = await page.evaluate(() => {
            const scriptElement = Array.from(document.querySelectorAll('script[src*="//cfa-js.cafe24.com/cfa.html?uid="]'))
                .map(script => script.src.match(/uid=([^&]*)/))
                .filter(match => match && match[1])
                .find(match => match)?.[1];

            if (scriptElement) return scriptElement;

            const metaUid = document.querySelector('meta[name="uid"]');
            if (metaUid) return metaUid.getAttribute('content');

            return '';
        });

        return { ...metaTags, uid: uid || '' }; // UID가 없으면 빈 문자열 반환
    } catch (error) {
        console.error('메타 태그 추출 중 오류 발생:', error);
        return {
            siteName: '',
            siteUrl: '',
            favicon: '',
            themeColor: '',
            representativeImage: '',
            uid: ''
        };
    }
}

/**
 * 주어진 Puppeteer 페이지에서 푸터 정보를 추출합니다.
 * @param {Page} page - Puppeteer 페이지 인스턴스.
 * @returns {Promise<Object>} 추출된 푸터 정보를 포함하는 객체.
 */
async function extractFooterInfo(page) {
    try {
        console.log('extractFooterInfo 함수 시작');
        return await page.evaluate(() => {
            const footer = document.querySelector('.xans-element-.xans-layout.xans-layout-footer');

            if (!footer) {
                return { debug: '푸터 요소를 찾을 수 없음' };
            }

            const texts = footer.textContent.replace(/\s+/g, ' ').trim();

            // 데이터 추출을 위한 패턴과 함수
            const extractData = (patterns, text, removeSuffix = '') => {
                for (const pattern of patterns) {
                    const match = text.match(pattern);
                    if (match) {
                        return removeSuffix ? match[1].replace(removeSuffix, '').trim() : match[1].trim();
                    }
                }
                return null;
            };

            // 패턴 설정
            const companyNamePatterns = [
                /COMPANY\.\s*(.*?)\s*PRESIDENT/,                            // https://example.com
                /company\s*\.\s*(.*?)\s*ceo\s*&\s*cpo\s*\./,                // https://ba-on.com
                /^(.*?)대표\s*:/,                                            // https://dailyjou.com, https://ba-on.com
                /Company:\s*(.*?)\s*Ceo:/                                   // https://cherryme.kr
            ];
            const ceoPatterns = [
                /PRESIDENT\s*(.*?)\s*E-MAIL/,                               // https://example.com
                /ceo\s*&\s*cpo\s*\.\s*(.*?)\s*business\s*license\s*\./,     // https://ba-on.com
                /대표\s*:\s*(.*?)\s*(?:고객센터|사업자등록번호)/,              // https://dailyjou.com, https://beidelli.com
                /Ceo:\s*(.*?)\s*Personal info manager/                       // https://cherryme.kr
            ];
            const phonePatterns = [
                /TEL\.\s*([^\s]+)/,                                         // https://example.com
                /tel\s*\.\s*([^\s]+)/,                                      // https://ba-on.com
                /고객센터\s*:\s*([^\s]+)/,                                    // https://dailyjou.com, https://beidelli.com
                /tel:\s*([^\s]+)/                                            // https://cherryme.kr
            ];
            const businessLicensePatterns = [
                /BUSINESS NUM\.\s*([^\s]+)/,                                // https://example.com
                /business\s*license\s*\.\s*([^\s]+)/,                       // https://ba-on.com
                /사업자등록번호\s*:\s*([^\s]+)/,                               // https://dailyjou.com, https://beidelli.com
                /Company Reg\.No:\s*([^\s]+)/                               // https://cherryme.kr
            ];
            const onlineBusinessLicensePatterns = [
                /MAIL-ORDER LICENSE\.\s*([^\s]+)/,                           // https://example.com
                /online\s*business\s*license\s*\.\s*([^\s]+)/,               // https://ba-on.com
                /통신판매업신고번호\s*:\s*제\s*([^ ]+)/,                       // https://beidelli.com
                /통신판매업신고\s*:\s*(.*?)\s*\[/,                              // https://dailyjou.com
                /Network Reg\.No:\s*([^\s]+)/                                // https://cherryme.kr
            ];

            // 패턴을 사용하여 데이터 추출
            const companyName = extractData(companyNamePatterns, texts);
            const ceo = extractData(ceoPatterns, texts);
            let customerServicePhone = extractData(phonePatterns, texts);
            let businessLicense = extractData(businessLicensePatterns, texts);
            const onlineBusinessLicense = extractData(onlineBusinessLicensePatterns, texts, '호');

            // 불필요한 부분 제거
            if (businessLicense) {
                businessLicense = businessLicense.replace(/\[.*?\]/g, '').trim();
            }
            if (customerServicePhone) {
                customerServicePhone = customerServicePhone.split('E-MAIL:')[0].trim();
            }

            return {
                companyName: companyName || '',
                ceo: ceo || '',
                customerServicePhone: customerServicePhone || '',
                businessLicense: businessLicense || '',
                onlineBusinessLicense: onlineBusinessLicense || '',
                debug: '데이터 추출 성공'
            };
        });
    } catch (error) {
        console.error('푸터 정보 추출 중 오류 발생:', error);
        return { debug: '푸터 정보 추출 중 오류 발생' };
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

            const processBanner = (img, aTag) => {
                const imgUrl = img ? (img.getAttribute('src').startsWith('http') ? img.getAttribute('src') : new URL(img.getAttribute('src'), baseUrl).href) : '';
                const linkUrl = aTag ? (aTag.getAttribute('href').startsWith('http') ? aTag.getAttribute('href') : new URL(aTag.getAttribute('href'), baseUrl).href) : '';
                const bannerName = aTag ? aTag.textContent.trim() : 'Unnamed Banner';
                banners.push({ '배너이미지 URL': imgUrl, '배너 링크': linkUrl, '배너 이름': bannerName });
            };

            // 이미지 배너 처리
            // https://ba-on.com
            const topBanners = document.querySelectorAll('#topbanner, [app4you-smart-banner]');
            topBanners.forEach(banner => {
                const img = banner.querySelector('img');
                const aTag = banner.querySelector('a');
                if (aTag) {
                    processBanner(img, aTag);
                }
            });

            // 슬라이더 배너 처리
            // https://beidelli.com
            const sliderBanners = document.querySelectorAll('#topbanner[data-slider="true"] ul li a');
            sliderBanners.forEach(sliderBanner => {
                processBanner(null, sliderBanner);
            });

            return banners.length > 0 ? banners : [{ '배너이미지 URL': '', '배너 링크': '', '배너 이름': '' }];
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
async function fetchCategoryData(url, page) {
    try {
        // 페이지 로드
        await page.goto(url, { waitUntil: 'domcontentloaded' });

        // 부모 카테고리 데이터 추출
        const categoryData = await page.evaluate(async () => {
            const categories = [];

            // .xans-element-.xans-layout.xans-layout-category 요소를 배열로 받음
            const categoryWrappers = document.querySelectorAll('.xans-element-.xans-layout.xans-layout-category');

            if (categoryWrappers.length > 0) {
                // 첫 번째 요소 안의 class="xans-record-"인 li들을 선택
                const categoryElements = Array.from(categoryWrappers[0].querySelectorAll('li'))
                    .filter(li => {
                        const style = li.getAttribute('style');
                        const hasDisplayNone = style && style.includes('display:none');
                        const hasContent = li.innerText.trim().length > 0;
                        return !hasDisplayNone && hasContent;
                    });

                for (const categoryElement of categoryElements) {
                    // li 바로 아래 있는 a 태그 href 추출
                    const mainLink = categoryElement.querySelector(':scope > a'); // :scope를 사용하여 li 바로 아래의 a 태그를 선택
                    if (mainLink && mainLink.href) {
                        const mainHref = mainLink.href;

                        // href에서 cate_no 값을 추출하는 로직
                        let parentCateNo;
                        const cateNoMatch = mainHref.match(/cate_no=(\d+)/);
                        if (cateNoMatch) {
                            parentCateNo = parseInt(cateNoMatch[1], 10); // cate_no 값을 추출하여 정수로 변환
                        } else {
                            parentCateNo = parseInt(mainHref.split('/').slice(-2, -1)[0], 10) || 1; // 기존 방식 사용
                        }

                        // 부모 카테고리도 categories에 추가
                        categories.push({
                            link_product_list: mainHref,
                            name: mainLink.innerText.trim(),
                            param: `?cate_no=${parentCateNo}`,
                            cate_no: parentCateNo,
                            parent_cate_no: 1, // 부모 카테고리는 최상위이므로 parent_cate_no는 1 설정
                            design_page_url: "product/list.html",
                            data_list: [] // 서브 카테고리를 저장할 배열
                        });
                    }
                }
            }

            return categories;
        });

        const addCategory = []

        // 각 부모 카테고리의 서브 카테고리 추출
        for (const category of categoryData) {
            const categoryUrl = `${url}/${category.design_page_url}${category.param}`;
            await page.goto(categoryUrl, { waitUntil: 'domcontentloaded' });

            // 서브 카테고리 데이터 추출
            const subCategories = await page.evaluate(async (parentCateNo) => {
                // 서브 카테고리가 로드될 때까지 대기
                await new Promise(resolve => setTimeout(resolve, 1000)); // 2초 대기, 상황에 따라 조정 가능

                const subCategoryLinks = [];
                // menuCategory 안에 xans-element- xans-product xans-product-displaycategory xans-record- 클래스를 가진 요소를 찾기
                const productElements = Array.from(document.querySelectorAll('.menuCategory .xans-element-.xans-product.xans-product-displaycategory.xans-record-'));

                productElements.forEach(async (productElement) => {
                    // li 바로 아래 있는 a 태그 선택
                    const subLink = productElement.querySelector(':scope > a'); // :scope를 사용하여 li 바로 아래의 a 태그를 선택
                    if (subLink) {
                        const name = subLink.innerText.trim();
                        const linkProductList = subLink.href;

                        // 서브 카테고리 번호 추출
                        let cateNo;
                        const subCateNoMatch = linkProductList.match(/cate_no=(\d+)/);
                        if (subCateNoMatch) {
                            cateNo = parseInt(subCateNoMatch[1], 10); // cate_no 값을 추출하여 정수로 변환
                        } else {
                            cateNo = parseInt(linkProductList.split('/').slice(-2, -1)[0], 10); // 기존 방식 사용
                        }

                        // 서브 카테고리 추가
                        subCategoryLinks.push({
                            link_product_list: linkProductList,
                            name,
                            param: `?cate_no=${cateNo}`,
                            cate_no: cateNo,
                            parent_cate_no: parentCateNo,
                            design_page_url: "product/list.html"
                        });

                        // await new Promise(resolve => setTimeout(resolve, 500)); // 1초 대기, 상황에 따라 조정 가능

                        // 마우스 오버 이벤트 발생
                        // subLink.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));

                        // 마우스 오버 후에 동료 요소 중 class="xans-element- xans-product xans-product-children"인 요소가 생길 때까지 대기
                        // await new Promise(resolve => setTimeout(resolve, 500)); // 1초 대기, 상황에 따라 조정 가능

                        // 서브 서브 카테고리 처리
                        const subSubCategoryElements = productElement.querySelectorAll('.xans-element-.xans-product.xans-product-children .xans-record- a');
                        const subSubCategoryLinks = [];

                        subSubCategoryElements.forEach(subSubLink => {
                            const subSubName = subSubLink.innerText.trim();
                            const subSubLinkProductList = subSubLink.href;

                            // 서브 서브 카테고리 번호 추출
                            let subSubCateNo;
                            const subSubCateNoMatch = subSubLinkProductList.match(/cate_no=(\d+)/);
                            if (subSubCateNoMatch) {
                                subSubCateNo = parseInt(subSubCateNoMatch[1], 10); // cate_no 값을 추출하여 정수로 변환
                            } else {
                                subSubCateNo = parseInt(subSubLinkProductList.split('/').slice(-2, -1)[0], 10); // 기존 방식 사용
                            }

                            subSubCategoryLinks.push({
                                link_product_list: subSubLinkProductList,
                                name: subSubName,
                                param: `?cate_no=${subSubCateNo}`,
                                cate_no: subSubCateNo,
                                parent_cate_no: cateNo, // 상위 카테고리 번호를 parent_cate_no로 설정
                                design_page_url: "product/list.html"
                            });
                        });

                        // subCategoryLinks에 서브 서브 카테고리 추가
                        subCategoryLinks.push(...subSubCategoryLinks);
                    }
                });

                return subCategoryLinks;
            }, category.cate_no); // category.cate_no를 parentCateNo로 넘김

            // 부모 카테고리의 data_list에 서브 카테고리 추가
            addCategory.push(...subCategories);
        }

        categoryData.push(...addCategory);

        return categoryData;
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

// HTML 태그 제거 함수
function stripHTML(html) {
    return html.replace(/<\/?[^>]+(>|$)/g, "");
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
                                "상품명*": stripHTML(product.product_name_tag),
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

                            console.log("productDetail : ", JSON.stringify(productDetail, null, 2));

                            const reviews = await fetchProductDetails(productDetail, url);
                            productDetails.push(productDetail);
                            productRepls.push(...reviews);
                            //test 시작
                            // break;
                            //test 끝
                        }
                        pageNum++;
                        //test 시작
                        // hasMoreData = false;
                        //test 끝
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
        await page.goto(productDetail["상품 상세화면 URL*"], { waitUntil: 'networkidle2', timeout: 30000 });
    } catch (error) {
        console.error('상품 상세 페이지로 이동 중 오류 발생:', error);
    }

    await new Promise(resolve => setTimeout(resolve, 3000)); // 5초 대기

    const productDetailHtml = await retry(async () => {
        return await page.evaluate((url) => {
            // prdDetail 요소 가져오기
            const detailElement = document.querySelector('#prdDetail');
            if (detailElement) {

                // <div class="cont"> 요소에 style 속성 추가하여 가운데 정렬
                const contElements = detailElement.querySelectorAll('div.cont');
                contElements.forEach(cont => {
                    cont.style.textAlign = 'center';
                });

                // img 태그의 src 속성을 ec-data-src로 교체
                const imgElementsWithEcDataSrc = detailElement.querySelectorAll('img[ec-data-src]');
                imgElementsWithEcDataSrc.forEach(img => {

                    const ecDataSrc = img.getAttribute('ec-data-src');

                    // https://dailyjou.com
                    if (ecDataSrc.startsWith('//')) {
                        img.src = "https:" + ecDataSrc;

                    // https://ba-on.com
                    } else if (ecDataSrc.startsWith('/')) {
                        img.src = url + ecDataSrc;

                    // https://beidelli.com
                    } else if (ecDataSrc.startsWith('https')) {
                        img.src = ecDataSrc;
                    }

                });


                // ec-data-src 속성이 없는 img 태그의 src가 '/'로 시작하면 url 추가

                // https://cherryme.kr
                // https://www.hotping.co.kr
                const allImgElements = detailElement.querySelectorAll('img:not([ec-data-src])');
                allImgElements.forEach(img => {

                    const dataSrc = img.getAttribute('src');

                    if (dataSrc.startsWith('//')) {
                        img.src = "https:" + dataSrc;

                    } else if (dataSrc.startsWith('/')) {
                        img.src = url + dataSrc;

                    } else if (dataSrc.startsWith('https')) {
                        img.src = dataSrc;
                    }

                });

                // ul 태그와 그 안의 모든 태그 삭제
                const ulElements = detailElement.querySelectorAll('ul');
                ulElements.forEach(ul => ul.remove());

                // a 태그의 href 속성이 '/'로 시작하면 url 추가
                const allAnchorElements = detailElement.querySelectorAll('a[href^="/"]');
                allAnchorElements.forEach(anchor => {
                    anchor.href = url + anchor.getAttribute('href');
                });
            }

            const detailHtml = detailElement ? detailElement.outerHTML : '';

            // 새로운 div 생성 및 prdDetail 내용 포함
            const combinedHtml = `<div>${detailHtml}</div>`;
            return combinedHtml;
        }, url);
    }, 3, 2000, "");

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
    console.log("상품 이미지* : ", productImages);

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

    // https://cherryme.kr
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

                const getReviewImages = (selector) => {
                    const elements = row.querySelectorAll(selector);
                    return elements ? Array.from(elements).map(element => element.src) : [];
                };

                const getReviewAlt = (selector) => {
                    const element = row.querySelector(selector);
                    return element ? element.alt.trim() : '';
                };

                const authorAndDateText = getReviewText('.rImg > span');
                const [author, date] = authorAndDateText.split(/\s+/); // 공백으로 분리하여 author와 date를 추출
                const images = getReviewImages('.review_img img');
                const score = getReviewAlt('.rPoint img').replace('점', ''); // alt 값을 가져와서 "점"을 제거
                let reviewText = getReviewText('.rContent');

                // "신고하기" 문구와 연속된 공백 제거
                reviewText = reviewText.replace(/[\r\n]+신고하기$/, '').trim();

                return {
                    author,
                    date,
                    images,
                    score,
                    reviewText
                };
            });

            reviews.push({
                "상품ID": productDetail["상품ID"],
                "상품명*": productDetail["상품명*"],
                "이미지": reviewData.images,
                "평점": reviewData.score,
                "리뷰": reviewData.reviewText,
                "작성날짜": reviewData.date,
                "작성자": reviewData.author,
                "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
            });
        }
        console.log("reviews : ", JSON.stringify(reviews, null, 2));
        return reviews;
    }

    // https://dailyjou.com
    // https://www.ba-on.com
    // 리뷰 테이블이 존재하지 않는 경우, iframe 확인
    const iframeElement1 = await retry(async () => {
        return await page.$('#prdReview iframe#review_widget3_0');
    }, 3, 2000, null);
    if (iframeElement1) {
        const frame = await iframeElement1.contentFrame();
        if (frame) {
            await new Promise(resolve => setTimeout(resolve, 3000)); // iframe 내에서 5초 대기
            const reviewElements = await retry(async () => {
                return await frame.$$('.sf_review_user_info.blindTextArea.review_wrapper_info.set_report');
            }, 3, 2000, []);
            for (const reviewElement of reviewElements) {
                const imageElement = await reviewElement.$('.sf_review_user_photo img');
                const image = imageElement ? await frame.evaluate(img => img.src, imageElement) : '';

                const imageElements = await reviewElement.$$('.sf_review_user_photo img');
                const images = imageElements.length > 0 ? await frame.evaluate(imgs => imgs.map(img => img.src), imageElements) : [];

                const scoreElement = await reviewElement.$('.sf_review_user_score');
                let score = '';
                if (scoreElement) {
                    const fullScoreText = await frame.evaluate(el => el.innerText.trim(), scoreElement);
                    score = fullScoreText.replace(/[^★]/g, ''); // "★" 외의 모든 문자 제거
                }

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
                    "이미지": JSON.stringify(images, null, 2),
                    "평점": score,
                    "리뷰": reviewText,
                    "작성날짜": date,
                    "작성자": author,
                    "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
                });
            }
        }
        console.log("reviews : ", JSON.stringify(reviews, null, 2));
        return reviews;
    }


    // https://beidelli.com/
    console.log('beidelli type');
    const prdReviewBeidelli = await page.evaluate(() => {
        const prdReviewEl = document.querySelector('#prdReview .alpha_widget');
        return {
            code: prdReviewEl?.getAttribute('data-code'),
            value: prdReviewEl?.getAttribute('data-value')
        };
    });
    console.log('prdReviewBeidelli.code ', prdReviewBeidelli.code);
    console.log('prdReviewBeidelli.value ', prdReviewBeidelli.value);
    if (prdReviewBeidelli.code && prdReviewBeidelli.value) {
        const url = `https://saladlab.shop/api/widget?code=${prdReviewBeidelli.code}&value=${prdReviewBeidelli.value}&idx=3`;
        console.log('url ', url);
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

        const reviewEls = await page.$$('.widget_boardAlphareview .widget_w .widget_item.review[data-widgettype="board_Alphareview"]');

        for (const reviewEl of reviewEls) {
            const author = await getElementTextContent(page, reviewEl, '.widget_item_none_username_2');
            const date = await getElementTextContent(page, reviewEl, '.widget_item_date_product_none');
            const score = '★'.repeat((await reviewEl.$$('.alph_star_full')).length);
            const reviewText = await getElementTextContent(page, reviewEl, '.widget_item_review_box');
            const images = await getImageSrcs(page, reviewEl, 'img.widget_item_photo.widget_item_photo_s.lozad');

            reviews.push({
                "상품ID": productDetail["상품ID"],
                "상품명*": productDetail["상품명*"],
                "이미지": JSON.stringify(images, null, 2),
                "평점": score,
                "리뷰": reviewText,
                "작성날짜": date,
                "작성자": author,
                "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
            });
        }

        console.log('reviews :', reviews);
        return reviews;

    } else {
        console.log('Code or value not found');
    }


    //https://www.hotping.co.kr
    console.log('hotping type ');
    const prdReviewHotping = await page.evaluate(() => {
        const prdReviewEl = document.querySelector('#prdReview .crema-product-reviews.crema-applied:not(.crema-hide)');
        return {
            code: prdReviewEl?.getAttribute('data-product-code'),
            id: prdReviewEl?.getAttribute('data-widget-id')
        };
    });
    console.log('prdReviewHotping.code ', prdReviewHotping.code);
    console.log('prdReviewHotping.id ', prdReviewHotping.id);
    if (prdReviewHotping.code && prdReviewHotping.id) {
        // 프로토콜 제거
        let mainUrl = url.replace(/^https?:\/\//, '').replace(/^www\./, '');

        const reviewUrl = `https://review3.cre.ma/${mainUrl}/products/reviews?page=1&product_code=${prdReviewHotping.code}&widget_env=300&widget_id=${prdReviewHotping.id}`;
        console.log('url ', reviewUrl);

        await page.goto(reviewUrl, { waitUntil: 'networkidle2', timeout: 30000 });

        const reviewEls = await page.evaluate(() => {
            const getElementTextContent = (el, selector) => {
                const element = el.querySelector(selector);
                return element ? element.textContent.trim() : '';
            };

            const getImageSrcs = (el, selector) => {
                return Array.from(el.querySelectorAll(selector)).map(img => img.src);
            };

            return Array.from(document.querySelectorAll('.products_reviews__reviews.reviews > li.review_list_v2.review_list_v2--collapsed.renewed_review.js-review-container')).map(el => ({
                author: getElementTextContent(el, '.review_list_v2__user_name_message b'),
                score: '★'.repeat(el.querySelectorAll('.crema_product_reviews_score_star_wrapper--full').length),
                reviewText: getElementTextContent(el, '.review_list_v2__message.js-collapsed-review-content.js-translate-text'),
                images: getImageSrcs(el, 'img.review_media_v2__medium_image.js-review-media')
            }));
        });

        const reviews = [];

        for (const reviewData of reviewEls) {
            reviews.push({
                "상품ID": productDetail["상품ID"],
                "상품명*": productDetail["상품명*"],
                "이미지": JSON.stringify(reviewData.images, null, 2),
                "평점": reviewData.score,
                "리뷰": reviewData.reviewText,
                "작성날짜": '', // 작성날짜를 가져오는 코드가 없습니다.
                "작성자": reviewData.author,
                "상품 상세화면 URL*": productDetail["상품 상세화면 URL*"]
            });
        }

        console.log('reviews hot :', reviews);
        return reviews;

    } else {
        console.log('Code or value not found');
    }

    return reviews;
}

async function getElementTextContent(page, parent, selector) {
    const element = await parent.$(selector);
    return element ? await page.evaluate(el => el.innerText.trim(), element) : '';
}

async function getImageSrcs(page, parent, selector) {
    const imgElements = await parent.$$(selector);
    if (imgElements.length > 0) {
        const imgSrcs = [];
        for (const imgElement of imgElements) {
            const src = await page.evaluate(img => img.getAttribute('data-src') || img.getAttribute('src'), imgElement);
            if (src) {
                imgSrcs.push(src.startsWith('http') ? src : `https:${src}`);
            }
        }
        return imgSrcs;
    }
    return [];
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
    let startTime = moment();
    console.log('Script start time:', startTime.format('YYYY.MM.DD HH:mm:ss'));

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    const browser = await launchBrowser();
    const page = await browser.newPage();
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded' });
    } catch (error) {
        console.error('메인 페이지로 이동 중 오류 발생:', error);
    }
    await page.waitForSelector('script[src*="cfa-js.cafe24.com/cfa.html?uid="]');

    const metaTags = await extractMetaTags(page);

    const bannerInfo = await extractBannerInfo(page, url);

    const footerInfo = await extractFooterInfo(page);

    // console.log('footerInfo111 : ', JSON.stringify(footerInfo, null, 2));
    // await browser.close();
    // return;

    const categoryData = await fetchCategoryData(url, page);

    console.log('categoryData len : ', categoryData.length);

    const categoryInfo = buildHierarchyWithParentReferences(categoryData);

    console.log('categoryInfo : ', categoryInfo.length);

    console.log('categoryInfo : ', JSON.stringify(categoryInfo, null, 2));

    console.log('bannerInfo : ', JSON.stringify(bannerInfo, null, 2));

    const shopInfo = {
        '쇼핑몰 이름': metaTags.siteName,
        '쇼핑몰 UID': metaTags.uid,
        '쇼핑몰 URL': metaTags.siteUrl,
        '파비콘 이미지': metaTags.favicon ? new URL(metaTags.favicon, metaTags.siteUrl).href : '',
        '테마컬러': metaTags.themeColor,
        '회사명': footerInfo?.companyName || '',
        '쇼핑몰 대표자': footerInfo?.ceo || '',
        '쇼핑몰 대표 이미지': metaTags.representativeImage ? new URL(metaTags.representativeImage, metaTags.siteUrl).href : '',
        '고객센터 전화번호': footerInfo?.customerServicePhone || '',
        '사업자등록번호': footerInfo?.businessLicense || '',
        '통신판매번호': footerInfo?.onlineBusinessLicense || ''
    };

    console.log('shopInfo : ', JSON.stringify(shopInfo, null, 2));

    const productDetails = [];
    const productRepls = [];

    await logCategoryInfo(url, categoryInfo, productDetails, productRepls);

    //test 시작
    // console.log('categoryInfo:', categoryInfo.slice(1,2));
    // await logCategoryInfo(url, categoryInfo.slice(1,2), productDetails, productRepls);
    //test 끝

    writeToExcel(shopInfo, bannerInfo, productDetails, productRepls);

    browser.close();

    const endTime = moment();
    console.log('Script end time:', endTime.format('YYYY.MM.DD HH:mm:ss'));

    const totalTime = moment.duration(endTime.diff(startTime));
    console.log('Total execution time:', `${totalTime.hours()}시간 ${totalTime.minutes()}분 ${totalTime.seconds()}초`);
}


// const url = "https://cherryme.kr";
// const url = "https://beidelli.com";
// const url = "https://dailyjou.com";
// const url = "https://ba-on.com";
const url = "https://www.hotping.co.kr";

main(url);