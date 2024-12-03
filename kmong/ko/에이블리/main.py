import requests
import json

def fetch_data(url, headers):
    """
    Fetch data from the specified URL using the given headers.

    Args:
        url (str): The API endpoint URL.
        headers (dict): The HTTP headers to include in the request.

    Returns:
        dict: The JSON response parsed as a Python dictionary.
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return {}

def main():
    # URL and headers
    url = "https://api.a-bly.com/api/v2/screens/TODAY/?next_token=eyJsaSI6IDcsICJuIjogImV5SnNZWE4wWDJsdVpHVjRJam9nTmpOOSJ9"
    headers = {
        "authority": "api.a-bly.com",
        "method": "GET",
        "path": "/api/v2/screens/TODAY/?next_token=eyJsaSI6IDcsICJuIjogImV5SnNZWE4wWDJsdVpHVjRJam9nTmpOOSJ9",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://m.a-bly.com",
        "priority": "u=1, i",
        "referer": "https://m.a-bly.com/",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-anonymous-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbm9ueW1vdXNfaWQiOiIzMjY3ODUyNTciLCJpYXQiOjE3MzI4NzY5MjJ9.xjUifIyjMaCQtfVjMKTGhuJ7RWgZQFbnKWvYKAUlQt4",
        "x-app-version": "0.1.0",
        "x-device-id": "44ce1c2f-38b7-48c1-8228-d945be0cc9fa",
        "x-device-type": "PCWeb",
        "x-web-type": "Web"
    }

    # Fetch and print the data
    data = fetch_data(url, headers)
    print(json.dumps(data, indent=4, ensure_ascii=False))  # Pretty print the JSON response

if __name__ == "__main__":
    main()
