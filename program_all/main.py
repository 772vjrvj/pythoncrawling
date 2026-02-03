import re
import httpx

URL = "https://457deep.com/essay/detail/cmh4emar4000w1ej30ijip692"

HEADERS = {
    "rsc": "1",
    "user-agent": "Mozilla/5.0",
}

def extract_19_html(text: str):

    pattern = re.compile(
        r'19:[A-Za-z0-9]{4},(.*?)(?=\n?[0-9a-f]+:|$)',
        re.DOTALL
    )

    return pattern.findall(text)


def main():

    with httpx.Client(http2=True, headers=HEADERS, timeout=30) as client:
        r = client.get(URL)
        r.raise_for_status()

        t = r.text

    html_chunks = extract_19_html(t)

    print("count:", len(html_chunks))

    full_html = "\n".join(html_chunks)

    print(full_html[:3000])


if __name__ == "__main__":
    main()
