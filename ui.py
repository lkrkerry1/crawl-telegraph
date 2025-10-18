from webui import webui
import threading
from typing import Optional
from pathlib import Path
import json

from main import download_imagelist


def _load_template() -> str:
    """Load and return the HTML template used by the UI.

    The template is expected at ``./templates/index.html`` relative to the
    repository root. This helper raises ``FileNotFoundError`` when the file
    is missing which surfaces a clear error to the developer.

    Returns
    -------
    str
        The HTML content as a UTF-8 string.
    """
    tpl = Path(__file__).resolve().parent / "templates" / "index.html"
    if not tpl.exists():
        raise FileNotFoundError(
            f"Template not found: {tpl}. Please ensure ./templates/index.html exists."
        )
    return tpl.read_text(encoding="utf-8")


def launch_ui():
    w = webui.Window()

    # 把 templates 目录设置为 webui 的 root，让内置服务器可以提供 webui.js 和 index.html
    tpl_dir = str(Path(__file__).resolve().parent / "templates")
    try:
        w.set_root_folder(tpl_dir)
    except Exception:
        # 某些 webui 版本可能不支持 set_root_folder; ignore and fall back
        pass

    # 使用相对文件名显示，让 webui 的服务器为页面注入并提供 /webui.js
    w.show("index.html")

    # 后端 -> 前端：调用前端函数 push_log
    def push_log_to_client(e: "webui.Event", msg: str) -> None:
        """Send a single text line to the client page's `push_log` JS
        function.

        This helper runs a short piece of JavaScript in the connected
        client; failures are swallowed because the client may not always be
        connected when the backend emits logs.
        """
        # 使用脚本接口在客户端执行 push_log
        safe_js = f"push_log({repr(msg)})"
        try:
            e.run_client(safe_js)
        except Exception:
            # 可能在无客户端连接时失败，忽略
            pass

    # 绑定开始下载的后端函数
    def start_download(event: "webui.Event") -> None:
        urls = event.get_string()  # 第一个参数为 urls 字符串

        def worker(u: str, ev: "webui.Event"):
            push_log_to_client(ev, "开始下载任务")
            try:
                # 将进度回调传给下载函数
                def progress_cb(msg: str):
                    # try to parse structured JSON events from main
                    try:
                        j = json.loads(msg)
                        if j.get("event") == "page":
                            action = j.get("action")
                            if action == "start":
                                push_log_to_client(ev, f"[页面开始] {j.get('page')}")
                            elif action == "end":
                                push_log_to_client(ev, f"[页面结束] {j.get('page')}")
                        elif j.get("event") == "file":
                            status = j.get("status")
                            name = j.get("name")
                            if status == "done":
                                push_log_to_client(ev, f"[完成] {j.get('filename')}")
                            elif status == "skipped":
                                push_log_to_client(ev, f"[跳过] {j.get('filename')}")
                            elif status == "error":
                                push_log_to_client(
                                    ev, f"[错误] {name}: {j.get('error')}"
                                )
                        else:
                            push_log_to_client(ev, msg)
                    except Exception:
                        # not JSON, just push raw
                        push_log_to_client(ev, msg)

                download_imagelist(u, progress=progress_cb)
                push_log_to_client(ev, "下载任务完成")
            except Exception as ex:
                push_log_to_client(ev, f"下载任务出错：{ex}")

        # 启动后台线程执行下载并把 event 传入用于回调
        t = threading.Thread(target=worker, args=(urls, event), daemon=True)
        t.start()

    # 绑定函数名 'start_download'，前端可通过 window.pywebui_call 调用
    w.bind("start_download", start_download)

    webui.wait()


if __name__ == "__main__":
    launch_ui()
