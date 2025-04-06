SELECT DISTINCT WEBSITE FROM PRODUCT_INFO;

SELECT * FROM PRODUCT_INFO
WHERE 1=1
# AND WEBSITE = 'ARITZIA'
AND SUCCESS = 'N';

SELECT * FROM PRODUCT_INFO WHERE PRODUCT_ID LIKE '27217154%';

SELECT COUNT(*) FROM PRODUCT_INFO WHERE WEBSITE = 'ARITZIA';


# ARITZIA
# FARFETCH
# H&M
# BANANAREPUBLIC
# &OTHER STORIES
# MANGO
# ZARA


# 데이터 보정 2025-04-07
# 87095762_99_01
# https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/short-flared-knitted-dress_87095762?l=01
#
# 448282189
# https://www.zara.com/us/en/wool-blend-blazer-zw-collection-p03178499.html
#
# 27217154
# https://www.farfetch.com/shopping/women/toteme-wool-cape-item-27217154.aspx?storeid=16046