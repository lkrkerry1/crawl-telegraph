import random
import re
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure a requests session with retries for transient errors
a_requests = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,  # type: ignore
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
a_requests.mount("https://", adapter)
a_requests.mount("http://", adapter)

user_agent = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
]


def get_headers():
    """Return a headers dict with a random User-Agent and fixed Referer.

    The function centralizes header construction so callers can reuse a
    consistent referer and rotate the user-agent for each request.

    Returns
    -------
    dict
        HTTP headers to pass to :mod:`requests`.
    """
    return {"User-Agent": random.choice(user_agent), "Referer": "https://telegra.ph/"}


def get_html_text(url: str, timeout: int = 10) -> str:
    """Fetch HTML text for ``url``.

    This function uses the session configured with a retry strategy, and
    raises an exception for non-2xx responses.

    Parameters
    ----------
    url:
        The page URL to fetch.
    timeout:
        Per-request timeout in seconds (passed to requests.get).

    Returns
    -------
    str
        The response body as text.

    Raises
    ------
    requests.RequestException
        If the request fails after retries or a bad HTTP status is
        returned.
    """
    headers = get_headers()
    resp = a_requests.get(url=url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def get_image_src(html_text: str):
    """Extract image src attribute values from the HTML text.

    Parameters
    ----------
    html_text:
        HTML content as a string.

    Returns
    -------
    list[str]
        A list of src attribute values (may be relative paths starting with
        "/file/...").
    """
    return re.findall(r'img src="(\S+)"', html_text)


def get_image_url_name(img_info):
    """Convert raw image src paths into structured info dicts.

    Each returned dict has keys: ``name`` (file name), ``url`` (absolute
    URL) and ``id`` (sequential index).
    """
    info = []
    for id, i in enumerate(img_info):
        # 如果 i 已经是完整的 URL（http:// 或 https://），直接使用；否则添加 telegra.ph 前缀
        if i.startswith("http://") or i.startswith("https://"):
            url = i
            name = i.split("/")[-1]  # 从 URL 中提取文件名
        else:
            url = "https://telegra.ph" + i
            name = i.replace("/file/", "")
        info.append({"name": name, "url": url, "id": id})
    return info


def get_image_content(url: str, timeout: int = 20) -> bytes:
    """Download image bytes for the given absolute URL.

    Parameters
    ----------
    url:
        Absolute image URL (e.g. https://telegra.ph/file/abc.jpg).
    timeout:
        Per-request timeout in seconds.

    Returns
    -------
    bytes
        Raw response content.

    Raises
    ------
    requests.RequestException
        For network errors or non-2xx responses.
    """
    headers = get_headers()
    resp = a_requests.get(url=url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def get_image_info(url: str):
    """Return a list of image info dicts for a telegra.ph page.

    The function fetches the page HTML and parses image src values then
    converts them to the standardized info dict format used by
    :mod:`main`.
    """
    html = get_html_text(url)
    srcs = get_image_src(html)
    return get_image_url_name(srcs)


if __name__ == "__main__":
    test_url = "https://telegra.ph/NO001-是一只废喵了-奶牛-10-01-2"
    print(get_image_info(test_url))
