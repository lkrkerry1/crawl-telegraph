# crawl-telegraph

抓取 telegra.ph 页面图片资源并保存到本地，支持命令行和 GUI 两种模式。

## 使用方法

1. 安装依赖（推荐在 PowerShell 下）：
	```powershell
	pip install -e .
	```

2. 命令行运行：
	```powershell
	python main.py
	```
	- 默认下载链接请在 `main.py` 顶部的 `sample` 变量中填写（多行字符串，每行一个链接）。

3. 启动 GUI（webui2 桌面窗口）：
	```powershell
	python -c "from ui import launch_ui; launch_ui()"
	```
	- 在弹出的窗口输入 telegra.ph 链接，每行一个，点击“开始下载”即可。

4. 可选：开发环境安装脚本入口
	```powershell
	pip install -e .[dev]
	# 之后可直接运行 crawl-telegraph
	```

## 主要文件说明

- `main.py`：命令行主流程，支持多线程下载，进度回调。
- `image_url.py`：页面解析与图片下载，带重试和超时。
- `ui.py`：webui2 GUI 启动器，负责窗口绑定和进度推送。
- `templates/index.html`：前端页面模板。
- `pyproject.toml`：依赖声明与脚本入口。

## 进阶说明

- 下载目录为 `./download/<页面名>`，图片命名为 `image_{id:03d}_{name}`。
- 进度事件以 JSON 格式推送到前端或控制台。
- 如需自定义下载链接，建议直接编辑 `main.py` 的 `sample` 变量或通过 GUI 输入。

## 开发/测试

- 推荐安装 dev 依赖：`pip install -e .[dev]`
- 支持 pytest/black。

---
如需命令行参数、配置文件支持或其它功能扩展，请参考 `main.py` 说明或联系维护者。