import os
import re
import threading
from typing import Callable, Optional

from urllib import parse

from image_url import get_image_info, get_image_content
import json

root_path = "./download"


def download_block(
    path: str,
    infos: list,
    progress: Optional[Callable[[str], None]] = None,
    root_path: Optional[str] = None,
    filename_format: str = "{id:03d}_{name}{ext}",
) -> None:
    """Download a block of images for a single page.

    New parameters:
      - root_path: override the base download directory (defaults to the
        module-level ``root_path``).
      - filename_format: format string used to generate filenames. It can
        use placeholders ``id``, ``name``, and ``ext`` (e.g. "{id:03d}_{name}{ext}").

    For each image info in ``infos`` this function will ensure the page
    directory exists, download the image bytes via
    :func:`image_url.get_image_content` and write them to disk. After each
    file is processed this function will call ``progress(payload)`` if
    provided, where ``payload`` is a JSON-encoded string with the shape:

        {"event": "file", "status": "done|skipped|error", "page": <page>,
         "name": <name>, "filename": <path>, ["error": <message>]}
    """
    # determine which root to use
    rp = (
        root_path if root_path is not None else globals().get("root_path", "./download")
    )

    for i in infos:
        name = i["name"]
        url = i["url"]
        page_dir = os.path.join(rp, path)

        # determine extension and basename
        base, ext = os.path.splitext(name)
        if not ext:
            ext = os.path.splitext(parse.urlparse(url).path)[1] or ".jpg"
        name_no_ext = base

        # clean name component
        safe_name_component = re.sub(r'[<>:"/\\|?*]', "", name_no_ext)

        # attempt to format using the provided filename_format
        try:
            safe_name = filename_format.format(
                id=i["id"], name=safe_name_component, ext=ext
            )
        except Exception:
            # fallback to previous behaviour on format error
            if name.startswith("http://") or name.startswith("https://"):
                safe_name = f"{i['id']:03d}{ext if ext else '.jpg'}"
            else:
                safe_name = re.sub(r"[<>:\"/\\|?*]", "", name)
                safe_name = (
                    f"{i['id']:03d}_{safe_name}" if safe_name else f"{i['id']:03d}.jpg"
                )

        filename = os.path.join(page_dir, safe_name)
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
    url: str,
    threadcnt: int = 32,
    progress: Optional[Callable[[str], None]] = None,
    root_path: Optional[str] = None,
    filename_format: str = "{id:03d}_{name}{ext}",
) -> None:
    """Download all images from a single telegra.ph page.

    Additional parameters ``root_path`` and ``filename_format`` are passed
    to :func:`download_block` to control output location and filename
    generation.
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
        t = threading.Thread(
            target=download_block,
            args=(path, blk, progress, root_path, filename_format),
        )
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
    urls: str,
    threadcnt: int = 32,
    progress: Optional[Callable[[str], None]] = None,
    root_path: Optional[str] = None,
    filename_format: str = "{id:03d}_{name}{ext}",
) -> None:
    """Download images from multiple telegra.ph pages.

    The input is a multi-line string where each non-empty line is treated as
    a telegra.ph page URL. For each page a background thread is started
    which calls :func:`download_image`. The per-page worker thread count is
    computed as ``max(1,threadcnt // num_pages)``.

    Additional parameters ``root_path`` and ``filename_format`` are
    forwarded to per-page workers.
    """
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    if not url_list:
        return
    per_page_threads = max(1, threadcnt // len(url_list))
    threads: list[threading.Thread] = []
    for url in url_list:
        t = threading.Thread(
            target=download_image,
            args=(url, per_page_threads, progress, root_path, filename_format),
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
