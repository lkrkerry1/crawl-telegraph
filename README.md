# crawl-telegraph

抓取 telegra.ph 页面图片资源并保存到本地，支持命令行与基于 Gradio 的 GUI。

## 使用方法

1. 安装依赖（推荐在 PowerShell 下）：
    ```powershell
    pip install -e .
    # 或（包含开发依赖）
    pip install -e .[dev]
    ```

2. 命令行运行：
    ```powershell
    python main.py
    # 或（安装后）直接运行脚本入口：
    crawl-telegraph
    ```

3. 启动 GUI（Gradio）：
    ```powershell
    python ui.py
    # 或（安装后）运行脚本入口：
    crawl-telegraph-ui
    ```
    - 在界面输入每行一个的 Telegraph 页面 URL，点击提交后会实时显示日志、已处理计数与进度百分比。

## 主要文件说明

- `main.py`：命令行主流程，支持多线程下载与进度回调。
- `image_url.py`：页面解析与图片下载（含重试策略与 UA 轮换）。
- `ui.py`：基于 Gradio 的流式进度展示（实时日志 + 已处理计数 + 百分比）。
- `compress.py`：可选的图片压缩工具（Pillow 实现）。
- `pyproject.toml`：依赖与 console scripts 配置。

## 进阶说明

- 默认下载路径为 `./download/<页面名>`，文件名可以通过 `filename_format` 配置（支持 `{id}`, `{name}`, `{ext}`）。
- 进度事件以 JSON 字符串从后端发出（事件类型：`page`、`file`），UI 会解析并展示为可读日志与百分比。

## 许可证

本项目遵循 **GNU General Public License v3 (GPLv3)**，详细内容见 `LICENSE` 文件。

## 开发/测试

- 推荐使用 dev 依赖并运行测试：
    ```powershell
    pip install -e .[dev]
    pytest
    ```

---
如需添加命令行参数、改进并发模型或其它功能扩展，欢迎提交 Issue 或 PR。