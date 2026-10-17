# C01 Lesson04：Lesson03 服务启动说明

## 1. 运行环境

本项目当前使用 Conda 的 `fde` 环境。

激活环境：

```bash
conda activate fde
```

检查当前解释器：

```bash
python -c "import sys; print(sys.executable)"
```

预期路径：

```text
/Users/jace/miniforge3/envs/fde/bin/python
```

VS Code 的 Python 解释器也应选择这个环境。

## 2. 项目目录

启动前进入项目根目录：

```bash
cd /Users/jace/office-agent-learning
```

## 3. 配置要求

项目根目录的本地 `.env` 需要配置以下变量：

- `DEEPSEEK_API_KEY`：本地填写真实 API Key。
- `DEEPSEEK_MODEL`：当前使用的模型名称。

配置项可参考 `.env.example`。

真实 `.env` 不提交到 Git。已有配置文件继续使用，避免覆盖。

## 4. 启动服务

在项目根目录执行：

```bash
python -m uvicorn examples.lesson03.api:app --reload --env-file .env
```

其中：

- `examples.lesson03.api`：应用所在模块。
- `app`：模块中定义的 FastAPI 应用对象。
- `--reload`：开发期间检测代码变化并重新加载。
- `--env-file .env`：启动时加载本地环境配置。

看到 `Application startup complete`，说明应用启动完成。

服务运行期间保留此终端。需要执行其他命令时打开另一个终端；停止服务按 `Ctrl+C`。

本说明使用默认 8000 端口，启动前先停止占用该端口的其他课程服务。README 另提供 8001 端口示例；使用哪个端口，就访问对应端口的地址。

## 5. 检查服务

健康检查：

http://127.0.0.1:8000/health

预期响应：

```json
{"status": "ok"}
```

接口文档：

http://127.0.0.1:8000/docs

健康检查成功表明本地服务可以响应请求；模型调用是否成功，需要另外检查生成接口。

## 6. ModuleNotFoundError 排查

首先检查两个方面：

1. **解释器与依赖**：是否正在使用 `fde`，所需依赖是否安装在这个环境中。
2. **模块路径与启动方式**：是否位于项目根目录，是否使用完整模块路径启动应用。

例如，缺少 `httpx` 时重点检查环境和依赖；找不到 `examples` 时重点检查目录和模块路径。
