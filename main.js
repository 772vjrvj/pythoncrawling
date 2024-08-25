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
        defaultViewport: null, // 기본 뷰포트 설정을 비활성화하여 전체 화면을 사용
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
            '--start-maximized', // 브라우저를 최대화된 상태로 시작
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

        return {...metaTags, uid: uid || ''}; // UID가 없으면 빈 문자열 반환
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
                return {debug: '푸터 요소를 찾을 수 없음'};
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
        return {debug: '푸터 정보 추출 중 오류 발생'};
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
                banners.push({'배너이미지 URL': imgUrl, '배너 링크': linkUrl, '배너 이름': bannerName});
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

            return banners.length > 0 ? banners : [{'배너이미지 URL': '', '배너 링크': '', '배너 이름': ''}];
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
        acc[item.cate_no] = {...item, data_list: []};
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
        await page.goto(url, {waitUntil: 'domcontentloaded'});

        // 부모 카테고리 데이터 추출
        const categoryData = await page.evaluate(async () => {
            const categories = [];

            // .xans-element-.xans-layout.xans-layout-category 요소를 배열로 받음
            const categoryWrappers = document.querySelectorAll('.xans-element-.xans-layout.xans-layout-category');

            if (categoryWrappers.length > 0) {
                let categoryElements = [];

                // 첫 번째 케이스: ':scope > ul > li' 또는 ':scope > div > ul > li' 선택자
                const ulLiElements = categoryWrappers[0].querySelectorAll(':scope > ul > li, :scope > div > ul > li');

                if (ulLiElements.length > 0) {
                    categoryElements = Array.from(ulLiElements);
                } else {
                    // 두 번째 케이스: ':scope > li' 선택자
                    const liElements = categoryWrappers[0].querySelectorAll(':scope > li');
                    if (liElements.length > 0) {
                        categoryElements = Array.from(liElements);
                    }
                }

                // 존재하는 요소들에 대해 필터링
                categoryElements = categoryElements.filter(li => {
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


        const addCategory = [];

        // 각 부모 카테고리의 서브 카테고리 추출
        for (const category of categoryData) {
            const categoryUrl = `${url}/${category.design_page_url}${category.param}`;

            let alertHandled = false;

            // 자식 페이지에서 alert 처리
            const handleDialog = async dialog => {
                if (!alertHandled) {
                    console.log('Alert detected: ', dialog.message());
                    await dialog.dismiss(); // 알림창 닫기
                    alertHandled = true; // alert 처리됨
                }
            };

            page.on('dialog', handleDialog);
            try {

                await page.goto(categoryUrl, {waitUntil: 'domcontentloaded'});

                // 만약 alert가 발생했다면 이 페이지를 건너뜀
                if (alertHandled) {
                    console.log(`Skipping category due to alert: ${categoryUrl}`);
                    alertHandled = false; // 다음에 사용할 수 있도록 초기화
                    continue; // 다음 카테고리로 이동
                }

                // 서브 카테고리 데이터 추출
                const subCategories = await page.evaluate(async (parentCateNo) => {
                    // 서브 카테고리가 로드될 때까지 대기
                    await new Promise(resolve => setTimeout(resolve, 1000)); // 1초 대기, 상황에 따라 조정 가능

                    const subCategoryLinks = [];
                    // menuCategory 안에 xans-element- xans-product xans-product-displaycategory xans-record- 클래스를 가진 요소를 찾기
                    const productElements = Array.from(document.querySelectorAll('.menuCategory .xans-element-.xans-product.xans-product-displaycategory.xans-record-'));

                    productElements.forEach((productElement) => {
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

            } catch (error) {
                console.log(`Error processing category: ${categoryUrl} - ${error.message}`);
                continue; // 문제가 있는 카테고리는 건너뜀
            } finally {
                page.off('dialog', handleDialog); // 이벤트 핸들러 제거
            }
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
async function logCategoryInfo(page, url, categories, productDetails, productRepls) {
    const logCategory = async (category, parentNames = []) => {
        const currentPath = parentNames.concat({name: category.name});

        if (category.data_list.length === 0) {

            let pageNum = 1;
            let hasMoreData = true;

            while (hasMoreData) {

                const category_menu = JSON.stringify(currentPath, null, 2);
                const category_url = `${url}/${category.design_page_url}${category.param}&page=${pageNum}`;

                console.log('"카테고리(메뉴)*": ', category_menu);

                try {

                    await page.goto(category_url, {waitUntil: 'networkidle2', timeout: 30000});

                    await new Promise(resolve => setTimeout(resolve, 2000));

                    let hrefs = [];

                    // "더보기" 버튼이 있는지 확인
                    const hasLoadMoreButton = await page.$('.xans-element-.xans-product.xans-product-listmore.ec-base-paginate.typeMoreview');

                    if (hasLoadMoreButton) {
                        let currentPage, totalPage;

                        do {
                            // 스크롤을 제일 아래로 내리기
                            await page.evaluate(() => {
                                window.scrollTo(0, document.body.scrollHeight);
                            });

                            // "더보기" 버튼 클릭
                            await page.click('.xans-element-.xans-product.xans-product-listmore.ec-base-paginate.typeMoreview a.btnMore');

                            // 잠시 대기
                            await new Promise(resolve => setTimeout(resolve, 2000));

                            // 현재 페이지와 총 페이지 수를 가져오기
                            currentPage = await page.$eval('#more_current_page', el => parseInt(el.innerText));
                            totalPage = await page.$eval('#more_total_page', el => parseInt(el.innerText));

                        } while (currentPage < totalPage); // 더 이상 페이지가 없을 때까지 반복

                        // 더 이상 데이터가 없다고 설정
                        hasMoreData = false;

                        hrefs = await page.$$eval('ul.prdList2 li .thumbnail', elements =>
                            elements.map(el => {
                                const anchor = el.querySelector('a');
                                return anchor ? anchor.href : null;
                            }).filter(href => href !== null)
                        );

                    }
                    else
                    {
                        hrefs = await page.$$eval('ul.prdList li .thumbnail', elements =>
                            elements.map(el => {
                                const anchor = el.querySelector('a');
                                return anchor ? anchor.href : null;
                            }).filter(href => href !== null)
                        );
                    }


                    console.log('Fetched hrefs: ', hrefs.length);
                    console.log('Fetched hrefs 1 : ', hrefs[0]);
                    console.log('Fetched hrefs L : ', hrefs[hrefs.length - 1]);

                    if (hrefs.length === 0) {
                        hasMoreData = false;
                        console.log('더 이상 데이터가 없습니다.');
                    } else {
                        for (const href of hrefs) {

                            const productIdMatch = href.match(/\/(\d+)\/category\//);
                            const productId = productIdMatch ? productIdMatch[1] : '';


                            const productDetail = {
                                "상품ID": productId, // 추출한 상품ID
                                "상품명*": "",
                                "카테고리(메뉴)*": category_menu,
                                "상품 상세(html)*": "",
                                "상품가격*": "",
                                "상품 할인가격*": "",
                                "상품 이미지*": "",
                                "상품 잔여수량": "",
                                "상품 태그": "",
                                "상품 상세화면 URL*": href,
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
    let reviews = [];
    let alertHandled = false;

    // 자식 페이지에서 alert 처리
    const handleDialog = async dialog => {
        if (!alertHandled) {
            console.log('Alert detected: ', dialog.message());
            await dialog.dismiss(); // 알림창 닫기
            alertHandled = true; // alert 처리됨
        }
    };

    page.on('dialog', handleDialog);

    try {
        await page.goto(productDetail["상품 상세화면 URL*"], { waitUntil: 'networkidle2', timeout: 30000 });

        // 만약 alert가 발생했다면 이 페이지를 건너뜀
        if (alertHandled) {
            console.log(`Skipping product due to alert: ${productDetail["상품 상세화면 URL*"]}`);
            alertHandled = false; // 다음 작업을 위해 초기화
            return reviews; // 빈 배열 리턴
        }


        await new Promise(resolve => setTimeout(resolve, 3000)); // 5초 대기

        // https://cherryme.kr/
        // https://www.hotping.co.kr
        // 추가된 부분: 상품명, 상품가격, 상품 할인가격 추출
        const productInfo = await retry(async () => {
            return await page.evaluate(() => {
                const productDetails = new Map();

                const container = document.querySelector('.xans-element-.xans-product.xans-product-detaildesign');

                if (container) {
                    // 모든 tr.xans-record- 요소를 순회하며 필요한 데이터를 추출
                    container.querySelectorAll('tr.xans-record-').forEach(row => {
                        const label = row.querySelector('th span')?.innerText.trim();
                        if (label === "상품명") {
                            const value = row.querySelector('td span')?.innerText.trim();
                            productDetails.set("상품명*", value || '');
                        } else if (label === "소비자가") {
                            const value = row.querySelector('td span')?.innerText.trim();
                            productDetails.set("상품가격*", value || '');
                        } else if (label === "판매가") {
                            const value = row.querySelector('td span')?.innerText.trim();
                            productDetails.set("상품 할인가격*", value || '');
                        } else if (label === "할인판매가") {
                            const value = row.querySelector('td span')?.innerText.trim();
                            productDetails.set("상품가격*", productDetails.get("상품 할인가격*") || '');
                            productDetails.set("상품 할인가격*", value || '');
                        }
                    });

                    // "상품명*"이 없는 경우, 첫 번째 td span 값을 "상품명*"으로 설정
                    if (!productDetails.has("상품명*")) {
                        const firstTdSpanValue = container.querySelector('tr.xans-record- td span')?.innerText.trim();
                        if (firstTdSpanValue) {
                            productDetails.set("상품명*", firstTdSpanValue);
                        }
                    }
                }

                return Array.from(productDetails.entries()).map(([key, value]) => ({ [key]: value }));
            });
        }, 3, 2000, []);


        productDetail["상품명*"] = productInfo.find(item => item["상품명*"])?.["상품명*"] || '';
        productDetail["상품가격*"] = productInfo.find(item => item["상품가격*"])?.["상품가격*"] ||
            productInfo.find(item => item["상품 할인가격*"])?.["상품 할인가격*"] || '';

        productDetail["상품 할인가격*"] = productInfo.find(item => item["상품 할인가격*"])?.["상품 할인가격*"] ||
            productInfo.find(item => item["상품가격*"])?.["상품가격*"] || '';

        console.log("상품명* : ", productDetail["상품명*"]);
        console.log("상품가격* : ", productDetail["상품가격*"]);
        console.log("상품 할인가격* : ", productDetail["상품 할인가격*"]);


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



        //상품 이미지 중복제거 2024.08.25
        //공통화를 위해 공통 class xans-element-.xans-product.xans-product-image이거를 잡고 내부 이미지중 필요 없는 것고 중복을 제거하는 방식으로 진행
        const productImages = await retry(async () => {
            return await page.evaluate(() => {
                const imgElements = document.querySelectorAll('.xans-element-.xans-product.xans-product-image img');
                const imgUrls = [];

                imgElements.forEach(img => {
                    let src = img.getAttribute('src');
                    if (src) {
                        // 'http:'를 붙여 완전한 URL을 만든 후, 'http:https:' 패턴을 'https:'로 변환
                        let fullUrl = `http:${src}`.replace('http:https:', 'https:');

                        // 제외할 키워드가 URL에 포함되어 있는지 검사
                        const hasInvalidKeywords = /(icon_facebook|icon_twitter|product_zoom|navleft_big|navright_big)/.test(fullUrl);

                        if (!hasInvalidKeywords) {
                            imgUrls.push(fullUrl);
                        }
                    }
                });

                // 중복 제거
                return [...new Set(imgUrls)];
            });
        }, 3, 2000, []);
        productDetail["상품 이미지*"] = JSON.stringify(productImages, null, 2);
        console.log("상품 이미지* : ", productImages);


        /**
         * 옵션 정보와 상태를 처리하는 메인 로직
         * retry 함수는 비동기 작업이 실패할 때 재시도하는 로직을 담당합니다.
         *
         * 상품 옵션들을 일일이 선택해서 구매가능한 상품 목록을 추가합니다.
         * 추가된 목록에 있으면 판매중, 없으면 품절 입니다.
         * 옵션이 1개인 경우와 2개인 경우 구분해서 작업합니다.
         *
         * @returns {Array} options - 옵션 그룹과 그 값들을 포함한 배열
         * @returns {Array} optionsInfos - 각 옵션별 가격 및 상태 정보를 포함한 배열
         *
         * @retry {number} 3 - 최대 3회까지 재시도
         * @delay {number} 2000ms - 재시도 간격
         */
        const [options, optionsInfos] = await retry(async () => {
            return await page.evaluate(async () => {

                // 문자열의 공백을 정리해주는 함수
                function normalizeString(str) {
                    return str.trim().replace(/\s+/g, '');
                }

                // 옵션 텍스트에서 가격 정보를 추출하는 함수 (5,000원) -> 5000
                function extractPrice(text) {
                    const priceMatch = text.match(/\(\s*([-+]?\d{1,3}(?:,\d{3})*)\s*원?\s*\)/);
                    return priceMatch ? priceMatch[1].replace(/[^-+\d]/g, '') : 0;
                }

                // 옵션 엘리먼트들을 선택
                const optionElements = document.querySelectorAll('table.xans-element-.xans-product.xans-record- .xans-element-.xans-product.xans-record-');
                const options = [];
                const optionsInfos = [];

                // 옵션이 1개인 경우 처리
                if (optionElements.length === 1) {
                    //옵션 명
                    const th = optionElements[0].querySelector('th');
                    //옵션 select box
                    const select = optionElements[0].querySelector('select');
                    const optionValues = new Set();

                    if (th && select) {
                        const optionTitle = th.innerText.trim();
                        const optionItems = select.querySelectorAll('option');

                        for (const optionItem of optionItems) {
                            const value = optionItem.value.trim();
                            const text = optionItem.innerText.trim();

                            // 유효한 옵션 값만 처리
                            if (value !== '*' && value !== '**' && value) {
                                optionValues.add(text);
                            }
                        }

                        //옵션(그룹)
                        options.push({
                            "이름": optionTitle,
                            "밸류": Array.from(optionValues),
                        });

                        for (const optionValue of optionValues) {
                            //옵션정보에 추가
                            optionsInfos.push({
                                '옵션1': optionValue,
                                '옵션가격': extractPrice(optionValue),
                                '옵션상태': optionValue.includes('품절') ? '품절' : '판매중',
                            });
                        }
                    }
                }

                // 옵션이 2개인 경우 처리
                if (optionElements.length === 2) {
                    const option1Element = optionElements[0];
                    const option2Element = optionElements[1];
                    const option1Values = [];
                    let option2ValuesSet = new Set();

                    let option1Title = "";
                    let option2Title = "";

                    //첫번째 옵션
                    const th1 = option1Element.querySelector('th');
                    const select1 = option1Element.querySelector('select');

                    if (th1 && select1) {
                        option1Title = th1.innerText.trim();
                        const option1Items = select1.querySelectorAll('option');

                        for (const option1Item of option1Items) {
                            const value1 = option1Item.value.trim();
                            const text1 = option1Item.innerText.trim();

                            if (value1 !== '*' && value1 !== '**' && value1) {
                                option1Values.push(text1);

                                option1Item.selected = true;
                                option1Item.dispatchEvent(new Event('change', { bubbles: true }));
                                option1Item.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                //두번째 옵션
                                const th2 = option2Element.querySelector('th');
                                const select2 = option2Element.querySelector('select');

                                if (th2 && select2) {
                                    option2Title = th2.innerText.trim();
                                    const option2Items = select2.querySelectorAll('option');

                                    const option2Values = []

                                    for (const option2Item of option2Items) {
                                        const value2 = option2Item.value.trim();
                                        const text2 = option2Item.innerText.trim();

                                        if (value2 !== '*' && value2 !== '**' && value2) {
                                            option2Values.push(text2);
                                            option2ValuesSet.add(text2);
                                        }
                                    }

                                    for (const option2Value of option2Values) {
                                        optionsInfos.push({
                                            '옵션1': text1,
                                            '옵션2': option2Value,
                                            '옵션가격': extractPrice(option2Value),
                                            '옵션상태': option2Value.includes('품절') ? '품절' : '판매중',
                                        });
                                    }
                                }
                            }
                        }
                    }

                    //첫번째 옵션(구륩)
                    options.push({
                        "이름": option1Title,
                        "밸류": option1Values,
                    });

                    //두번째 옵션(구륩)
                    options.push({
                        "이름": option2Title,
                        "밸류": Array.from(option2ValuesSet),
                    });
                }

                return [options, optionsInfos];
            });
        }, 3, 2000, []);

        productDetail["옵션(그룹)"] = JSON.stringify(options, null, 2);
        console.log("옵션(그룹) : ", productDetail["옵션(그룹)"]);

        productDetail["옵션정보"] = JSON.stringify(optionsInfos, null, 2);
        console.log("옵션정보 : ", productDetail["옵션정보"]);

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
                            imgUrls.push({url: src});
                        }
                    });
                    if (imgUrls.length > 0) notice["이미지"] = imgUrls;
                }
                return notice;
            });
        }, 1, 2000, {});
        productDetail["상품 고지 정보"] = productNotice;
        console.log("상품 고지 정보 : ", JSON.stringify(productNotice, null, 2));

        reviews = await fetchProductReviews(page, productDetail, url);
        await browser.close();
        return reviews;

    } catch (error) {
        console.log('상품 상세 페이지로 이동 중 오류 발생 url:', url);
        console.error('상품 상세 페이지로 이동 중 오류 발생:', error);

        return reviews; // 오류 발생 시 빈 배열 리턴
    } finally {
        page.off('dialog', handleDialog); // 이벤트 핸들러 제거
        if (browser.isConnected()) {
            await browser.close(); // 브라우저 종료
        }
    }
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
                // const imageElement = await reviewElement.$('.sf_review_user_photo img');
                // const image = imageElement ? await frame.evaluate(img => img.src, imageElement) : '';

                const imageElements = await reviewElement.$$('.sf_review_user_photo img');
                const images = [];
                for (const imageElement of imageElements) {
                    const src = await frame.evaluate(img => img.getAttribute('src') || img.getAttribute('data-src'), imageElement);
                    images.push(src);
                }


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
        await page.goto(url, {waitUntil: 'networkidle2', timeout: 30000});

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

        await page.goto(reviewUrl, {waitUntil: 'networkidle2', timeout: 30000});

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
        await page.goto(url, {waitUntil: 'domcontentloaded'});
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

    // console.log('categoryData len : ', categoryData.length);

    const categoryInfo = buildHierarchyWithParentReferences(categoryData);

    // const categoryInfo = testJson;

    console.log('categoryInfo len : ', categoryInfo.length);

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

    await logCategoryInfo(page, url, categoryInfo, productDetails, productRepls);

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
// const url = "https://www.hotping.co.kr";
// const url = "https://ba-on.com";
// const url = "https://beidelli.com";
const url = "https://dailyjou.com";

main(url);

// testDetail(url)
async function testDetail(url)
{
    //1개 옵션 테스트
    // let href = "https://cherryme.kr/product/%EB%8B%B9%EC%9D%BC%EC%B6%9C%EA%B3%A0%EC%8B%A0%EC%83%81%ED%95%A0%EC%9D%B8%F0%9F%92%99-%EB%B0%9C%EB%A0%88%EC%BD%94%EC%96%B4-%EC%B2%AD%EC%88%9C-%ED%81%AC%EB%A1%AD-%EB%A6%AC%EB%B3%B8-%EC%8A%A4%ED%8A%B8%EB%9E%A9-%ED%88%AC%ED%94%BC%EC%8A%A4-%EB%B9%84%ED%82%A4%EB%8B%88-%EC%88%98%EC%98%81%EB%B3%B5/385/category/59/display/1/#none";
    // let href = "https://www.hotping.co.kr/product/detail.html?product_no=39386&cate_no=1900&display_group=1";
    // let href = "https://dailyjou.com/product/21%EB%A7%8C%EC%9E%A5%ED%8C%90%EB%A7%A4made-%EB%8D%B0%EC%96%B4-%EB%B0%B4%EB%94%A9-%ED%8C%AC%EC%B8%A0%EC%88%8F%ED%8C%AC%EC%B8%A0-%EC%B6%94%EA%B0%80/3420/category/50/display/1/"
    // let href = "https://ba-on.com/product/baonhaus-%EC%97%90%ED%83%80%EC%9D%B4-%EC%8A%A4%ED%8A%B8%EB%9D%BC%EC%9D%B4%ED%94%84-%EC%98%A4%EB%B2%84-%EC%85%94%EC%B8%A0-2color/18402/category/39/display/2/";

    //2개 옵션 테스트
    // let href = 'https://www.hotping.co.kr/product/set%EB%AA%A8%EB%8D%B8%EC%BD%94%EB%94%94-%ED%95%A0%EC%9D%B8%EA%B5%AC%EB%A7%A4made-%EC%A0%9C%EC%8A%A4%ED%8B%B0-%ED%85%8C%EC%9D%BC%EB%9F%AC%EB%93%9C%EB%8D%94%EB%B8%94%EC%9E%90%EC%BC%93made-%EC%A0%9C%EC%8A%A4%ED%8B%B0-%EB%92%B7%EB%B0%B4%EB%94%A9-%EB%A1%B1-%EC%99%80%EC%9D%B4%EB%93%9C-%EC%8A%AC%EB%9E%99%EC%8A%A4%ED%88%AC%ED%94%BC%EC%8A%A4%EC%85%8B%EC%97%85-%EC%A0%95%EC%9E%A5%EC%84%B8%ED%8A%B8-%EC%A0%95%EC%9E%A5%EC%84%B8%ED%8A%B8-%EB%A9%B4%EC%A0%91%EB%A3%A9/44485/category/620/display/1/';
    // let href = 'https://dailyjou.com/product/%EB%94%94%EB%A0%89%ED%8A%B8-%EC%BB%B7%ED%8C%85-%EB%8D%B0%EB%AF%B8%EC%A7%80-%EB%8D%B0%EB%8B%98-%EC%88%8F%ED%8C%AC%EC%B8%A0/18520/category/214/display/1/';
    // let href = 'https://ba-on.com/product/%ED%94%8C%EB%A3%A8%ED%82%A4-%EC%98%A4%EB%B2%84-%ED%9B%84%EB%93%9C-%EA%B8%B4%ED%8C%94-%EC%85%94%EC%B8%A0-2color/18939/category/34/display/1/';
    // let href = 'https://beidelli.com/product/detail.html?product_no=4184&cate_no=49&display_group=2';
    // let href = 'https://beidelli.com/product/detail.html?product_no=4184&cate_no=24&display_group=1';
    // let href = 'https://www.hotping.co.kr/product/made-%EB%A3%A8%EC%9D%B4%EC%8A%A4-%EC%9E%90%EC%88%98%EB%A1%B1%EC%9B%90%ED%94%BC%EC%8A%A444110/25527/category/25/display/1/'
    // let href = 'https://dailyjou.com/product/%EC%B9%B4%EC%8B%9C%ED%83%80-%EB%A0%88%EC%9D%B4%EC%8A%A4-%EB%82%98%EC%8B%9C-%EB%A1%B1-%EC%9B%90%ED%94%BC%EC%8A%A4%EB%81%88-%EC%A1%B0%EC%A0%88%EA%B0%80%EB%8A%A5/18722/category/214/display/1/'
    // let href = 'https://www.hotping.co.kr/product/2%EA%B8%B0%EC%9E%A5%EB%8D%B0%EC%9D%BC%EB%A6%AC%ED%95%84%EC%88%98%F0%9F%92%95made-%EC%97%90%EB%94%94%EC%85%98-%EA%B8%B0%EB%B3%B8%EC%88%8F-%EC%8A%AC%EB%A6%AC%EB%B8%8C%EB%A6%AC%EC%8A%A4-%EC%9D%B4%EB%84%88%ED%8B%B044110-%EB%B9%85%EC%82%AC%EC%9D%B4%EC%A6%88%EB%82%98%EC%8B%9C-%EC%9D%B4%EB%84%88%EB%82%98%EC%8B%9C-%EB%8D%B0%EC%9D%BC%EB%A6%AC%EB%82%98%EC%8B%9C-%EB%B2%A0%EC%9D%B4%EC%A7%81%EB%82%98%EC%8B%9C-%EB%AC%B4%EC%A7%80%EB%82%98%EC%8B%9C-%ED%81%AC%EB%A1%AD%EB%82%98%EC%8B%9C/39923/category/25/display/1/'
    // let href = 'https://dailyjou.com/product/%EC%9D%B4%EB%A0%88%ED%94%84-%EB%A9%80%ED%8B%B0-%EC%8A%A4%ED%8A%B8%EB%9E%A9-%EC%83%8C%EB%93%A4/18164/category/214/display/1/'
    // let href = 'https://beidelli.com/product/detail.html?product_no=4164&cate_no=24&display_group=1'

    // let href = 'https://ba-on.com/product/3%EC%B2%9C%EC%9E%A5%EB%8F%8C%ED%8C%8Cunisex-%EC%9D%B4%EC%A7%80%EC%98%A4-%EB%A0%88%ED%84%B0%EB%A7%81-%EB%82%98%EC%9D%BC%EB%A1%A0-%EC%98%A4%EB%B2%84-%ED%9B%84%EB%93%9C-3color/17337/category/786/display/1/'
    let href = 'https://dailyjou.com/product/%EC%B9%B4%EC%8B%9C%ED%83%80-%EB%A0%88%EC%9D%B4%EC%8A%A4-%EB%82%98%EC%8B%9C-%EB%A1%B1-%EC%9B%90%ED%94%BC%EC%8A%A4%EB%81%88-%EC%A1%B0%EC%A0%88%EA%B0%80%EB%8A%A5/18722/category/214/display/1/';

    const productDetails = [];
    const productRepls = [];


    const productIdMatch = href.match(/\/(\d+)\/category\//);
    const productId = productIdMatch ? productIdMatch[1] : '';


    const productDetail = {
        "상품ID": productId, // 추출한 상품ID
        "상품명*": "",
        "카테고리(메뉴)*": "",
        "상품 상세(html)*": "",
        "상품가격*": "",
        "상품 할인가격*": "",
        "상품 이미지*": "",
        "상품 잔여수량": "",
        "상품 태그": "",
        "상품 상세화면 URL*": href,
        "옵션": [],
        "옵션 정보": [],
        "상품 고지 정보": "",
        "카테고리(URL)": ""
    };

    console.log("productDetail : ", JSON.stringify(productDetail, null, 2));

    const reviews = await fetchProductDetails(productDetail, url);
    productDetails.push(productDetail);
    productRepls.push(...reviews);
}

//https://cherryme.kr
const testJson_x1 = [
    {
        "link_product_list": "https://cherryme.kr/category/365%EC%9D%BCsummer%F0%9F%8C%B4/44/",
        "name": "365일SUMMER🌴",
        "param": "?cate_no=44",
        "cate_no": 44,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://cherryme.kr/category/%EB%B9%84%ED%82%A4%EB%8B%88%F0%9F%91%99/59/",
                "name": "비키니👙",
                "param": "?cate_no=59",
                "cate_no": 59,
                "parent_cate_no": 44,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://cherryme.kr/category/%EC%9B%90%ED%94%BC%EC%8A%A4%EB%AA%A8%EB%85%B8%ED%82%A4%EB%8B%88%F0%9F%A9%B1/56/",
                "name": "원피스&모노키니🩱",
                "param": "?cate_no=56",
                "cate_no": 56,
                "parent_cate_no": 44,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://cherryme.kr/category/%EC%9D%B4%EB%84%88%EB%B3%BC%EB%A5%A8%EC%95%84%EC%9D%B4%ED%85%9C/48/",
                "name": "이너+볼륨아이템!",
                "param": "?cate_no=48",
                "cate_no": 48,
                "parent_cate_no": 44,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://cherryme.kr/category/%EB%B0%94%EC%BA%89%EC%8A%A4%EB%A3%A9%F0%9F%92%99/54/",
        "name": "바캉스룩💙",
        "param": "?cate_no=54",
        "cate_no": 54,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://cherryme.kr/category/%EC%9B%90%ED%94%BC%EC%8A%A4/42/",
        "name": "원피스",
        "param": "?cate_no=42",
        "cate_no": 42,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://cherryme.kr/category/%EB%AF%B8%EB%8B%88%EC%9B%90%ED%94%BC%EC%8A%A4/64/",
                "name": "미니원피스",
                "param": "?cate_no=64",
                "cate_no": 64,
                "parent_cate_no": 42,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://cherryme.kr/category/%EB%A1%B1%EC%9B%90%ED%94%BC%EC%8A%A4/66/",
                "name": "롱원피스",
                "param": "?cate_no=66",
                "cate_no": 66,
                "parent_cate_no": 42,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://cherryme.kr/category/%EC%A0%90%ED%94%84%EC%88%98%ED%8A%B8/52/",
                "name": "점프수트",
                "param": "?cate_no=52",
                "cate_no": 52,
                "parent_cate_no": 42,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://cherryme.kr/category/%ED%99%88%EC%9B%A8%EC%96%B4%F0%9F%A7%B8/62/",
        "name": "홈웨어🧸",
        "param": "?cate_no=62",
        "cate_no": 62,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://cherryme.kr/category/%EC%BD%94%EB%94%94%EC%84%B8%ED%8A%B8/43/",
        "name": "코디세트",
        "param": "?cate_no=43",
        "cate_no": 43,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://cherryme.kr/category/%EC%83%81%EC%9D%98/49/",
        "name": "상의",
        "param": "?cate_no=49",
        "cate_no": 49,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://cherryme.kr/category/%ED%95%98%EC%9D%98/70/",
        "name": "하의",
        "param": "?cate_no=70",
        "cate_no": 70,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://cherryme.kr/category/%EC%95%84%EC%9A%B0%ED%84%B0/47/",
        "name": "아우터",
        "param": "?cate_no=47",
        "cate_no": 47,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    }
]

//https://www.hotping.co.kr
const testJson_x2 = [
    {
        "link_product_list": "https://www.hotping.co.kr/product/bestList.html?cate_no=24",
        "name": "BEST",
        "param": "?cate_no=24",
        "cate_no": 24,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B3%A0%EA%B0%9D%EC%B6%94%EC%B2%9C/1426/",
                "name": "고객추천",
                "param": "?cate_no=1426",
                "cate_no": 1426,
                "parent_cate_no": 24,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            // {
            //     "link_product_list": "https://www.hotping.co.kr/category/%EC%95%84%EC%9A%B0%ED%84%B0-best/530/",
            //     "name": "아우터 BEST",
            //     "param": "?cate_no=530",
            //     "cate_no": 530,
            //     "parent_cate_no": 24,
            //     "design_page_url": "product/list.html",
            //     "data_list": []
            // },
            // {
            //     "link_product_list": "https://www.hotping.co.kr/category/%EC%9B%90%ED%94%BC%EC%8A%A4-best/527/",
            //     "name": "원피스 BEST",
            //     "param": "?cate_no=527",
            //     "cate_no": 527,
            //     "parent_cate_no": 24,
            //     "design_page_url": "product/list.html",
            //     "data_list": []
            // },
            // {
            //     "link_product_list": "https://www.hotping.co.kr/category/%EC%83%81%EC%9D%98-best/1420/",
            //     "name": "상의 BEST",
            //     "param": "?cate_no=1420",
            //     "cate_no": 1420,
            //     "parent_cate_no": 24,
            //     "design_page_url": "product/list.html",
            //     "data_list": []
            // },
            // {
            //     "link_product_list": "https://www.hotping.co.kr/category/%ED%95%98%EC%9D%98-best/1421/",
            //     "name": "하의 BEST",
            //     "param": "?cate_no=1421",
            //     "cate_no": 1421,
            //     "parent_cate_no": 24,
            //     "design_page_url": "product/list.html",
            //     "data_list": []
            // }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list_new.html?cate_no=25",
        "name": "NEW 7%",
        "param": "?cate_no=25",
        "cate_no": 25,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=2106",
        "name": "가을가을🍁",
        "param": "?cate_no=2106",
        "cate_no": 2106,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list_77.html?cate_no=1772",
        "name": "난77💝",
        "param": "?cate_no=1772",
        "cate_no": 1772,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=90",
        "name": "하객룩💐",
        "param": "?cate_no=90",
        "cate_no": 90,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%93%9C%EB%A0%88%EC%8A%A4/97/",
                "name": "드레스",
                "param": "?cate_no=97",
                "cate_no": 97,
                "parent_cate_no": 90,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%95%84%EC%9A%B0%ED%84%B0/98/",
                "name": "아우터",
                "param": "?cate_no=98",
                "cate_no": 98,
                "parent_cate_no": 90,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/99/",
                "name": "블라우스",
                "param": "?cate_no=99",
                "cate_no": 99,
                "parent_cate_no": 90,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%95%98%EC%9D%98/100/",
                "name": "하의",
                "param": "?cate_no=100",
                "cate_no": 100,
                "parent_cate_no": 90,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%84%B8%ED%8A%B8/1131/",
                "name": "세트",
                "param": "?cate_no=1131",
                "cate_no": 1131,
                "parent_cate_no": 90,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=1506",
        "name": "여행룩✈️",
        "param": "?cate_no=1506",
        "cate_no": 1506,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%9B%84%EC%BF%A0%EC%98%A4%EC%B9%B4/1900/",
                "name": "후쿠오카",
                "param": "?cate_no=1900",
                "cate_no": 1900,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%8B%9C%EB%93%9C%EB%8B%88%F0%9F%A6%98/1757/",
                "name": "시드니🦘",
                "param": "?cate_no=1757",
                "cate_no": 1757,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%99%8D%EC%BD%A9/1943/",
                "name": "홍콩",
                "param": "?cate_no=1943",
                "cate_no": 1943,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8F%84%EC%BF%84%F0%9F%97%BC/1702/",
                "name": "도쿄🗼",
                "param": "?cate_no=1702",
                "cate_no": 1702,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%A0%9C%EC%A3%BC%F0%9F%8C%B4/1701/",
                "name": "제주🌴",
                "param": "?cate_no=1701",
                "cate_no": 1701,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B3%B5%ED%95%AD%EB%A3%A9%F0%9F%9B%AC/1508/",
                "name": "공항룩🛬",
                "param": "?cate_no=1508",
                "cate_no": 1508,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%9C%B4%EC%96%91%EC%A7%80%EB%A3%A9%EF%B8%8F/1750/",
                "name": "휴양지룩⛱️",
                "param": "?cate_no=1750",
                "cate_no": 1750,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%88%98%EC%98%81%EB%B3%B5acc/1527/",
                "name": "수영복/ACC",
                "param": "?cate_no=1527",
                "cate_no": 1527,
                "parent_cate_no": 1506,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=169",
        "name": "LOVB LOVB",
        "param": "?cate_no=169",
        "cate_no": 169,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=26",
        "name": "DRESS",
        "param": "?cate_no=26",
        "cate_no": 26,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%A1%B1%EC%9B%90%ED%94%BC%EC%8A%A4/50/",
                "name": "롱원피스",
                "param": "?cate_no=50",
                "cate_no": 50,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%AF%B8%EB%8B%88%EC%9B%90%ED%94%BC%EC%8A%A4/471/",
                "name": "미니원피스",
                "param": "?cate_no=471",
                "cate_no": 471,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8C%A8%ED%84%B4%EC%9B%90%ED%94%BC%EC%8A%A4/472/",
                "name": "패턴원피스",
                "param": "?cate_no=472",
                "cate_no": 472,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%95%98%EA%B0%9D%EC%98%A4%ED%94%BC%EC%8A%A4/49/",
                "name": "하객&오피스",
                "param": "?cate_no=49",
                "cate_no": 49,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B7%94%EC%8A%A4%ED%8B%B0%EC%97%90/404/",
                "name": "뷔스티에",
                "param": "?cate_no=404",
                "cate_no": 404,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%88%AC%ED%94%BC%EC%8A%A4/48/",
                "name": "투피스",
                "param": "?cate_no=48",
                "cate_no": 48,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=27",
        "name": "OUTER",
        "param": "?cate_no=27",
        "cate_no": 27,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%A0%90%ED%8D%BC/58/",
                "name": "점퍼",
                "param": "?cate_no=58",
                "cate_no": 58,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%BD%94%ED%8A%B8/76/",
                "name": "코트",
                "param": "?cate_no=76",
                "cate_no": 76,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%9E%90%EC%BC%93/57/",
                "name": "자켓",
                "param": "?cate_no=57",
                "cate_no": 57,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B0%80%EB%94%94%EA%B1%B4/61/",
                "name": "가디건",
                "param": "?cate_no=61",
                "cate_no": 61,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8A%B8%EC%9C%84%EB%93%9C/1129/",
                "name": "트위드",
                "param": "?cate_no=1129",
                "cate_no": 1129,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8C%A8%EB%94%A9%EB%B2%A0%EC%8A%A4%ED%8A%B8/77/",
                "name": "패딩/베스트",
                "param": "?cate_no=77",
                "cate_no": 77,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=29",
        "name": "TOP",
        "param": "?cate_no=29",
        "cate_no": 29,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8B%B0%EC%85%94%EC%B8%A0/360/",
                "name": "티셔츠",
                "param": "?cate_no=360",
                "cate_no": 360,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%A7%A8%ED%88%AC%EB%A7%A8%ED%9B%84%EB%93%9C/364/",
                "name": "맨투맨/후드",
                "param": "?cate_no=364",
                "cate_no": 364,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B0%98%ED%8C%94%ED%8B%B0/1444/",
                "name": "반팔티",
                "param": "?cate_no=1444",
                "cate_no": 1444,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B2%A0%EC%9D%B4%EC%A7%81/467/",
                "name": "베이직",
                "param": "?cate_no=467",
                "cate_no": 467,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8C%A8%ED%84%B4%ED%94%84%EB%A6%B0%ED%8C%85/468/",
                "name": "패턴/프린팅",
                "param": "?cate_no=468",
                "cate_no": 468,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8/1199/",
                "name": "니트",
                "param": "?cate_no=1199",
                "cate_no": 1199,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%82%98%EC%8B%9C/365/",
                "name": "나시",
                "param": "?cate_no=365",
                "cate_no": 365,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/set%EC%84%B8%ED%8A%B8/403/",
                "name": "SET(세트)",
                "param": "?cate_no=403",
                "cate_no": 403,
                "parent_cate_no": 29,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=66",
        "name": "KNIT",
        "param": "?cate_no=66",
        "cate_no": 66,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8%ED%8B%B0/121/",
                "name": "니트티",
                "param": "?cate_no=121",
                "cate_no": 121,
                "parent_cate_no": 66,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8%EA%B0%80%EB%94%94%EA%B1%B4/119/",
                "name": "니트가디건",
                "param": "?cate_no=119",
                "cate_no": 119,
                "parent_cate_no": 66,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8%EC%9B%90%ED%94%BC%EC%8A%A4%ED%88%AC%ED%94%BC%EC%8A%A4/434/",
                "name": "니트원피스(투피스)",
                "param": "?cate_no=434",
                "cate_no": 434,
                "parent_cate_no": 66,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8%EB%B2%A0%EC%8A%A4%ED%8A%B8/469/",
                "name": "니트베스트",
                "param": "?cate_no=469",
                "cate_no": 469,
                "parent_cate_no": 66,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8B%88%ED%8A%B8%ED%95%98%EC%9D%98/120/",
                "name": "니트하의",
                "param": "?cate_no=120",
                "cate_no": 120,
                "parent_cate_no": 66,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=28",
        "name": "SHIRTS",
        "param": "?cate_no=28",
        "cate_no": 28,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/465/",
                "name": "블라우스",
                "param": "?cate_no=465",
                "cate_no": 465,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%85%94%EC%B8%A0/466/",
                "name": "셔츠",
                "param": "?cate_no=466",
                "cate_no": 466,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=31",
        "name": "PANTS",
        "param": "?cate_no=31",
        "cate_no": 31,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%A7%88%EB%B2%95%EB%B0%94%EC%A7%80/279/",
                "name": "마법바지",
                "param": "?cate_no=279",
                "cate_no": 279,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%8D%B0%EB%8B%98/54/",
                "name": "데님",
                "param": "?cate_no=54",
                "cate_no": 54,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%BD%94%ED%8A%BC/1664/",
                "name": "코튼",
                "param": "?cate_no=1664",
                "cate_no": 1664,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%8A%AC%EB%9E%99%EC%8A%A4/124/",
                "name": "슬랙스",
                "param": "?cate_no=124",
                "cate_no": 124,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%8A%A4%ED%82%A4%EB%8B%88/531/",
                "name": "스키니",
                "param": "?cate_no=531",
                "cate_no": 531,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%A1%B0%EA%B1%B0%ED%8C%AC%EC%B8%A0/1319/",
                "name": "조거팬츠",
                "param": "?cate_no=1319",
                "cate_no": 1319,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%B9%B4%EA%B3%A0%EB%B0%94%EC%A7%80/1743/",
                "name": "카고바지",
                "param": "?cate_no=1743",
                "cate_no": 1743,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B8%B0%EB%B3%B8%EB%A1%B1%EB%B2%84%EC%A0%84/565/",
                "name": "기본&롱버전",
                "param": "?cate_no=565",
                "cate_no": 565,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B0%B4%EB%94%A9%EB%B0%94%EC%A7%80/620/",
                "name": "밴딩바지",
                "param": "?cate_no=620",
                "cate_no": 620,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%A0%88%EA%B9%85%EC%8A%A4/65/",
                "name": "레깅스",
                "param": "?cate_no=65",
                "cate_no": 65,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B0%98%EB%B0%94%EC%A7%80%EC%B9%98%EB%A7%88%EB%B0%94%EC%A7%80/290/",
                "name": "반바지/치마바지",
                "param": "?cate_no=290",
                "cate_no": 290,
                "parent_cate_no": 31,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=535",
        "name": "SKIRT",
        "param": "?cate_no=535",
        "cate_no": 535,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%A1%B1%EC%8A%A4%EC%BB%A4%ED%8A%B8/568/",
                "name": "롱스커트",
                "param": "?cate_no=568",
                "cate_no": 568,
                "parent_cate_no": 535,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%AF%B8%EB%8B%88%EC%8A%A4%EC%BB%A4%ED%8A%B8/569/",
                "name": "미니스커트",
                "param": "?cate_no=569",
                "cate_no": 569,
                "parent_cate_no": 535,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=30",
        "name": "TRAINING / 홈웨어",
        "param": "?cate_no=30",
        "cate_no": 30,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D%EC%84%B8%ED%8A%B8/624/",
                "name": "트레이닝>세트",
                "param": "?cate_no=624",
                "cate_no": 624,
                "parent_cate_no": 30,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D%EC%83%81%EC%9D%98/622/",
                "name": "트레이닝>상의",
                "param": "?cate_no=622",
                "cate_no": 622,
                "parent_cate_no": 30,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D%ED%95%98%EC%9D%98/623/",
                "name": "트레이닝>하의",
                "param": "?cate_no=623",
                "cate_no": 623,
                "parent_cate_no": 30,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%9B%90%ED%94%BC%EC%8A%A4/719/",
                "name": "원피스",
                "param": "?cate_no=719",
                "cate_no": 719,
                "parent_cate_no": 30,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=102",
        "name": "INNER",
        "param": "?cate_no=102",
        "cate_no": 102,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B3%B4%EC%A0%95%EC%86%8D%EC%98%B7%EC%86%8D%EB%B0%94%EC%A7%80/418/",
                "name": "보정속옷/속바지",
                "param": "?cate_no=418",
                "cate_no": 418,
                "parent_cate_no": 102,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%86%8D%EC%98%B7set/417/",
                "name": "속옷(set)",
                "param": "?cate_no=417",
                "cate_no": 417,
                "parent_cate_no": 102,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%82%98%EC%8B%9C/419/",
                "name": "나시",
                "param": "?cate_no=419",
                "cate_no": 419,
                "parent_cate_no": 102,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%8C%8C%EC%9E%90%EB%A7%88/651/",
                "name": "파자마",
                "param": "?cate_no=651",
                "cate_no": 651,
                "parent_cate_no": 102,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=43",
        "name": "SHOES",
        "param": "?cate_no=43",
        "cate_no": 43,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%B0%A9%ED%95%9C%EA%B5%AC%EB%91%90/709/",
                "name": "착한구두",
                "param": "?cate_no=709",
                "cate_no": 709,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%94%8C%EB%9E%AB%EB%A1%9C%ED%8D%BC/83/",
                "name": "플랫/로퍼",
                "param": "?cate_no=83",
                "cate_no": 83,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%9E%90%ED%8E%8C%ED%94%84%EC%8A%A4/82/",
                "name": "힐/펌프스",
                "param": "?cate_no=82",
                "cate_no": 82,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%95%B5%ED%81%B4%EB%B6%80%EC%B8%A0%EC%9B%8C%EC%BB%A4/84/",
                "name": "앵클/부츠/워커",
                "param": "?cate_no=84",
                "cate_no": 84,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88%EC%8A%AC%EB%A6%BD%EC%98%A8/85/",
                "name": "스니커즈/슬립온",
                "param": "?cate_no=85",
                "cate_no": 85,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%83%8C%EB%93%A4%EC%8A%AC%EB%A6%AC%ED%8D%BC/86/",
                "name": "샌들/슬리퍼",
                "param": "?cate_no=86",
                "cate_no": 86,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=34",
        "name": "ACC/BAG",
        "param": "?cate_no=34",
        "cate_no": 34,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%96%91%EB%A7%90/87/",
                "name": "양말",
                "param": "?cate_no=87",
                "cate_no": 87,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B0%80%EB%B0%A9/74/",
                "name": "가방",
                "param": "?cate_no=74",
                "cate_no": 74,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%AA%A8%EC%9E%90%ED%97%A4%EC%96%B4/68/",
                "name": "모자/헤어",
                "param": "?cate_no=68",
                "cate_no": 68,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%A5%AC%EC%96%BC%EB%A6%AC/72/",
                "name": "쥬얼리",
                "param": "?cate_no=72",
                "cate_no": 72,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%95%88%EA%B2%BD%EC%84%A0%EA%B8%80%EB%9D%BC%EC%8A%A4/151/",
                "name": "안경&선글라스",
                "param": "?cate_no=151",
                "cate_no": 151,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EB%B2%A8%ED%8A%B8%EC%9E%A5%EA%B0%91etc/75/",
                "name": "벨트/장갑/etc",
                "param": "?cate_no=75",
                "cate_no": 75,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://www.hotping.co.kr/product/list.html?cate_no=447",
        "name": "여름싹-세일🎁",
        "param": "?cate_no=447",
        "cate_no": 447,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%9B%90%ED%94%BC%EC%8A%A4/452/",
                "name": "원피스",
                "param": "?cate_no=452",
                "cate_no": 452,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%83%81%EC%9D%98/448/",
                "name": "상의",
                "param": "?cate_no=448",
                "cate_no": 448,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%ED%95%98%EC%9D%98/449/",
                "name": "하의",
                "param": "?cate_no=449",
                "cate_no": 449,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%95%84%EC%9A%B0%ED%84%B0/450/",
                "name": "아우터",
                "param": "?cate_no=450",
                "cate_no": 450,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EC%9D%B4%EB%84%88acc/451/",
                "name": "이너/acc",
                "param": "?cate_no=451",
                "cate_no": 451,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://www.hotping.co.kr/category/%EA%B7%A0%EC%9D%BC%EA%B0%80/1759/",
                "name": "균일가✨",
                "param": "?cate_no=1759",
                "cate_no": 1759,
                "parent_cate_no": 447,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    }
]

//https://ba-on.com
const testJson_x3 = [
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=765",
        "name": "☂️장마코디제안",
        "param": "?cate_no=765",
        "cate_no": 765,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/best.html?cate_no=85",
        "name": "NEW 5%",
        "param": "?cate_no=85",
        "cate_no": 85,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/best.html?cate_no=132",
        "name": "BEST 50",
        "param": "?cate_no=132",
        "cate_no": 132,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/best.html?cate_no=39",
        "name": "🏠BAONHAUS!",
        "param": "?cate_no=39",
        "cate_no": 39,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EC%95%84%EC%9A%B0%ED%84%B0/73/",
                "name": "아우터",
                "param": "?cate_no=73",
                "cate_no": 73,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%83%81%EC%9D%98/69/",
                "name": "상의",
                "param": "?cate_no=69",
                "cate_no": 69,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B0%94%EC%A7%80/70/",
                "name": "바지",
                "param": "?cate_no=70",
                "cate_no": 70,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%8A%A4%EC%BB%A4%ED%8A%B8/72/",
                "name": "스커트",
                "param": "?cate_no=72",
                "cate_no": 72,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%9B%90%ED%94%BC%EC%8A%A4/75/",
                "name": "원피스",
                "param": "?cate_no=75",
                "cate_no": 75,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%95%85%EC%84%B8%EC%84%9C%EB%A6%AC/74/",
                "name": "악세서리",
                "param": "?cate_no=74",
                "cate_no": 74,
                "parent_cate_no": 39,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=700",
        "name": "BASIC_BAON",
        "param": "?cate_no=700",
        "cate_no": 700,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=619",
        "name": "회원전용 특별관",
        "param": "?cate_no=619",
        "cate_no": 619,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/best.html?cate_no=628",
        "name": "무료배송",
        "param": "?cate_no=628",
        "cate_no": 628,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/best.html?cate_no=347",
        "name": "베스트재입고",
        "param": "?cate_no=347",
        "cate_no": 347,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=34",
        "name": "TOP",
        "param": "?cate_no=34",
        "cate_no": 34,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EB%A6%B0%EB%84%A8%F0%9F%8C%BF/548/",
                "name": "린넨🌿",
                "param": "?cate_no=548",
                "cate_no": 548,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%85%94%EC%B8%A0%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/43/",
                "name": "셔츠/블라우스",
                "param": "?cate_no=43",
                "cate_no": 43,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%ED%8B%B0%EC%85%94%EC%B8%A0/42/",
                "name": "티셔츠",
                "param": "?cate_no=42",
                "cate_no": 42,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B0%98%ED%8C%94/102/",
                "name": "반팔",
                "param": "?cate_no=102",
                "cate_no": 102,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%82%98%EC%8B%9C%EB%B2%A0%EC%8A%A4%ED%8A%B8/109/",
                "name": "나시/베스트",
                "param": "?cate_no=109",
                "cate_no": 109,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%ED%9B%84%EB%93%9C%EB%A7%A8%ED%88%AC%EB%A7%A8/159/",
                "name": "후드/맨투맨",
                "param": "?cate_no=159",
                "cate_no": 159,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%8B%88%ED%8A%B8/44/",
                "name": "니트",
                "param": "?cate_no=44",
                "cate_no": 44,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EA%B8%B4%ED%8C%94/101/",
                "name": "긴팔",
                "param": "?cate_no=101",
                "cate_no": 101,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%ED%81%AC%EB%A1%AD/61/",
                "name": "크롭",
                "param": "?cate_no=61",
                "cate_no": 61,
                "parent_cate_no": 34,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=178",
        "name": "PANTS",
        "param": "?cate_no=178",
        "cate_no": 178,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EB%B2%84%EB%AE%A4%EB%8B%A4%ED%8C%AC%EC%B8%A0%EB%B0%98%EB%B0%94%EC%A7%80/197/",
                "name": "버뮤다팬츠&반바지",
                "param": "?cate_no=197",
                "cate_no": 197,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%A6%B0%EB%84%A8%ED%8C%AC%EC%B8%A0/546/",
                "name": "린넨팬츠",
                "param": "?cate_no=546",
                "cate_no": 546,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%8D%B0%EB%8B%98%EC%BD%94%ED%8A%BC/179/",
                "name": "데님&코튼",
                "param": "?cate_no=179",
                "cate_no": 179,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%82%98%EC%9D%BC%EB%A1%A0%ED%8C%AC%EC%B8%A0/545/",
                "name": "나일론팬츠",
                "param": "?cate_no=545",
                "cate_no": 545,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%A1%B0%EA%B1%B0%ED%8C%AC%EC%B8%A0/182/",
                "name": "조거팬츠",
                "param": "?cate_no=182",
                "cate_no": 182,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%8A%AC%EB%9E%99%EC%8A%A4/181/",
                "name": "슬랙스",
                "param": "?cate_no=181",
                "cate_no": 181,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B0%B4%EB%94%A9/206/",
                "name": "밴딩",
                "param": "?cate_no=206",
                "cate_no": 206,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B2%8C%EB%A3%AC/183/",
                "name": "벌룬",
                "param": "?cate_no=183",
                "cate_no": 183,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/160cm/184/",
                "name": "160cm↑",
                "param": "?cate_no=184",
                "cate_no": 184,
                "parent_cate_no": 178,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=33",
        "name": "OUTER",
        "param": "?cate_no=33",
        "cate_no": 33,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%F0%9F%A4%8D%EB%B0%94%EB%9E%8C%EB%A7%89%EC%9D%B4/465/",
                "name": "🤍바람막이",
                "param": "?cate_no=465",
                "cate_no": 465,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%F0%9F%8D%80%EC%97%AC%EB%A6%84%EA%B0%80%EB%94%94%EA%B1%B4/62/",
                "name": "🍀여름가디건",
                "param": "?cate_no=62",
                "cate_no": 62,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%A0%90%ED%8D%BC/100/",
                "name": "점퍼",
                "param": "?cate_no=100",
                "cate_no": 100,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%9E%90%EC%BC%93/40/",
                "name": "자켓",
                "param": "?cate_no=40",
                "cate_no": 40,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B2%A0%EC%8A%A4%ED%8A%B8%EC%A1%B0%EB%81%BC/466/",
                "name": "베스트/조끼",
                "param": "?cate_no=466",
                "cate_no": 466,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%BD%94%ED%8A%B8/41/",
                "name": "코트",
                "param": "?cate_no=41",
                "cate_no": 41,
                "parent_cate_no": 33,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=177",
        "name": "SKIRT",
        "param": "?cate_no=177",
        "cate_no": 177,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EB%A1%B1%EC%8A%A4%EC%BB%A4%ED%8A%B8/432/",
                "name": "롱스커트",
                "param": "?cate_no=432",
                "cate_no": 432,
                "parent_cate_no": 177,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%AF%B8%EB%94%94%EB%AF%B8%EB%8B%88%EC%8A%A4%EC%BB%A4%ED%8A%B8/433/",
                "name": "미디&미니스커트",
                "param": "?cate_no=433",
                "cate_no": 433,
                "parent_cate_no": 177,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=36",
        "name": "DRESS",
        "param": "?cate_no=36",
        "cate_no": 36,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EA%B8%B4%ED%8C%94/160/",
                "name": "긴팔",
                "param": "?cate_no=160",
                "cate_no": 160,
                "parent_cate_no": 36,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%8A%AC%EB%A6%AC%EB%B8%8C%EB%A6%AC%EC%8A%A4/162/",
                "name": "슬리브리스",
                "param": "?cate_no=162",
                "cate_no": 162,
                "parent_cate_no": 36,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B0%98%ED%8C%94/161/",
                "name": "반팔",
                "param": "?cate_no=161",
                "cate_no": 161,
                "parent_cate_no": 36,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=37",
        "name": "ACC",
        "param": "?cate_no=37",
        "cate_no": 37,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EB%B2%A8%ED%8A%B8/47/",
                "name": "벨트",
                "param": "?cate_no=47",
                "cate_no": 47,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EA%B0%80%EB%B0%A9/50/",
                "name": "가방",
                "param": "?cate_no=50",
                "cate_no": 50,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%8B%A0%EB%B0%9C/76/",
                "name": "신발",
                "param": "?cate_no=76",
                "cate_no": 76,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%AA%A8%EC%9E%90%ED%97%A4%EC%96%B4%EC%95%85%EC%84%B8%EC%84%9C%EB%A6%AC/48/",
                "name": "모자/헤어악세서리",
                "param": "?cate_no=48",
                "cate_no": 48,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%A5%AC%EC%96%BC%EB%A6%AC/106/",
                "name": "쥬얼리",
                "param": "?cate_no=106",
                "cate_no": 106,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%9E%A5%EA%B0%91%EB%A8%B8%ED%94%8C%EB%9F%AC/107/",
                "name": "장갑/머플러",
                "param": "?cate_no=107",
                "cate_no": 107,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EA%B8%B0%ED%83%80/51/",
                "name": "기타",
                "param": "?cate_no=51",
                "cate_no": 51,
                "parent_cate_no": 37,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=57",
        "name": "오늘출발",
        "param": "?cate_no=57",
        "cate_no": 57,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EC%83%81%EC%9D%98/164/",
                "name": "상의",
                "param": "?cate_no=164",
                "cate_no": 164,
                "parent_cate_no": 57,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%ED%95%98%EC%9D%98/165/",
                "name": "하의",
                "param": "?cate_no=165",
                "cate_no": 165,
                "parent_cate_no": 57,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=38",
        "name": "LAST CHANCE!",
        "param": "?cate_no=38",
        "cate_no": 38,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/10/144/",
                "name": "10%",
                "param": "?cate_no=144",
                "cate_no": 144,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/15/544/",
                "name": "15%",
                "param": "?cate_no=544",
                "cate_no": 544,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/20/146/",
                "name": "20%",
                "param": "?cate_no=146",
                "cate_no": 146,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/25/563/",
                "name": "25%",
                "param": "?cate_no=563",
                "cate_no": 563,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/30/147/",
                "name": "30%",
                "param": "?cate_no=147",
                "cate_no": 147,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/35/582/",
                "name": "35%",
                "param": "?cate_no=582",
                "cate_no": 582,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/40/148/",
                "name": "40%",
                "param": "?cate_no=148",
                "cate_no": 148,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/50/149/",
                "name": "50%",
                "param": "?cate_no=149",
                "cate_no": 149,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/60/185/",
                "name": "60%",
                "param": "?cate_no=185",
                "cate_no": 185,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/70/186/",
                "name": "70%",
                "param": "?cate_no=186",
                "cate_no": 186,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%83%98%ED%94%8C%EC%84%B8%EC%9D%BC/657/",
                "name": "샘플세일",
                "param": "?cate_no=657",
                "cate_no": 657,
                "parent_cate_no": 38,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/list.html?cate_no=54",
        "name": "UNISEX",
        "param": "?cate_no=54",
        "cate_no": 54,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EC%95%84%EC%9A%B0%ED%84%B0/111/",
                "name": "아우터",
                "param": "?cate_no=111",
                "cate_no": 111,
                "parent_cate_no": 54,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%83%81%EC%9D%98/112/",
                "name": "상의",
                "param": "?cate_no=112",
                "cate_no": 112,
                "parent_cate_no": 54,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EB%B0%94%EC%A7%80/113/",
                "name": "바지",
                "param": "?cate_no=113",
                "cate_no": 113,
                "parent_cate_no": 54,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/product/boy.html?cate_no=122",
        "name": "BOY",
        "param": "?cate_no=122",
        "cate_no": 122,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://ba-on.com/category/%EC%95%84%EC%9A%B0%ED%84%B0/124/",
                "name": "아우터",
                "param": "?cate_no=124",
                "cate_no": 124,
                "parent_cate_no": 122,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%83%81%EC%9D%98/125/",
                "name": "상의",
                "param": "?cate_no=125",
                "cate_no": 125,
                "parent_cate_no": 122,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%ED%95%98%EC%9D%98/127/",
                "name": "하의",
                "param": "?cate_no=127",
                "cate_no": 127,
                "parent_cate_no": 122,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://ba-on.com/category/%EC%95%85%EC%84%B8%EC%84%9C%EB%A6%AC/134/",
                "name": "악세서리",
                "param": "?cate_no=134",
                "cate_no": 134,
                "parent_cate_no": 122,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://ba-on.com/collection.html",
        "name": "COLLECTION",
        "param": "?cate_no=1",
        "cate_no": 1,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    }
]

//https://beidelli.com
const testJson_x4 = [
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=240",
        "name": "🏷Bellide",
        "param": "?cate_no=240",
        "cate_no": 240,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EC%95%84%EC%9A%B0%ED%84%B0/257/",
                "name": "아우터",
                "param": "?cate_no=257",
                "cate_no": 257,
                "parent_cate_no": 240,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%83%81%EC%9D%98/259/",
                "name": "상의",
                "param": "?cate_no=259",
                "cate_no": 259,
                "parent_cate_no": 240,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%95%98%EC%9D%98/260/",
                "name": "하의",
                "param": "?cate_no=260",
                "cate_no": 260,
                "parent_cate_no": 240,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%84%B8%ED%8A%B8%EC%9B%90%ED%94%BC%EC%8A%A4/261/",
                "name": "세트/원피스",
                "param": "?cate_no=261",
                "cate_no": 261,
                "parent_cate_no": 240,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/acc/303/",
                "name": "ACC",
                "param": "?cate_no=303",
                "cate_no": 303,
                "parent_cate_no": 240,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=24",
        "name": "BEST",
        "param": "?cate_no=24",
        "cate_no": 24,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=61",
        "name": "당일출고",
        "param": "?cate_no=61",
        "cate_no": 61,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/top/103/",
                "name": "TOP",
                "param": "?cate_no=103",
                "cate_no": 103,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/outer/105/",
                "name": "OUTER",
                "param": "?cate_no=105",
                "cate_no": 105,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/pants/107/",
                "name": "PANTS",
                "param": "?cate_no=107",
                "cate_no": 107,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/skirt/109/",
                "name": "SKIRT",
                "param": "?cate_no=109",
                "cate_no": 109,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/opsset/110/",
                "name": "OPS/SET",
                "param": "?cate_no=110",
                "cate_no": 110,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/acc/111/",
                "name": "ACC",
                "param": "?cate_no=111",
                "cate_no": 111,
                "parent_cate_no": 61,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=59",
        "name": "ALL ITEM",
        "param": "?cate_no=59",
        "cate_no": 59,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=192",
        "name": "Summer🩵",
        "param": "?cate_no=192",
        "cate_no": 192,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=26",
        "name": "OUTER",
        "param": "?cate_no=26",
        "cate_no": 26,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EB%B0%94%EB%9E%8C%EB%A7%89%EC%9D%B4/68/",
                "name": "바람막이",
                "param": "?cate_no=68",
                "cate_no": 68,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EA%B0%80%EB%94%94%EA%B1%B4/64/",
                "name": "가디건",
                "param": "?cate_no=64",
                "cate_no": 64,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%A7%91%EC%97%85%ED%9B%84%EB%93%9C%EC%A7%91%EC%97%85/67/",
                "name": "집업/후드집업",
                "param": "?cate_no=67",
                "cate_no": 67,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%9E%90%EC%BC%93%EC%A0%90%ED%8D%BC/65/",
                "name": "자켓/점퍼",
                "param": "?cate_no=65",
                "cate_no": 65,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%BD%94%ED%8A%B8/66/",
                "name": "코트",
                "param": "?cate_no=66",
                "cate_no": 66,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%8C%A8%EB%94%A9/69/",
                "name": "패딩",
                "param": "?cate_no=69",
                "cate_no": 69,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=320",
        "name": "TOP",
        "param": "?cate_no=320",
        "cate_no": 320,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EB%82%98%EC%8B%9C%EC%8A%AC%EB%A6%AC%EB%B8%8C%EB%A6%AC%EC%8A%A4/324/",
                "name": "나시/슬리브리스",
                "param": "?cate_no=324",
                "cate_no": 324,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%8B%B0%EC%85%94%EC%B8%A0/323/",
                "name": "티셔츠",
                "param": "?cate_no=323",
                "cate_no": 323,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%85%94%EC%B8%A0%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/327/",
                "name": "셔츠/블라우스",
                "param": "?cate_no=327",
                "cate_no": 327,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EB%8B%88%ED%8A%B8/322/",
                "name": "니트",
                "param": "?cate_no=322",
                "cate_no": 322,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EB%A7%A8%ED%88%AC%EB%A7%A8/325/",
                "name": "맨투맨",
                "param": "?cate_no=325",
                "cate_no": 325,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%9B%84%EB%93%9C%ED%8B%B0/326/",
                "name": "후드티",
                "param": "?cate_no=326",
                "cate_no": 326,
                "parent_cate_no": 320,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=28",
        "name": "PANTS",
        "param": "?cate_no=28",
        "cate_no": 28,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EC%88%8F%ED%8C%AC%EC%B8%A0/70/",
                "name": "숏팬츠",
                "param": "?cate_no=70",
                "cate_no": 70,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EB%8D%B0%EB%8B%98%ED%8C%AC%EC%B8%A0/49/",
                "name": "데님팬츠",
                "param": "?cate_no=49",
                "cate_no": 49,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D%ED%8C%AC%EC%B8%A0/71/",
                "name": "트레이닝팬츠",
                "param": "?cate_no=71",
                "cate_no": 71,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%8A%AC%EB%9E%99%EC%8A%A4/72/",
                "name": "슬랙스",
                "param": "?cate_no=72",
                "cate_no": 72,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EA%B2%A8%EC%9A%B8%ED%8C%AC%EC%B8%A0%EA%B8%B0%EB%AA%A8%EB%AA%A8%EC%A7%81/184/",
                "name": "겨울팬츠(기모,모직)",
                "param": "?cate_no=184",
                "cate_no": 184,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=48",
        "name": "SKIRT",
        "param": "?cate_no=48",
        "cate_no": 48,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EC%88%8F/265/",
                "name": "숏",
                "param": "?cate_no=265",
                "cate_no": 265,
                "parent_cate_no": 48,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EB%A1%B1/268/",
                "name": "롱",
                "param": "?cate_no=268",
                "cate_no": 268,
                "parent_cate_no": 48,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=42",
        "name": "OPS/SET",
        "param": "?cate_no=42",
        "cate_no": 42,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EC%9B%90%ED%94%BC%EC%8A%A4/63/",
                "name": "원피스",
                "param": "?cate_no=63",
                "cate_no": 63,
                "parent_cate_no": 42,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%88%AC%ED%94%BC%EC%8A%A4/62/",
                "name": "투피스",
                "param": "?cate_no=62",
                "cate_no": 62,
                "parent_cate_no": 42,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://beidelli.com/product/list.html?cate_no=43",
        "name": "ACC",
        "param": "?cate_no=43",
        "cate_no": 43,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://beidelli.com/category/%EA%B0%80%EB%B0%A9/46/",
                "name": "가방",
                "param": "?cate_no=46",
                "cate_no": 46,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%8B%A0%EB%B0%9C/53/",
                "name": "신발",
                "param": "?cate_no=53",
                "cate_no": 53,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EC%A5%AC%EC%96%BC%EB%A6%AC/60/",
                "name": "쥬얼리",
                "param": "?cate_no=60",
                "cate_no": 60,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%ED%97%A4%EC%96%B4/95/",
                "name": "헤어",
                "param": "?cate_no=95",
                "cate_no": 95,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EB%A8%B8%ED%94%8C%EB%9F%AC/97/",
                "name": "머플러",
                "param": "?cate_no=97",
                "cate_no": 97,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://beidelli.com/category/%EA%B8%B0%ED%83%80/76/",
                "name": "기타",
                "param": "?cate_no=76",
                "cate_no": 76,
                "parent_cate_no": 43,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    }
]

//https://dailyjou.com
const testJson = [
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=214",
        "name": "바캉스룩🌊🌴",
        "param": "?cate_no=214",
        "cate_no": 214,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=24",
        "name": "NEW 5% + 앱쿠폰 10%",
        "param": "?cate_no=24",
        "cate_no": 24,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=50",
        "name": "BEST",
        "param": "?cate_no=50",
        "cate_no": 50,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=86",
        "name": "D,CHIVE",
        "param": "?cate_no=86",
        "cate_no": 86,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/bottom/122/",
                "name": "BOTTOM",
                "param": "?cate_no=122",
                "cate_no": 122,
                "parent_cate_no": 86,
                "design_page_url": "product/list.html",
                "data_list": [
                    {
                        "link_product_list": "https://dailyjou.com/category/%EB%8D%B0%EB%8B%98/229/",
                        "name": "데님 ()",
                        "param": "?cate_no=229",
                        "cate_no": 229,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D/230/",
                        "name": "트레이닝 ()",
                        "param": "?cate_no=230",
                        "cate_no": 230,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%BD%94%ED%8A%BC/231/",
                        "name": "코튼 ()",
                        "param": "?cate_no=231",
                        "cate_no": 231,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%8A%AC%EB%9E%99%EC%8A%A4/232/",
                        "name": "슬랙스 ()",
                        "param": "?cate_no=232",
                        "cate_no": 232,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%87%BC%EC%B8%A0/233/",
                        "name": "쇼츠 ()",
                        "param": "?cate_no=233",
                        "cate_no": 233,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/etc/234/",
                        "name": "etc. ()",
                        "param": "?cate_no=234",
                        "cate_no": 234,
                        "parent_cate_no": 122,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    }
                ]
            },
            {
                "link_product_list": "https://dailyjou.com/category/top/123/",
                "name": "TOP",
                "param": "?cate_no=123",
                "cate_no": 123,
                "parent_cate_no": 86,
                "design_page_url": "product/list.html",
                "data_list": [
                    {
                        "link_product_list": "https://dailyjou.com/category/%ED%8B%B0%EC%85%94%EC%B8%A0/235/",
                        "name": "티셔츠 ()",
                        "param": "?cate_no=235",
                        "cate_no": 235,
                        "parent_cate_no": 123,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%8A%AC%EB%A6%AC%EB%B8%8C%EB%A6%AC%EC%8A%A4/239/",
                        "name": "슬리브리스 ()",
                        "param": "?cate_no=239",
                        "cate_no": 239,
                        "parent_cate_no": 123,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%85%94%EC%B8%A0%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/236/",
                        "name": "셔츠/블라우스 ()",
                        "param": "?cate_no=236",
                        "cate_no": 236,
                        "parent_cate_no": 123,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EB%8B%88%ED%8A%B8/237/",
                        "name": "니트 ()",
                        "param": "?cate_no=237",
                        "cate_no": 237,
                        "parent_cate_no": 123,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EB%A7%A8%ED%88%AC%EB%A7%A8%ED%9B%84%EB%93%9C/238/",
                        "name": "맨투맨/후드 ()",
                        "param": "?cate_no=238",
                        "cate_no": 238,
                        "parent_cate_no": 123,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    }
                ]
            },
            {
                "link_product_list": "https://dailyjou.com/category/outer/121/",
                "name": "OUTER",
                "param": "?cate_no=121",
                "cate_no": 121,
                "parent_cate_no": 86,
                "design_page_url": "product/list.html",
                "data_list": [
                    {
                        "link_product_list": "https://dailyjou.com/category/%EA%B0%80%EB%94%94%EA%B1%B4/240/",
                        "name": "가디건 ()",
                        "param": "?cate_no=240",
                        "cate_no": 240,
                        "parent_cate_no": 121,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%A0%90%ED%8D%BC/241/",
                        "name": "점퍼 ()",
                        "param": "?cate_no=241",
                        "cate_no": 241,
                        "parent_cate_no": 121,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%9E%90%EC%BC%93%EC%BD%94%ED%8A%B8/242/",
                        "name": "자켓/코트 ()",
                        "param": "?cate_no=242",
                        "cate_no": 242,
                        "parent_cate_no": 121,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    }
                ]
            },
            {
                "link_product_list": "https://dailyjou.com/category/dressskirt/124/",
                "name": "DRESS&SKIRT",
                "param": "?cate_no=124",
                "cate_no": 124,
                "parent_cate_no": 86,
                "design_page_url": "product/list.html",
                "data_list": [
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%8A%A4%EC%BB%A4%ED%8A%B8/243/",
                        "name": "스커트 ()",
                        "param": "?cate_no=243",
                        "cate_no": 243,
                        "parent_cate_no": 124,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    },
                    {
                        "link_product_list": "https://dailyjou.com/category/%EC%9B%90%ED%94%BC%EC%8A%A4/244/",
                        "name": "원피스 ()",
                        "param": "?cate_no=244",
                        "cate_no": 244,
                        "parent_cate_no": 124,
                        "design_page_url": "product/list.html",
                        "data_list": []
                    }
                ]
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=26",
        "name": "TOP",
        "param": "?cate_no=26",
        "cate_no": 26,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%ED%8B%B0%EC%85%94%EC%B8%A0/46/",
                "name": "티셔츠",
                "param": "?cate_no=46",
                "cate_no": 46,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%85%94%EC%B8%A0/51/",
                "name": "셔츠",
                "param": "?cate_no=51",
                "cate_no": 51,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EB%B8%94%EB%9D%BC%EC%9A%B0%EC%8A%A4/47/",
                "name": "블라우스",
                "param": "?cate_no=47",
                "cate_no": 47,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%8A%AC%EB%A6%AC%EB%B8%8C%EB%A6%AC%EC%8A%A4/166/",
                "name": "슬리브리스",
                "param": "?cate_no=166",
                "cate_no": 166,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EB%8B%88%ED%8A%B8/55/",
                "name": "니트",
                "param": "?cate_no=55",
                "cate_no": 55,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EB%A7%A8%ED%88%AC%EB%A7%A8%ED%9B%84%EB%93%9C/89/",
                "name": "맨투맨/후드",
                "param": "?cate_no=89",
                "cate_no": 89,
                "parent_cate_no": 26,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=27",
        "name": "BOTTOM",
        "param": "?cate_no=27",
        "cate_no": 27,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%EB%8D%B0%EB%8B%98/148/",
                "name": "데님",
                "param": "?cate_no=148",
                "cate_no": 148,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%ED%8A%B8%EB%A0%88%EC%9D%B4%EB%8B%9D/150/",
                "name": "트레이닝",
                "param": "?cate_no=150",
                "cate_no": 150,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%BD%94%ED%8A%BC/82/",
                "name": "코튼",
                "param": "?cate_no=82",
                "cate_no": 82,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%8A%AC%EB%9E%99%EC%8A%A4/84/",
                "name": "슬랙스",
                "param": "?cate_no=84",
                "cate_no": 84,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%87%BC%EC%B8%A0/85/",
                "name": "쇼츠",
                "param": "?cate_no=85",
                "cate_no": 85,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/etc/245/",
                "name": "etc.",
                "param": "?cate_no=245",
                "cate_no": 245,
                "parent_cate_no": 27,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=25",
        "name": "OUTER",
        "param": "?cate_no=25",
        "cate_no": 25,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%EA%B0%80%EB%94%94%EA%B1%B4/44/",
                "name": "가디건",
                "param": "?cate_no=44",
                "cate_no": 44,
                "parent_cate_no": 25,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%A0%90%ED%8D%BC/45/",
                "name": "점퍼",
                "param": "?cate_no=45",
                "cate_no": 45,
                "parent_cate_no": 25,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%9E%90%EC%BC%93/53/",
                "name": "자켓",
                "param": "?cate_no=53",
                "cate_no": 53,
                "parent_cate_no": 25,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%BD%94%ED%8A%B8/52/",
                "name": "코트",
                "param": "?cate_no=52",
                "cate_no": 52,
                "parent_cate_no": 25,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=28",
        "name": "DRESS&SKIRT",
        "param": "?cate_no=28",
        "cate_no": 28,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%EC%8A%A4%EC%BB%A4%ED%8A%B8/48/",
                "name": "스커트",
                "param": "?cate_no=48",
                "cate_no": 48,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%9B%90%ED%94%BC%EC%8A%A4/80/",
                "name": "원피스",
                "param": "?cate_no=80",
                "cate_no": 80,
                "parent_cate_no": 28,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=220",
        "name": "BAG & SHOES",
        "param": "?cate_no=220",
        "cate_no": 220,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%EB%B0%B1/221/",
                "name": "백",
                "param": "?cate_no=221",
                "cate_no": 221,
                "parent_cate_no": 220,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%8A%88%EC%A6%88/222/",
                "name": "슈즈",
                "param": "?cate_no=222",
                "cate_no": 222,
                "parent_cate_no": 220,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=67",
        "name": "ACC",
        "param": "?cate_no=67",
        "cate_no": 67,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/%EB%AA%A8%EC%9E%90%ED%97%A4%EC%96%B4/223/",
                "name": "모자/헤어",
                "param": "?cate_no=223",
                "cate_no": 223,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EB%B2%A8%ED%8A%B8/224/",
                "name": "벨트",
                "param": "?cate_no=224",
                "cate_no": 224,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EB%A8%B8%ED%94%8C%EB%9F%AC%EC%9E%A5%EA%B0%91/226/",
                "name": "머플러/장갑",
                "param": "?cate_no=226",
                "cate_no": 226,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%96%91%EB%A7%90%EC%8A%A4%ED%83%80%ED%82%B9/225/",
                "name": "양말/스타킹",
                "param": "?cate_no=225",
                "cate_no": 225,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%95%88%EA%B2%BD%EC%84%A0%EA%B8%80%EB%9D%BC%EC%8A%A4/227/",
                "name": "안경/선글라스",
                "param": "?cate_no=227",
                "cate_no": 227,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%A3%BC%EC%96%BC%EB%A6%AC/99/",
                "name": "주얼리",
                "param": "?cate_no=99",
                "cate_no": 99,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%9D%B4%EB%84%88%EC%9B%A8%EC%96%B4/138/",
                "name": "이너웨어",
                "param": "?cate_no=138",
                "cate_no": 138,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/%EC%8A%A4%EC%9C%94%EC%9B%A8%EC%96%B4/164/",
                "name": "스윔웨어",
                "param": "?cate_no=164",
                "cate_no": 164,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/etc/228/",
                "name": "etc.",
                "param": "?cate_no=228",
                "cate_no": 228,
                "parent_cate_no": 67,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=91",
        "name": "오늘출발🚚",
        "param": "?cate_no=91",
        "cate_no": 91,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/outer/101/",
                "name": "OUTER",
                "param": "?cate_no=101",
                "cate_no": 101,
                "parent_cate_no": 91,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/top/102/",
                "name": "TOP",
                "param": "?cate_no=102",
                "cate_no": 102,
                "parent_cate_no": 91,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/bottom/103/",
                "name": "BOTTOM",
                "param": "?cate_no=103",
                "cate_no": 103,
                "parent_cate_no": 91,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/dressskirt/104/",
                "name": "DRESS&SKIRT",
                "param": "?cate_no=104",
                "cate_no": 104,
                "parent_cate_no": 91,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/acc/105/",
                "name": "ACC",
                "param": "?cate_no=105",
                "cate_no": 105,
                "parent_cate_no": 91,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=168",
        "name": "RESTOCK 10%할인",
        "param": "?cate_no=168",
        "cate_no": 168,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=73",
        "name": "UNISEX",
        "param": "?cate_no=73",
        "cate_no": 73,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": [
            {
                "link_product_list": "https://dailyjou.com/category/outer/158/",
                "name": "OUTER",
                "param": "?cate_no=158",
                "cate_no": 158,
                "parent_cate_no": 73,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/top/160/",
                "name": "TOP",
                "param": "?cate_no=160",
                "cate_no": 160,
                "parent_cate_no": 73,
                "design_page_url": "product/list.html",
                "data_list": []
            },
            {
                "link_product_list": "https://dailyjou.com/category/bottoms/161/",
                "name": "BOTTOMS",
                "param": "?cate_no=161",
                "cate_no": 161,
                "parent_cate_no": 73,
                "design_page_url": "product/list.html",
                "data_list": []
            }
        ]
    },
    {
        "link_product_list": "https://dailyjou.com/product/list.html?cate_no=146",
        "name": "SET",
        "param": "?cate_no=146",
        "cate_no": 146,
        "parent_cate_no": 1,
        "design_page_url": "product/list.html",
        "data_list": []
    }
];