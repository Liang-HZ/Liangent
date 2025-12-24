# Liangent: Minimalist Lightweight Agent

[![PyPI version](https://badge.fury.io/py/liangent.svg)](https://badge.fury.io/py/liangent)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/YOUR_USERNAME/liangent/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/liangent/actions/workflows/ci.yml)

> **Slogan**: Minimalist lightweight agent, your first usable agent.

[English](README.md) | [中文](README_CN.md)


---

**Liangent** is a lightweight, extensible, and memory-aware agent framework designed for building LLM-based applications. It is designed to be a **teaching prototype** and a practical solution for **simple tasks**.

Unlike complex frameworks that rely on heavy planning steps, Liangent focuses on solving problems through **forced tool usage constraints** and **dynamic prompt injection**. This approach significantly reduces hallucinations and improves usability for everyday tasks.

---

## ✨ Key Features

### 🛡️ Local Code Sandbox
- Safely execute **Python code** with AST-based validation
- Safely execute **Shell commands** with whitelist/blacklist control
- **Double Security Guarantee**:
  - Python: Allowed modules whitelist (`math`, `datetime`, `json`, `random`, `re`, `collections`, `itertools`, `functools`, `statistics`)
  - Python: Blacklisted built-in functions (`open`, `exec`, `eval`, `compile`, etc.)
  - Shell: Command whitelist (`python3`, `ls`, `grep`, `cat`, `date`, `find`)
  - Shell: Dangerous pattern blocking (`;`, `&`, `` ` ``, `$(`)
- Process isolation with timeout protection

### 📉 Hallucination Reduction via Dynamic Constraints
- **Minimum Tool Usage (`min_tool_use`)**: Force the agent to use tools before answering
- **Maximum Tool Usage (`max_tool_use`)**: Prevent infinite tool calling loops
- **Dynamic Prompt Injection**: If the agent attempts to answer too early, the system intercepts and forces reflection

### 🔧 Simple Tool Registration
- Register tools using a simple `@tool` decorator
- **Dual Mode Support**:
  - **Native Function Calling**: Works with models that support FC API (GPT-4, Claude 3, etc.)
  - **Prompt-based Mode**: Parses JSON from text output, compatible with any LLM
- Automatic JSON Schema generation from Google-style docstrings

### 💾 Minimalist SQLite Storage
- Zero-config persistent sessions and logs
- Full traceability for every step
- Support for PostgreSQL and other databases

### 🔍 High Observability
- `verbose=True`: See tool calls, thoughts, and results
- `debug=True`: See token usage, costs, and detailed step info
- `show_prompts=True`: See complete prompts (System + History) sent to LLM

### ☁️ Serverless Ready
- Built-in `fc_handler.py` for Aliyun Function Compute
- Adaptable to AWS Lambda, Google Cloud Functions, etc.

---

## 🚀 Getting Started

### 1. Installation
```bash
pip install liangent
```

### 2. Initialize Project
```bash
liangent init
```
This generates:
- `.env`: Configuration file (API Keys, limits, etc.)
- `AGENTS.md`: Agent identity and behavior guidelines

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# Tool Usage Policy
MIN_TOOL_USE=1
MAX_TOOL_USE=15
MAX_STEPS=20

# Enable native function calling for supported models
SUPPORTS_FUNCTION_CALLING=False
```

### 3. Basic Usage

#### Synchronous Chat
```python
from liangent import Liangent

client = Liangent(verbose=True)
response = client.chat("What is 123 * 456?")
print(response)
```

#### Streaming Mode
```python
from liangent import Liangent

client = Liangent()

for event in client.stream("List files in current directory"):
    evt_type = event.get("event")
    
    if evt_type == "thought":
        print(f"[Thinking] {event.get('content')}")
    elif evt_type == "item.started":
        item = event.get("data", {}).get("item", {})
        print(f"[Tool Call] {item.get('tool')}({item.get('args')})")
    elif evt_type == "item.completed":
        item = event.get("data", {}).get("item", {})
        print(f"[Tool Result] {item.get('aggregated_output')}")
    elif evt_type == "final_answer":
        print(f"[Answer] {event.get('content')}")
    elif evt_type == "usage_stats":
        content = event.get("content", {})
        print(f"[Usage] {content.get('usage')}")
        print(f"[Cost] {content.get('cost')}")
```

---

## ⚙️ Configuration Options

### Liangent Client Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | None | OpenAI API Key (falls back to env) |
| `base_url` | str | None | OpenAI Base URL (falls back to env) |
| `model_name` | str | None | Model name (falls back to env) |
| `db_url` | str | None | Database URL (`:memory:` if not set) |
| `tools` | List[str] | None | List of tool names to enable (all if None) |
| `verbose` | bool | False | Print thinking process and tool execution |
| `debug` | bool | False | Print full debug info (implies verbose) |
| `show_prompts` | bool | False | Print complete prompts for each step |
| `min_tool_use` | int | 1 | Minimum tool calls before final answer |
| `max_tool_use` | int | 15 | Maximum tool calls allowed |
| `max_steps` | int | 20 | Maximum agent steps |

### Example: Forcing Tool Usage
```python
from liangent import Liangent

# Agent must use at least 2 tools before answering
client = Liangent(
    min_tool_use=2,
    max_tool_use=10,
    max_steps=15,
    verbose=True
)

response = client.chat("What's the weather like?")
```

---

## 🖥️ CLI Commands

### Interactive Chat
```bash
liangent chat
```

### Start API Server
```bash
liangent start --port 8000
```
- API Endpoint: `http://localhost:8000/api/chat`
- API Docs: `http://localhost:8000/docs`

### Initialize Configuration
```bash
liangent init
```

---

## 🔧 Custom Tools

Register custom tools using the `@tool` decorator. **Google-style docstrings are mandatory** as they generate the tool schema.

```python
from liangent import tool

@tool
def get_weather(city: str, unit: str = "celsius") -> str:
    """
    Get current weather for a city.
    
    Args:
        city: Name of the city.
        unit: Temperature unit (celsius or fahrenheit).
    """
    # Your implementation
    return f"Weather in {city}: 22°C, Sunny"

@tool
def search_database(query: str, limit: int = 10) -> list:
    """
    Search the database for records.
    
    Args:
        query: Search query string.
        limit: Maximum number of results.
    """
    # Your implementation
    return [{"id": 1, "name": "Result 1"}]
```

### Built-in Tools
- `python`: Execute Python code in sandbox
- `shell_execute`: Execute shell commands with security restrictions

---

## 📝 Customizing Agent Behavior

The `AGENTS.md` file defines your agent's persona and rules. It is automatically injected into the System Prompt.

```markdown
# Agent Guidelines

## Identity
You are a senior Python engineer with expertise in data analysis.

## Behavior Rules
- Be concise and professional
- Always verify code logic using the python tool
- When handling file operations, list files first before reading

## Domain Knowledge
- Python best practices
- Data analysis workflows
```

---

## 🌐 API Server

### Endpoint: POST `/api/chat`

#### Request Body
```json
{
    "query": "Your question here",
    "session_id": "optional-session-id",
    "user_id": "default_user",
    "stream": true
}
```

#### SSE Events (when `stream=true`)
| Event | Description |
|-------|-------------|
| `meta` | Session metadata |
| `status` | Current step status |
| `thought` | Agent's thinking process |
| `item.started` | Tool execution started |
| `item.completed` | Tool execution completed |
| `final_answer` | Final response |
| `done` | Completion with usage stats |
| `error` | Error occurred |

---

## ☁️ Serverless Deployment

### Aliyun Function Compute

1. Set environment variables in FC console:
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `MODEL_NAME`

2. Use `fc_handler.py` as entry point:
```python
# fc_handler.py is included in the package
# Handler function: handler
```

3. Deploy and invoke:
```json
{
    "query": "Calculate 123 * 456"
}
```

---

## 📊 Event Types Reference

| Event | Data Fields | Description |
|-------|-------------|-------------|
| `input_received` | `content` | User query received |
| `status` | `content` | Step status (e.g., "Thinking (Step 1)...") |
| `thought` | `content` | Agent's reasoning |
| `item.started` | `data.item.id`, `tool`, `args` | Tool execution begins |
| `item.completed` | `data.item.id`, `tool`, `aggregated_output`, `exit_code` | Tool execution ends |
| `prompt_info` | `data.step`, `system_prompt`, `history` | Full prompt details |
| `debug` | `data.step`, `current_usage`, `total_cost` | Debug statistics |
| `final_answer` | `content` | Final response |
| `usage_stats` | `content.usage`, `content.cost` | Token usage and costs |
| `error` | `content` | Error message |

---

## 🔒 Security Features

### Python Sandbox
- **Allowed Modules**: `math`, `datetime`, `json`, `random`, `re`, `collections`, `itertools`, `functools`, `statistics`
- **Blocked Functions**: `open`, `exec`, `eval`, `compile`, `input`, `globals`, `locals`
- **Process Isolation**: 5-second timeout, separate process execution
- **AST Validation**: Pre-execution security check

### Shell Sandbox
- **Allowed Commands**: `python3`, `ls`, `grep`, `cat`, `date`, `find`
- **Blocked Patterns**: `;`, `&`, `` ` ``, `$(`
- **Path Restriction**: No `..` traversal, project directory only
- **Timeout**: 60 seconds default

---

## 📦 Project Structure

```
liangent/
├── __init__.py          # Exports: Liangent, tool
├── client.py            # High-level Liangent client
├── config.py            # Settings and init_config
├── cli.py               # CLI commands (init, start, chat)
├── server.py            # FastAPI server
├── types.py             # AgentState, MessageRole enums
├── core/
│   ├── agent.py         # ContextAgent implementation
│   ├── llm.py           # LLMClient (OpenAI compatible)
│   └── prompt_engine.py # Jinja2 template rendering
├── memory/
│   ├── db.py            # Database initialization
│   ├── models.py        # SQLAlchemy models
│   └── manager.py       # SessionManager
├── tools/
│   ├── registry.py      # @tool decorator and ToolRegistry
│   ├── sandbox.py       # Python sandbox (SafeExecutor)
│   ├── shell_env.py     # Shell sandbox
│   └── builtin/
│       └── shell.py     # shell_execute tool
└── prompts/
    └── system.j2        # System prompt template
```

---

## License

MIT License