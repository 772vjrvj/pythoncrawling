const axios = require('axios');

async function fetchReviews() {
    const url = 'https://sfre-srcs-service.snapfit.co.kr/Dataupdate/GetReview';
    const payload = {
        widgetid: 3,
        platform: 'pc',
        Sea: 'kmQ9oJlN%2By072qNIzynOr%2FqPQn8Mau0Shst7ptOudjPI5H4LMyXfKDAcAnVMQJ4KXelTccJSqc6AJWtFsf8CCqsPQaE3hsemvmXRfI5nn6ZAYNh8o8d%2BPbQxjalpvRjCiqWU%2BBYajMD2pQBoLBc5gMtGB0HeHE9YQZEuilBowFj1wEQAovDl3BJhTouJWbkkN1Kt5RoIcK7FwW7IWZl1ww%3D%3D',
        store_username: 'hIA%2BwUdvRpaULjOCEIDsoA%3D%3D',
        item_id: 3420, //제품 아이디
        from: 1
    };

    try {
        const response = await axios.post(url, new URLSearchParams(payload));
        console.log(JSON.stringify(response.data.data.reviewinfo.review, null, 2));
    } catch (error) {
        console.error('Error:', error.response ? error.response.data : error.message);
    }
}

fetchReviews();
