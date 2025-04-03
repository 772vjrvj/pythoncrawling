# 전역 변수
SERVER_URL = "http://vjrvj.cafe24.com"

IMAGE_MAIN_DIRECTORY = 'images'

SITE_CONFIGS = {
    # "MYTHERESA": {
    #     "name": "MYTHERESA",
    #     "color": "#000",
    #     "check_list": ["Women", "Men", "Girls", "Boys", "Baby"]
    # },
    # "ZALANDO": {
    #     "name": "ZALANDO",
    #     "color": "#D2451E",
    #     "check_list": ["Women", "Men", "Girls", "Boys", "Baby"]
    # },
    # "OLDNAVY": {
    #     "name": "OLDNAVY",
    #     "color": "#000080",
    #     "check_list": [
    #         "Women / Women’s Tops / Shirts & Blouses",
    #         "Women / Women’s Tops / Button-down Shirts",
    #         "Women / Women’s Bottoms / Pants",
    #         "Women / Women’s Bottoms / Shorts",
    #         "Women / Women’s Bottoms / Skirts",
    #         "Women / Shop Women’s Categories / Dresses & Jumpsuits",
    #         "Now Trending!",
    #         "Activewear",
    #         "Women", "Men", "Girls", "Boys", "Toddler", "Baby", "Maternity"
    #     ]
    # },
    # "KOHLS": {
    #     "name": "KOHLS",
    #     "color": "#860035",
    #     "check_list": [
    #         "Women / Nine West",
    #         "Women / Sonoma",
    #         "Women / Croft",
    #         "Women / LC",
    #         "Women / SVVW"
    #     ]
    # },
    "ZARA": {
        "name": "ZARA",
        "color": "#000",
        "base_url": "https://www.zara.com/us/en",
        "check_list": {
            "WOMEN _ THE NEW": "/woman-new-in-l1180.html?v1=2546081",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
    },
    "MANGO": {
        "name": "MANGO",
        "color": "#000",
        "base_url": "https://shop.mango.com/us/en",
        "check_list": {
            "WOMEN _ NEW NOW": "/c/women/new-now_56b5c5ed",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
    },
    "FARFETCH": {
        "name": "FARFETCH",
        "color": "#222222",
        "base_url": "https://www.farfetch.com",
        "check_list": {
            "WOMEN _ ALC"             : "/shopping/women/alc/items.aspx?qst=2&qr=1&qt=A.L.C&ffref=Search%7C56aa959cb435923f339f01bef12634edb2713392401ca04867ff94d56e71566b%7C1%7C0%7C1%7C%7C",
            "WOMEN _ ANINE BING"      : "/shopping/women/anine-bing/items.aspx?qst=2&qr=1&qt=A.L.C.ANINE+BING&ffref=Search%7C5efbae3e672ea2d3b7d15ff0af7b0f6932efbcb614cd57c4d2214f101edd2931%7C1%7C0%7C1%7C%7C",
            "WOMEN _ KHAITE"          : "/shopping/women/khaite/items.aspx?qst=2&qr=1&ffref=Search%7Cdb11b7c3c6007e255b1271d62ba9a9f85f7e40d138d61786e4c837c22a3e63d0%7C1%7C0%7C1%7C%7C",
            "WOMEN _ THE FRANKIE SHOP": "/shopping/women/designer-the-frankie-shop/items.aspx?qst=2&qr=1&ffref=Search%7Ce695bcd1cd91aeb794767372407d81736e02a2b0c3cd5f9689a87e0b71728d9b%7C1%7C0%7C1%7C%7C",
            "WOMEN _ TIBI"            : "/shopping/women/tibi/items.aspx?qr=1&ffref=Search%7C03a4505b9e0a598227746e8b35e58e365b3971bb8ad321755af852c0bb39e13b%7C1%7C0%7C1%7C%7C",
            "WOMEN _ VINCE"           : "/shopping/women/vince/items.aspx?qst=2&qr=1&ffref=Search%7Cee3df1c03091b0735b369297debe1dda619e38b48ba9ca1518b80178a2efbc09%7C1%7C0%7C1%7C%7C",
            "WOMEN _ JONATHAN SIMKHAI": "/shopping/women/search/items.aspx?ffref=Search%7C55eb24ab0e623d710ea48780ab0b70dd960ff76d684af705cf55ba6d5e847854%7C1%7C0%7C1%7C%7C&qst=6&qr=3&q=JONATHAN+SIMKHAI",
            "WOMEN _ STAUD"           : "/shopping/women/staud/items.aspx?qr=1&ffref=Search%7C7a54ad307675ae959921c225eed2fe228c36e0836763e9f853533400bab03d00%7C1%7C0%7C1%7C%7C",
            "WOMEN _ NILI LOTAN"      : "/shopping/women/nili-lotan/items.aspx?ffref=Search%7C%7C%7C%7C%7C%7C&qr=1",
            "WOMEN _ JIL SANDER"      : "/shopping/women/jil-sander/items.aspx?qr=1&ffref=Search%7C4bad91c1b7048b919cdb3323a25688c00cd8b4c73a41d50a32993aa6dd4b2ed9%7C1%7C0%7C1%7C%7C",
            "WOMEN _ THEORY"          : "/shopping/women/theory/items.aspx?qst=2&qr=1&ffref=Search%7C3af7dcf29f6068e1fd60b155199332ec9390cb59eda0d6d8f6809452725f5a77%7C1%7C0%7C1%7C%7C",
            "WOMEN _ TOTEME"          : "/shopping/women/toteme/items.aspx?qr=1&qt=TOTEME&ffref=Search%7C89c45e18d9f193470a5842cc2f9168993170bba8b4273b8302a7497db398ae80%7C1%7C0%7C1%7C%7C",
            "WOMEN _ VERONICA BEARD"  : "/shopping/women/veronica-beard/items.aspx?qst=2&qr=1&ffref=Search%7C8e10dc5c56dd4f5b1f7e753a0a262229e8bc69c5eb1c147ec48c029b39579da8%7C1%7C0%7C1%7C%7C",
            "WOMEN _ MATTEAU"         : "/shopping/women/designer-matteau/items.aspx?qr=1&ffref=Search%7Cc7a2f5bf58d46ffed381440dbf3c57d424a718ca5ef67880099b8532e001f80d%7C1%7C0%7C1%7C%7C",
            "WOMEN _ ST. AGNI"        : "/shopping/women/designer-st.-agni/items.aspx",
            "WOMEN _ VANESSA BRUNO"   : "/shopping/women/search/items.aspx?q=VANESSA+BRUNO&ffref=Search%7C5ccd0fddacd0bf2c326917789590081b0f191fd67ef69adf8953d6b6a21fcbe7%7C1%7C0%7C1%7C%7C&qst=6&qr=3",
        },
        "brand_type": "Inspiration Brand",
        "country": "US"
    },
    "H&M": {
        "name": "H&M",
        "color": "#E4080A",
        "base_url": "https://www2.hm.com/en_us",
        "check_list": {
            "WOMEN _ NEW IN": "/women/new-arrivals/view-all.html",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
    },
    "&OTHER STORIES": {
        "name": "&OTHER STORIES",
        "color": "#CECECE",
        "base_url": "https://www.stories.com/en_usd",
        "check_list": {
            "WOMEN _ All New Arrivals": "/whats-new/all.html",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
   },
    "BANANAREPUBLIC": {
        "name": "BANANAREPUBLIC",
        "color": "#000",
        "base_url": "https://bananarepublic.gap.com",
        "check_list": {
            "WOMEN _ New Arrivals": "/browse/women/new-arrivals?cid=48422&nav=meganav%3AWomen%3ADiscover%3ANew%20Arrivals",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
    },
    "ARITZIA": {
        "name": "ARITZIA",
        "color": "#000",
        "base_url": "https://www.aritzia.com/intl/en",
        "check_list": {
            "WOMEN _ ALL NEW": "/new/all-new",
        },
        "brand_type": "Competitive Brand",
        "country": "US"
    },
}