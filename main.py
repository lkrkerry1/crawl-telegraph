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


def download_imagelist(urls: str) -> None:
    url_list = urls.splitlines()
    threads: list[threading.Thread] = []
    for url in url_list:
        t = threading.Thread(target=download_image, args=(url,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    url = "https://telegra.ph/NO001-%E6%98%AF%E4%B8%80%E5%8F%AA%E5%BA%9F%E5%96%B5%E4%BA%86-%E5%A5%B6%E7%89%9B-10-01-2"
    download_image(url, 32)
    print(">>> 任务结束！")
