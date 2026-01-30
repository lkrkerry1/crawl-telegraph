<!--
Guidance for AI coding agents working on the `crawl-telegraph` repo.
Keep this file short and actionable: focus on how this repo is organized, key
runtime flows, local conventions, and where to make safe changes.
-->

# crawl-telegraph — Copilot instructions

## 一句话架构
本仓库用于从 telegra.ph 页面批量抓取图片并保存到本地，提供两种运行方式：
- CLI (`main.py`)：并发下载、控制台/回调式进度事件输出。
- GUI (`ui.py`, 基于 `webui2`)：桌面窗口，输入链接后异步下载并把日志推送到前端。

## 哪里开始（快速上手） ✅
- 安装（建议使用虚拟环境）：
  ```powershell
  pip install -e .[dev]
  ```
- 命令行运行：
  ```powershell
  python main.py
  # 或（安装后）直接运行脚本入口： crawl-telegraph
  ```
- 启动 GUI：
  ```powershell
  python -c "from ui import launch_ui; launch_ui()"
  # 或（安装后）crawl-telegraph-ui
  ```

## 关键文件 & 角色 🔧
- `main.py` — 下载控制流、并发分区、文件写入、进度事件 JSON（页面/文件层级）。
- `image_url.py` — 网络层：requests session（带 Retry）、UA 轮换、HTML 解析、获取图片 bytes。修改网络参数/重试策略请在此文件修改。
- `ui.py` — GUI 启动与后端事件推送。前端通过 `window.start_download(urls)` 调用后端，后端用 `Event.run_client(js)` 调用 `push_log(msg)`。
- `templates/index.html` — 前端模板：`start` 按钮会调用 `window.start_download(urls)`，并提供 `push_log(msg)` 供后端显示日志。
- `pyproject.toml` — 依赖、版本、以及两个 console-scripts：`crawl-telegraph` 和 `crawl-telegraph-ui`。
- `compress.py` — 目前为空，属于安全改动区域（新增工具/脚本放这里）。

## 重要实现细节（需知道的「坑」） ⚠️
- 线程分区：每个页内使用 `id % threadcnt` 将图片分配到多个工作桶（默认 `threadcnt=32`）。批量多页时，`download_imagelist` 会将总线程数按页数分配为 `per_page_threads = max(1, threadcnt // len(url_list))`。
- 进度事件（JSON）：
  - 页面开始/结束： {"event":"page","action":"start|end","page": <page>}。
  - 文件事件： {"event":"file","status":"done|skipped|error","page":...,"name":...,"filename":..., ["error": ...]}。
  - 代码中使用 `json.dumps(..., ensure_ascii=False)` 保持中文可读。
- 网络与重试：使用 `requests.Session()` 与 `urllib3.util.retry.Retry(total=3, backoff_factor=0.3, status_forcelist=[429,500,502,503,504])`。
  - 默认超时：HTML 请求 `timeout=10`，图片下载 `timeout=20`。
  - 头部：`get_headers()` 随机 `User-Agent`（列表内）+ 固定 `Referer: https://telegra.ph/`。
- 文件命名与安全字符清理：
  - 如果源 name 看起来像 URL，会提取扩展名并使用 `{id:03d}{ext}`；否则使用 `re.sub(r'[<>:\"/\\|?*]', "", name)`，再拼成 `{id:03d}_{name}`。
  - 下载目录默认为 `root_path = "./download"`（在 `main.py`），变更时注意路径拼接与安全性（不允许把文件写到 repo 根外）。
- UI 细节：`templates/index.html` 依赖 `webui.js`（由 webui2 嵌入），`ui.py` 尝试 `w.set_root_folder(tpl_dir)` 以确保模板和 `webui.js` 被提供；不同 webui 版本可能不支持该方法，已作容错处理。
  - 前端现在提供额外设置：**输出目录**（`output`）、**文件名格式**（`filename_format`，默认 `"{id:03d}_{name}{ext}"`）和**最大线程数**（`max_threads`）。这些设置由前端以 JSON 字符串传给 `window.start_download`（例如 `{urls:"...",output:"./download",filename_format:"{id:03d}_{name}{ext}",max_threads:32}`），`ui.py` 会解析 JSON 并把设置转发给 `download_imagelist`。
  - `filename_format` 支持 Python 风格格式化占位符：`id`（可用格式如 `{id:03d}`）、`name`（清理过的文件名主体，无扩展名）和 `ext`（包含 `.` 的扩展名，如 `.jpg`）。失败时会回退到原来的命名策略。

## 修改建议与安全边界 ✅
- 想添加 CLI 参数：优先在 `main.py` 用 `argparse` 增加 `--threads`, `--output`, `--timeout` 等（不要直接改名为全局常量，保留默认值）。
- 修改重试/超时或 User-Agent 列表：在 `image_url.py` 中修改 `retry_strategy`, `backoff_factor`, `user_agent` 列表。
- 改进并发模型：可替换为 `concurrent.futures.ThreadPoolExecutor` 或 `asyncio`，但要保持相同的进度事件 JSON API 以兼容 `ui.py`。
- 增加日志：后端使用 `print(payload)` 产生日志；若引入 logging，请确保在 `ui.py` 的 `progress_cb` 中解析 JSON 事件并通过 `push_log_to_client` 发送友好的文本。

## 测试 / 类型 & Lint 🧪
- 推荐添加单元测试到 `tests/`：首选 `image_url.get_image_info`, `get_image_src`, `get_image_url_name` 的解析测试。
- dev 依赖在 `pyproject.toml`：`pytest`, `black`。运行 `pytest` 来执行测试。

## PR 小贴士 / 代码审查关注点 🔍
- 保持 **输出事件格式不变**（前端依赖该格式）。
- 小改动优先：网络参数、超时、错误信息改进、增加单元测试。
- 重构并发/IO 层时，确保至少有一组集成测试覆盖下载流程（可以用本地静态 HTML 模拟页面）。

---

如果你想要，我可以：
1. 增加一个示例 `tests/test_image_url.py`（覆盖 HTML->src->info 的解析）✅
2. 添加 `argparse` 支持到 `main.py` 的 `main()`（`--threads`, `--output`）✅

需要我先做哪一项？或者觉得文件中哪些地方还不够清晰？
