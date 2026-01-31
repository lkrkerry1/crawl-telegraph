import json
import threading
import queue
import gradio as gr

from image_url import get_image_info
from main import download_imagelist


def download_with_progress(
    urls: str, threadcnt: int, compress: bool, opt_path: str, filename_format: str
):
    """Generator that runs download_imagelist in a background thread and yields
    streaming updates (logs, processed count, progress percent) to the UI."""
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    if not url_list:
        yield ("没有输入 URL", 0, "0%")
        return

    # pre-scan pages to estimate total images (best-effort)
    total = 0
    for url in url_list:
        try:
            info = get_image_info(url)
            total += len(info)
        except Exception:
            # ignore failures; we still proceed
            pass

    q: "queue.Queue[str]" = queue.Queue()

    def progress_cb(msg: str):
        q.put(msg)

    worker = threading.Thread(
        target=download_imagelist,
        kwargs={
            "urls": urls,
            "threadcnt": int(threadcnt),
            "opt_path": opt_path,
            "filename_format": filename_format,
            "progress": progress_cb,
        },
    )
    worker.start()

    processed = 0
    logs: list[str] = []
    last_percent = -1

    # initial yield
    yield ("", 0, "0%")

    while worker.is_alive() or not q.empty():
        try:
            msg = q.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            evt = json.loads(msg)
        except Exception:
            logs.append(str(msg))
            percent = int(processed / total * 100) if total > 0 else 0
            yield ("\n".join(logs[-200:]), processed, f"{percent}%")
            continue

        if evt.get("event") == "page":
            action = evt.get("action")
            page = evt.get("page")
            if action == "start":
                logs.append(f"页面开始: {page}")
            else:
                logs.append(f"页面结束: {page}")
        elif evt.get("event") == "file":
            status = evt.get("status")
            name = evt.get("name")
            filename = evt.get("filename")
            if status == "done":
                processed += 1
                logs.append(f"已下载: {name} -> {filename}")
            elif status == "skipped":
                processed += 1
                logs.append(f"跳过: {name} (已存在)")
            else:
                processed += 1
                logs.append(f"错误: {name} -> {evt.get('error')}")
        else:
            logs.append(str(evt))

        percent = int(processed / total * 100) if total > 0 else 0
        # yield updates (coalescing to reduce UI churn)
        if percent != last_percent or len(logs) % 2 == 0:
            last_percent = percent
            yield ("\n".join(logs[-200:]), processed, f"{percent}%")

    worker.join()
    logs.append("任务完成")
    final_percent = 100 if total > 0 else int(processed)
    yield ("\n".join(logs[-200:]), processed, f"{final_percent}%")


iface = gr.Interface(
    fn=download_with_progress,
    inputs=[
        gr.Textbox(
            label="Telegraph 页面 URL 列表", lines=6, placeholder="每行一个 URL"
        ),
        gr.Number(label="线程数", value=32, precision=0),
        gr.Checkbox(label="启用图片压缩", value=True),
        gr.Textbox(label="保存路径", value="./download"),
        gr.Textbox(
            label="文件命名格式",
            value="{id:03d}_{name}{ext}",
            placeholder="使用 Python 格式化字符串语法",
        ),
    ],
    outputs=[
        gr.Textbox(label="日志", lines=15),
        gr.Number(label="已处理文件数", value=0, precision=0),
        gr.Textbox(label="进度"),
    ],
    title="Telegraph 图片下载器",
    description="输入多个 Telegraph 页面 URL，点击提交后开始下载。界面会实时显示日志与进度。",
    flagging_mode="never",
)


def launch_ui():
    """Launch the Gradio UI for the package console-script entry point."""
    iface.launch()


if __name__ == "__main__":
    launch_ui()
