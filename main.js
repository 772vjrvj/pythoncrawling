const puppeteer = require('puppeteer');
const xlsx = require('xlsx');

async function setupBrowser() {
    const browser = await puppeteer.launch({
        headless: false, // 브라우저가 백그라운드에서 실행되지 않도록 설정 (디버깅용)
        args: [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--incognito',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });
    return { browser, page };
}

async function getCategoryLinks(page) {
    await page.goto('https://ba-on.com');
    await page.waitForSelector('.xans-element-.xans-layout.xans-layout-category');

    const categoryLinks = await page.evaluate(() => {
        const links = [];
        const items = document.querySelectorAll('.xans-element-.xans-layout.xans-layout-category li a');
        items.forEach(item => {
            const text = item.innerText;
            const url = item.href;
            links.push({ text, url });
        });
        return links;
    });
    return categoryLinks;
}

async function getPrdImgUrls(page) {
    const prdImgUrls = await page.evaluate(() => {
        const urls = [];
        const items = document.querySelectorAll('.prdList .prdImg a');
        items.forEach(item => {
            const url = item.href;
            urls.push(url);
        });
        return urls;
    });
    return prdImgUrls;
}

async function scrapeProductDetails(page, url, categoryText) {
    await page.goto(url);
    await page.waitForSelector('.xans-element-.xans-product.xans-product-image.imgArea img');

    const product = { 카테고리: categoryText };

    try {
        const imgSrc = await page.$eval('.xans-element-.xans-product.xans-product-image.imgArea img', img => img.src);
        product['상품 이미지'] = imgSrc;
    } catch (error) {
        product['상품 이미지'] = null;
    }

    try {
        const productName = await page.$eval('.product_info tbody tr td', td => td.innerText);
        product['상품 리스트'] = productName;
    } catch (error) {
        product['상품 리스트'] = null;
    }


    console.log(`Scraped product details: ${JSON.stringify(product)}`);
    return product;
}

async function main() {
    const { browser, page } = await setupBrowser();
    const allProducts = [];

    try {
        const categoryLinks = await getCategoryLinks(page);

        for (let i = 0; i < Math.min(categoryLinks.length, 3); i++) {
            const category = categoryLinks[i];
            console.log(`Scraping category: ${category.text}`);
            await page.goto(category.url);

            const imgUrls = await getPrdImgUrls(page);
            console.log(`Collected ${imgUrls.length} image URLs from ${category.text}`);

            for (let j = 0; j < Math.min(imgUrls.length, 3); j++) {
                const imgUrl = imgUrls[j];
                const product = await scrapeProductDetails(page, imgUrl, category.text);
                allProducts.push(product);
            }
        }

    } catch (error) {
        console.error(`An error occurred: ${error.message}`);
    } finally {
        await browser.close();
    }

    const worksheet = xlsx.utils.json_to_sheet(allProducts);
    const workbook = xlsx.utils.book_new();
    xlsx.utils.book_append_sheet(workbook, worksheet, 'Products');
    xlsx.writeFile(workbook, 'products.xlsx');

    console.log('Data saved to products.xlsx');
}

main();
