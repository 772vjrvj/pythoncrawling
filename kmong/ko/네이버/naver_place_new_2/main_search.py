import requests


def fetch_search_results(query, page):
    try:
        url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord=&boundary=&page={page}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Referer': '',
            'Cookie': 'NAC=OsXJBQA7C4Wj; NNB=FOXBS434SDKGM; ASID=da9384ec00000191d00facf700000072; NFS=2; NACT=1; nid_inf=391290400; NID_AUT=BKWCh2nwSx87OqhQiU7fA53ABVeIM0NVMvSL50BLM9CsrtH2hS3M5nj4JkmZmLa5; NID_SES=AAABrK7oOJ3oxSpt990kiHxmKrg4harLTIhsTFL4RNy721y0kPWFyndoU2cAObU+KJUscFZV7gaVh8lMUyj/pIpfJPAb2Kt9Acnx2/0GP0qd95hsxnijuZU4yCTu+37rUwjcJoQI217JYznF8kRHVg9+yuCQJ4hDtP3/TSENNHeX4zw9RudCmqQoLp9HEUZjzmzRNII8lXg2c+XmDMg13hTxaFnF+6wDkb6dtzRGKK7VrV5bTPiL0/taU0rS3zytdz984pGZieeS74tG7KdSx+IO9WAQ8bNU99Vgk7QiQ4lA17VHmCtxHa1BXXsj3/hJG3J1S6/9WQjuxWqmGPnW2g0tHtcFMqqN0AaF9/fdEoFrY9YKJ3S8M06MyDSBqMuigP3mul7VFGM37qKxpnz/lvnDZ4SDNY32EKYnStMUssjPxr7pnuF+cGubpwM5DNK8/X4FewZRiOT6J1hUjGpPFOuq8hvCqOj1rqjHNcqlxziFSC42w4N/FoNEVn9SaAXvBh1L75nTcm3wXGMKzMxygVCZPc99dsO+XUhpbusDOlN62HGLNJwPteOhKo7ZyQb4k5YWXA==; NID_JKL=CNZkLlqEX2rtTV3YMO64OWCpmUjIqDGQwtQED8C+LlE=; BUC=50ImD0ovxSThrenHO4dcb-MPmonlTPAc0WgfuSDYqZk='
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch search results: {e}")
    return None


if __name__ == "__main__":

    result = fetch_search_results("강남 네일", 4)

    place_list = result.get("result", {}).get("place", {}).get("list", [])

    # ids_this_page = [place.get("id") for place in place_list if place.get("id")]

    for p in place_list:
        print(f'p : {p}')