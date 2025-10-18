import os
import re
import threading
from typing import Callable, Optional

from urllib import parse

from image_url import get_image_info, get_image_content, get_headers
import json

root_path = "./download"


def download_block(
    path: str, infos: list, progress: Optional[Callable[[str], None]] = None
) -> None:
    """Download a block of images for a single page.

    For each image info in ``infos`` this function will ensure the page
    directory exists, download the image bytes via
    :func:`image_url.get_image_content` and write them to disk. After each
    file is processed this function will call ``progress(payload)`` if
    provided, where ``payload`` is a JSON-encoded string with the shape:

        {"event": "file", "status": "done|skipped|error", "page": <page>,
         "name": <name>, "filename": <path>, ["error": <message>]}

    Parameters
    ----------
    path:
        The page directory name (derived from the telegra.ph URL).
    infos:
        A list of dicts produced by :func:`image_url.get_image_info`, each
        containing keys ``name``, ``url`` and ``id``.
    progress:
        Optional callable that accepts a single string message. This
        function uses the callback to emit JSON messages describing file
        progress. Exceptions raised by the callback are ignored.

    Returns
    -------
    None

    Notes
    -----
    This function swallows exceptions from the ``progress`` callback, but
    allows exceptions raised during the actual download to be captured and
    reported as a file-level error event in the JSON payload.
    """
    for i in infos:
        name = i["name"]
        url = i["url"]
        # ensure path is inside root_path
        page_dir = os.path.join(root_path, path)
        filename = os.path.join(page_dir, f"image_{i['id']:03d}_{name}")
        if not os.path.exists(page_dir):
            os.makedirs(page_dir, exist_ok=True)
        if not os.path.exists(filename):
            try:
                with open(filename, "wb") as f:
                    f.write(get_image_content(url))
                evt = {
                    "event": "file",
                    "status": "done",
                    "page": path,
                    "name": name,
                    "filename": filename,
                }
            except Exception as e:
                evt = {
                    "event": "file",
                    "status": "error",
                    "page": path,
                    "name": name,
                    "filename": filename,
                    "error": str(e),
                }
        else:
            evt = {
                "event": "file",
                "status": "skipped",
                "page": path,
                "name": name,
                "filename": filename,
            }
        payload = json.dumps(evt, ensure_ascii=False)
        print(payload)
        if progress:
            try:
                progress(payload)
            except Exception:
                pass


def download_image(
    url: str, threadcnt: int = 32, progress: Optional[Callable[[str], None]] = None
) -> None:
    """Download all images from a single telegra.ph page.

    The function will parse the telegra.ph `url` to derive a directory
    name, fetch image metadata with :func:`image_url.get_image_info` and
    dispatch worker threads to download images in parallel. It emits page
    lifecycle events through the ``progress`` callback as JSON strings:

      - Page start:  {"event":"page", "action":"start", "page":...}
      - File events: see :func:`download_block` for file payload shape
      - Page end:    {"event":"page", "action":"end", "page":...}

    Parameters
    ----------
    url:
        A full telegra.ph page URL (e.g. "https://telegra.ph/SomePage-10-01").
    threadcnt:
        Number of per-page worker buckets used to partition images. The
        implementation uses ``id % threadcnt`` to distribute work.
    progress:
        Optional callable receiving string messages (JSON-encoded events).

    Raises
    ------
    ValueError
        If a page path cannot be extracted from ``url``.
    """
    m = re.findall(r"telegra.ph/(.+)", parse.unquote(url))
    if not m:
        raise ValueError(f"无法从 url 提取页面路径: {url}")
    path = m[0]
    info = get_image_info(url)
    threads: list[threading.Thread] = []

    infolst = [[] for _ in range(max(1, threadcnt))]
    for i in info:
        infolst[i["id"] % len(infolst)].append(i)

    # notify page start
    if progress:
        try:
            progress(
                json.dumps(
                    {"event": "page", "action": "start", "page": path},
                    ensure_ascii=False,
                )
            )
        except Exception:
            pass

    for blk in infolst:
        t = threading.Thread(target=download_block, args=(path, blk, progress))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # notify page end
    if progress:
        try:
            progress(
                json.dumps(
                    {"event": "page", "action": "end", "page": path}, ensure_ascii=False
                )
            )
        except Exception:
            pass


def download_imagelist(
    urls: str, threadcnt: int = 32, progress: Optional[Callable[[str], None]] = None
) -> None:
    """Download images from multiple telegra.ph pages.

    The input is a multi-line string where each non-empty line is treated as
    a telegra.ph page URL. For each page a background thread is started
    which calls :func:`download_image`. The per-page worker thread count is
    computed as ``max(1, threadcnt // num_pages)``.

    Parameters
    ----------
    urls:
        Multi-line string: one telegra.ph URL per line.
    threadcnt:
        Total number of worker buckets to divide among pages.
    progress:
        Optional callback to receive JSON-encoded progress messages from
        page/file events.

    Returns
    -------
    None
    """
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    if not url_list:
        return
    per_page_threads = max(1, threadcnt // len(url_list))
    threads: list[threading.Thread] = []
    for url in url_list:
        t = threading.Thread(
            target=download_image, args=(url, per_page_threads, progress)
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def main():
    """Example runner used when executing the module directly.

    The function contains a small built-in sample list of telegra.ph pages
    (for development) and calls :func:`download_imagelist`.
    """
    sample = """https://telegra.ph/NO001-是一只废喵了-奶牛-10-01-2
    https://telegra.ph/NO002-是一只废喵了-竞泳-10-01
    https://telegra.ph/NO003-Fantia-2022年07月套图-56P-173MB-10-01-2
    https://telegra.ph/NO004-Fantia-2022年09月套图-35P-376MB-10-03"""
    download_imagelist(sample)
    print(">>> 任务结束！")


if __name__ == "__main__":
    main()
