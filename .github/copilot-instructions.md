<!--
Guidance for AI coding agents working on the `crawl-telegraph` repo.
Keep this file short and actionable: focus on how this repo is organized, key
runtime flows, local conventions, and where to make safe changes.
-->

# crawl-telegraph — Copilot instructions

## 一句话架构
本仓库用于从 telegra.ph 页面批量抓取图片并保存到本地，支持命令行和 GUI 两种模式：
- 命令行脚本（`main.py`）：多线程下载，进度事件打印到控制台。
- GUI 启动器（`ui.py`，基于 `webui2`）：桌面窗口，输入链接后可一键下载。

## 关键文件（快速索引）
- `main.py` — 命令行主流程，支持多线程下载，进度事件打印。
- `image_url.py` — 页面解析与图片下载，带重试和超时。
- `ui.py` — GUI 启动器，负责窗口绑定和进度推送。
- `templates/index.html` — 前端页面模板。
- `pyproject.toml` — 依赖声明与脚本入口。

## 运行 / 调试 快速指南
- 安装依赖（PowerShell）：
  ```powershell
  pip install requests webui2
  ```
- 命令行运行：
  ```powershell
  python main.py
  ```
- 启动 GUI：
  ```powershell
  python -c "from ui import launch_ui; launch_ui()"
  ```
- 可选：开发环境脚本入口
  ```powershell
  pip install -e .[dev]
  # 之后可直接运行 crawl-telegraph
  ```

## 项目约定与易忽视的实现细节
- 下载目录：`root_path = "./download"`（在 `main.py` 内），图片命名为 `image_{id:03d}_{name}`。
- 并发分区：`infolst[i['id'] % threadcnt].append(i)`，分配依赖 `id`。
- HTTP headers：`image_url.py` 随机 `User-Agent` + 固定 `Referer`，所有请求共用一个 session。
- 新页面添加：编辑 `main.py` 的 `sample` 变量或通过 GUI 输入。

## 常见改动点（示例和安全边界）
- 支持命令行参数：可将 `main.py` 的 `sample` 改为 argparse/click 参数。
- 增加重试/超时：`image_url.py` 已实现。
- 并发模型可扩展为进程池/asyncio，但当前线程已满足需求。

## 代码示例（引用自仓库）
- `image_url.py`：
	```python
	def get_image_info(url):
			return get_image_url_name(get_image_src(get_html_text(url)))
	```
- `main.py`：
	```python
	infolst = [[] for _ in range(threadcnt)]
	for i in info:
			infolst[i["id"] % threadcnt].append(i)
	# 每个分区启动线程保存图片
	```

## 测试 / Lint / Dev 流程
- 推荐安装 dev 依赖：`pip install -e .[dev]`（或单独安装 `pytest black`）。
- 可添加单元测试验证 `get_image_info`。

## 可改进点（供 AI/开发者参考）
- URL 输入可支持 CLI/配置文件。
- 日志与 exit code 可进一步规范。

---
如需扩展功能（如 CLI 参数、配置文件、日志优化等），可直接提出。
