# Liangent：极简轻量级 Agent 框架

> **Slogan**: 极简轻量 Agent，你的第一个可用 Agent。

[English](README.md) | [中文](README_CN.md)

---

**Liangent** 是一个轻量级、可扩展且具备记忆感知能力的 Agent 框架。它的初衷是作为 **Agent 教学原型**，同时也是解决**简单任务**的实战利器。

不同于那些依赖繁重"规划（Planning）"步骤的复杂框架，Liangent 专注于通过 **强制工具调用** 和 **运行时动态 Prompt 注入** 来解决问题。这种方法在处理简单任务时，能有效减少大模型的幻觉，提高可用性。

---

## ✨ 核心特性

### 🛡️ 本地代码沙箱
- 基于 AST 校验的 **Python 代码**安全执行
- 基于白名单/黑名单的 **Shell 命令**安全执行
- **双重安全保证**：
  - Python：模块白名单（`math`, `datetime`, `json`, `random`, `re`, `collections`, `itertools`, `functools`, `statistics`）
  - Python：内置函数黑名单（`open`, `exec`, `eval`, `compile` 等）
  - Shell：命令白名单（`python3`, `ls`, `grep`, `cat`, `date`, `find`）
  - Shell：危险模式拦截（`;`, `&`, `` ` ``, `$(`）
- 进程隔离 + 超时保护

### 📉 动态约束减少幻觉
- **最小工具调用次数 (`min_tool_use`)**：强制 Agent 调用工具后才能回答
- **最大工具调用次数 (`max_tool_use`)**：防止无限循环调用
- **动态 Prompt 注入**：如果 Agent 试图过早回答，系统会拦截并强制反思

### 🔧 极简工具注册
- 使用 `@tool` 装饰器即可注册工具
- **双模式支持**：
  - **原生 Function Calling**：支持 FC API 的模型（GPT-4、Claude 3 等）
  - **Prompt 解析模式**：从文本输出解析 JSON，兼容任意大模型
- 从 Google 风格文档字符串自动生成 JSON Schema

### 💾 极简 SQLite 存储
- 零配置会话和日志持久化
- 全链路可追溯
- 支持 PostgreSQL 等其他数据库

### 🔍 高可观测性
- `verbose=True`：查看工具调用、思考过程和结果
- `debug=True`：查看 Token 用量、成本和详细步骤信息
- `show_prompts=True`：查看发送给 LLM 的完整 Prompt（系统提示 + 历史）

### ☁️ Serverless 友好
- 内置 `fc_handler.py`，适配阿里云函数计算
- 可适配 AWS Lambda、Google Cloud Functions 等

---

## 🚀 快速开始

### 1. 安装
```bash
pip install liangent
```

### 2. 初始化项目
```bash
liangent init
```
生成以下文件：
- `.env`：配置文件（API Key、限制参数等）
- `AGENTS.md`：Agent 人设和行为指南

编辑 `.env`：
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# 工具调用策略
MIN_TOOL_USE=1
MAX_TOOL_USE=15
MAX_STEPS=20

# 是否启用原生 Function Calling（需模型支持）
SUPPORTS_FUNCTION_CALLING=False
```

### 3. 基础用法

#### 同步调用
```python
from liangent import Liangent

client = Liangent(verbose=True)
response = client.chat("计算 123 * 456")
print(response)
```

#### 流式调用
```python
from liangent import Liangent

client = Liangent()

for event in client.stream("查看当前目录下的文件"):
    evt_type = event.get("event")
    
    if evt_type == "thought":
        print(f"[思考中] {event.get('content')}")
    elif evt_type == "item.started":
        item = event.get("data", {}).get("item", {})
        print(f"[工具调用] {item.get('tool')}({item.get('args')})")
    elif evt_type == "item.completed":
        item = event.get("data", {}).get("item", {})
        print(f"[工具结果] {item.get('aggregated_output')}")
    elif evt_type == "final_answer":
        print(f"[答案] {event.get('content')}")
    elif evt_type == "usage_stats":
        content = event.get("content", {})
        print(f"[用量] {content.get('usage')}")
        print(f"[成本] {content.get('cost')}")
```

---

## ⚙️ 配置参数

### Liangent 客户端参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `api_key` | str | None | OpenAI API Key（回退到环境变量） |
| `base_url` | str | None | OpenAI Base URL（回退到环境变量） |
| `model_name` | str | None | 模型名称（回退到环境变量） |
| `db_url` | str | None | 数据库 URL（未设置则使用内存） |
| `tools` | List[str] | None | 启用的工具名称列表（None 表示全部） |
| `verbose` | bool | False | 打印思考过程和工具执行 |
| `debug` | bool | False | 打印完整调试信息（包含 verbose） |
| `show_prompts` | bool | False | 打印每步的完整 Prompt |
| `min_tool_use` | int | 1 | 最终答案前最少调用工具次数 |
| `max_tool_use` | int | 15 | 最多允许调用工具次数 |
| `max_steps` | int | 20 | Agent 最大执行步数 |

### 示例：强制工具调用
```python
from liangent import Liangent

# Agent 必须调用至少 2 个工具才能回答
client = Liangent(
    min_tool_use=2,
    max_tool_use=10,
    max_steps=15,
    verbose=True
)

response = client.chat("今天天气怎么样？")
```

---

## 🖥️ 命令行工具

### 交互式聊天
```bash
liangent chat
```

### 启动 API 服务
```bash
liangent start --port 8000
```
- API 接口：`http://localhost:8000/api/chat`
- 接口文档：`http://localhost:8000/docs`

### 初始化配置
```bash
liangent init
```

---

## 🔧 自定义工具

使用 `@tool` 装饰器注册自定义工具。**必须使用 Google 风格文档字符串**，因为它会自动生成工具的 JSON Schema。

```python
from liangent import tool

@tool
def get_weather(city: str, unit: str = "celsius") -> str:
    """
    获取城市的当前天气。
    
    Args:
        city: 城市名称。
        unit: 温度单位（celsius 或 fahrenheit）。
    """
    # 你的实现逻辑
    return f"{city}天气：22°C，晴"

@tool
def search_database(query: str, limit: int = 10) -> list:
    """
    搜索数据库记录。
    
    Args:
        query: 搜索关键词。
        limit: 最大返回数量。
    """
    # 你的实现逻辑
    return [{"id": 1, "name": "结果1"}]
```

### 内置工具
- `python`：在沙箱中执行 Python 代码
- `shell_execute`：执行 Shell 命令（有安全限制）

---

## 📝 定制 Agent 行为

`AGENTS.md` 文件定义 Agent 的人设和规则，会自动注入到 System Prompt 中。

```markdown
# Agent 指南

## 身份
你是一名资深 Python 工程师，擅长数据分析。

## 行为规则
- 回答简洁专业
- 涉及代码逻辑必须使用 python 工具验证
- 处理文件操作时，先列出文件再读取

## 领域知识
- Python 最佳实践
- 数据分析工作流
```

---

## 🌐 API 服务

### 接口：POST `/api/chat`

#### 请求体
```json
{
    "query": "你的问题",
    "session_id": "可选的会话ID",
    "user_id": "default_user",
    "stream": true
}
```

#### SSE 事件（`stream=true` 时）
| 事件 | 说明 |
|-----|------|
| `meta` | 会话元数据 |
| `status` | 当前步骤状态 |
| `thought` | Agent 思考过程 |
| `item.started` | 工具开始执行 |
| `item.completed` | 工具执行完成 |
| `final_answer` | 最终回答 |
| `done` | 完成（含用量统计） |
| `error` | 发生错误 |

---

## ☁️ Serverless 部署

### 阿里云函数计算

1. 在函数计算控制台设置环境变量：
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `MODEL_NAME`

2. 使用 `fc_handler.py` 作为入口：
```python
# fc_handler.py 已包含在包中
# Handler 函数: handler
```

3. 部署并调用：
```json
{
    "query": "计算 123 * 456"
}
```

---

## 📊 事件类型参考

| 事件 | 数据字段 | 说明 |
|-----|---------|------|
| `input_received` | `content` | 收到用户输入 |
| `status` | `content` | 步骤状态（如 "Thinking (Step 1)..."） |
| `thought` | `content` | Agent 推理过程 |
| `item.started` | `data.item.id`, `tool`, `args` | 工具开始执行 |
| `item.completed` | `data.item.id`, `tool`, `aggregated_output`, `exit_code` | 工具执行完成 |
| `prompt_info` | `data.step`, `system_prompt`, `history` | 完整 Prompt 详情 |
| `debug` | `data.step`, `current_usage`, `total_cost` | 调试统计 |
| `final_answer` | `content` | 最终回答 |
| `usage_stats` | `content.usage`, `content.cost` | Token 用量和成本 |
| `error` | `content` | 错误信息 |

---

## 🔒 安全特性

### Python 沙箱
- **允许模块**：`math`, `datetime`, `json`, `random`, `re`, `collections`, `itertools`, `functools`, `statistics`
- **禁止函数**：`open`, `exec`, `eval`, `compile`, `input`, `globals`, `locals`
- **进程隔离**：5 秒超时，独立进程执行
- **AST 校验**：执行前安全检查

### Shell 沙箱
- **允许命令**：`python3`, `ls`, `grep`, `cat`, `date`, `find`
- **禁止模式**：`;`, `&`, `` ` ``, `$(`
- **路径限制**：禁止 `..` 跨目录，仅限项目目录
- **超时**：默认 60 秒

---

## 📦 项目结构

```
liangent/
├── __init__.py          # 导出：Liangent, tool
├── client.py            # 高层 Liangent 客户端
├── config.py            # 设置和 init_config
├── cli.py               # CLI 命令（init, start, chat）
├── server.py            # FastAPI 服务
├── types.py             # AgentState, MessageRole 枚举
├── core/
│   ├── agent.py         # ContextAgent 实现
│   ├── llm.py           # LLMClient（兼容 OpenAI）
│   └── prompt_engine.py # Jinja2 模板渲染
├── memory/
│   ├── db.py            # 数据库初始化
│   ├── models.py        # SQLAlchemy 模型
│   └── manager.py       # SessionManager
├── tools/
│   ├── registry.py      # @tool 装饰器和 ToolRegistry
│   ├── sandbox.py       # Python 沙箱（SafeExecutor）
│   ├── shell_env.py     # Shell 沙箱
│   └── builtin/
│       └── shell.py     # shell_execute 工具
└── prompts/
    └── system.j2        # System Prompt 模板
```

---

## License

MIT License
