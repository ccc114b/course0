# agtw - Agent Team Work

一個類似 Git/Docker CLI 的多智能體協調系統。

[![PyPI version](https://badge.fury.io/py/agtw.svg)](https://badge.fury.io/py/agtw)
[![GitHub](https://img.shields.io/github/license/ccc-py/agtw)](https://github.com/ccc-py/agtw)

## 功能特色

- **Session 管理** - 建立、加入、刪除工作階段
- **多元代理** - Planner（規劃）、Executor（執行）、Evaluator（評估）
- **安全審查** - Shell 命令由 Guard 代理審查後才執行
- **WebSocket 伺服器** - 持久化連線，支援推播
- **雙模式 CLI** - 支援 One-shot 指令和 REPL 互動模式
- **Session 持久化** - 用戶端自動記憶當前 session

## 安裝

```bash
pip install agtw
```

或開發模式：

```bash
git clone https://github.com/ccc-py/agtw.git
cd agtw
pip install -e ".[dev]"
```

## 快速開始

### One-shot 模式

```bash
# 啟動伺服器
agtw server

# 在另一終端：
agtw session new myproject          # 建立 session
agtw session join myproject         # 加入 session
agtw agent exec "寫一個 hello.py"  # 建立 executor
agtw agent list                     # 列出 agents
```

### REPL 互動模式

```bash
agtw shell

[無 session] agtw> session new myproject
[myproject] agtw> agent exec "寫 hello"
[myproject] agtw> agent list
[myproject] agtw> exit
```

## 指令列表

### 伺服器

| 指令 | 說明 |
|------|------|
| `agtw server` | 啟動 agtw 伺服器 |

### Session 管理

| 指令 | 說明 |
|------|------|
| `agtw session new [name]` | 建立新 session |
| `agtw session list` | 列出所有 sessions |
| `agtw session join <id>` | 加入 session |
| `agtw session leave` | 離開目前 session |
| `agtw session delete <id>` | 刪除 session |

### Agent 操作

| 指令 | 說明 |
|------|------|
| `agtw agent list` | 列出目前 session 的 agents |
| `agtw agent exec <task>` | 建立 executor |
| `agtw agent eval <desc>` | 建立 evaluator |

### 其他

| 指令 | 說明 |
|------|------|
| `agtw planner <prompt>` | 執行 planner |
| `agtw status` | 顯示狀態 |
| `agtw shell` | 進入 REPL 互動模式 |

## 系統架構

```
┌─────────────────────────────────────────────────┐
│                   agtw CLI                      │
│         (One-shot 或 REPL 模式)                  │
└─────────────────┬───────────────────────────────┘
                  │ WebSocket
┌─────────────────▼───────────────────────────────┐
│               agtw Server                       │
│  ┌─────────────────────────────────────────┐   │
│  │           SessionManager               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │ Session │ │ Session │ │ Session │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Planner│ │  │Planner│ │  │Planner│ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Exec │ │ │  │Exec │ │ │  │Exec │ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  │  ┌────┐ │ │  ┌────┐ │ │  ┌────┐ │  │   │
│  │  │  │Eval │ │ │  │Eval │ │ │  │Eval │ │  │   │
│  │  │  └────┘ │ │  └────┘ │ │  └────┘ │  │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘  │   │
│  │       └───────────┼───────────┘       │   │
│  │              ┌────▼────┐               │   │
│  │              │  Guard  │               │   │
│  │              └────┬────┘               │   │
│  └──────────────────┼─────────────────────┘   │
└─────────────────────┼───────────────────────────┘
                      │ Shell Commands
              ┌───────▼───────┐
              │    System     │
              └───────────────┘
```

## 代理說明

- **Planner** - 分析需求、規劃任務、協調團隊
- **Executor** - 執行 Planner 交辦的具體任務
- **Evaluator** - 驗證 Executor 的執行結果
- **Guard** - 安全審查員，檢查 Shell 命令是否危險

## 開發指令

```bash
# 執行測試
python -m pytest tests/ -v

# 打包上傳 PyPI
python -m build
twine upload dist/*
```

## 依賴

- Python >= 3.10
- aiohttp >= 3.8.0
- websockets >= 10.0

## License

MIT
