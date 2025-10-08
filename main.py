import os.path
import re, threading
import time

from urllib import parse

from judgeWeb.image_url import get_image_info, get_image_content, get_headers


def download_block(path: str, infos: dict) -> None:
    for i in infos:
        name = i["name"]
        url = i["url"]
        filename = path + f"/image_{i['id']:03d}_" + name
        if not os.path.exists(filename):
            with open(filename, "wb") as f:
                f.write(get_image_content(url))
            print(f">>> 已完成：{filename}")
            time.sleep(1)
        else:
            print(f">>> {filename} 已存在，跳过。")


def download_image(url: str, threadcnt: int = 32) -> None:
    path = re.findall(r"telegra.ph/(.+)", parse.unquote(url))[0]
    info = get_image_info(url)
    threads: list[threading.Thread] = []

    if not os.path.exists(path):
        os.mkdir(path)
    infolst = [[] for _ in range(threadcnt)]
    for i in info:
        infolst[i["id"] % threadcnt].append(i)

    for blk in infolst:
        t = threading.Thread(target=download_block, args=(path, blk))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def download_imagelist(urls: str, threadcnt: int = 32) -> None:
    url_list = urls.splitlines()
    threads: list[threading.Thread] = []
    for url in url_list:
        if not url.strip():
            continue
        t = threading.Thread(
            target=download_image, args=(url, threadcnt // len(url_list))
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    url = """https://telegra.ph/NO001-是一只废喵了-奶牛-10-01-2
    
https://telegra.ph/NO002-是一只废喵了-竞泳-10-01
    https://telegra.ph/NO003-Fantia-2022年07月套图-56P-173MB-10-01-2
  https://telegra.ph/NO004-Fantia-2022年09月套图-35P-376MB-10-03"""
    download_imagelist(url)
    print(">>> 任务结束！")
