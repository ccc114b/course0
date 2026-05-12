# AGTW 系統設計報告

## 1. 系統概述

AGTW (Agent Team Work) 是一個類似 Git/Docker CLI 風格的多智能體協調系統。系統透過命令列介面提供 session 管理、多代理協作和安全審查功能。

### 1.1 設計目標

- **易用性**：提供直覺的 Git 風格命令列工具
- **可擴展性**：支援多元代理架構
- **安全性**：Shell 命令審查機制
- **持久化**：Session 狀態跨連線保持
- **雙模式支援**：One-shot 和 REPL 互動模式

### 1.2 核心元件

```
┌──────────────────────────────────────────────┐
│                  AGTW 系統                   │
├──────────────────────────────────────────────┤
│  CLI 層 (client.py, cli.py)                │
│    - One-shot 指令模式                      │
│    - REPL 互動模式                          │
├──────────────────────────────────────────────┤
│  通訊層 (WebSocket)                         │
│    - 持久連線支援                            │
│    - 雙向訊息傳遞                            │
│    - 推播通知                                │
├──────────────────────────────────────────────┤
│  伺服器層 (server.py)                       │
│    - Session 管理                            │
│    - 代理協調                                │
│    - 廣播機制                                │
├──────────────────────────────────────────────┤
│  代理層 (agents.py)                         │
│    - Planner (規劃)                          │
│    - Executor (執行)                         │
│    - Evaluator (評估)                        │
│    - Guard (安全審查)                         │
├──────────────────────────────────────────────┤
│  Session 層 (session.py)                    │
│    - SessionManager                          │
│    - Session                                 │
└──────────────────────────────────────────────┘
```

## 2. 系統架構

### 2.1 整體架構

系統採用客戶端-伺服器架構，客戶端透過 WebSocket 與伺服器通訊。設計靈感來自 Docker CLI 和 Git 的命令模式，提供一致的使用者體驗。

```
┌─────────────┐         WebSocket          ┌─────────────┐
│   Client A   │ ◄────────────────────────► │   Server    │
│ session: p1  │                            │             │
└─────────────┘                            │ Session[p1] │ ◄── A
                                          │ Session[p2] │ ◄── B
┌─────────────┐                            │ Session[p3] │    (無客戶端)
│   Client B   │ ◄────────────────────────► │             │
│ session: p2  │                            └─────────────┘
└─────────────┘
```

### 2.2 元件職責

**CLI 層 (`cli.py`)**：負責解析命令列參數、呼叫客戶端功能、提供使用說明。

**客戶端層 (`client.py`)**：處理 WebSocket 連線管理、請求發送、Session 持久化（寫入 ~/.agtw/client.json）。

**伺服器層 (`server.py`)**：管理 WebSocket 連線、處理請求、協調各 Session 和代理。

**代理層 (`agents.py`)**：定義 Planner、Executor、Evaluator、Guard 四種代理型態。

**Session 層 (`session.py`)**：管理 Session 生命週期、代理實例、狀態持久化。

### 2.3 通訊協定

使用 JSON 格式的 WebSocket 訊息：

**請求格式**：
```json
{
  "cmd": "agent.exec",
  "args": ["Write hello world"],
  "kwargs": {}
}
```

**回應格式**：
```json
{
  "status": "ok",
  "executor": {"name": "Executor[main-1]", "task": "Write hello world"}
}
```

**推播格式**：
```json
{
  "type": "agent_started",
  "agent": {"name": "Executor[main-1]"},
  "session_id": "abc123"
}
```

## 3. 代理系統設計

### 3.1 代理型態

系統定義四種代理型態，各司其職：

| 代理 | 職責 | 主要方法 |
|------|------|---------|
| Planner | 分析需求、規劃任務 | `think()`, `request_exec()`, `request_eval()` |
| Executor | 執行具體任務 | `execute_shell()` |
| Evaluator | 驗證執行結果 | `follow()` 追蹤 Executor |
| Guard | 安全審查 Shell 命令 | `review_command()`, `check_and_execute()` |

### 3.2 Planner 設計

Planner 是團隊的協調者，負責：
- 分析使用者需求
- 分解任務為子任務
- 指派 Executor 執行任務
- 要求 Evaluator 驗證結果

Planner 使用 XML 風格的標籤與系統互動：
```xml
<shell> ls -la </shell>     <!-- 執行 Shell 命令 -->
<exec> 寫一個函式 </exec>    <!-- 請求 Executor -->
<eval> 檢查程式品質 </eval>  <!-- 請求 Evaluator -->
<end/>                       <!-- 完成回覆 -->
```

### 3.3 Executor 設計

Executor 負責執行 Planner 交辦的具體任務：
- 寫入或修改程式碼
- 執行開發工具
- 處理檔案操作
- 執行自動測試

每個 Executor 有獨立的工作執行緒，透過任務佇列接收 Planner 的指令。

### 3.4 Evaluator 設計

Evaluator 負責驗證 Executor 的執行結果：
- 檢查程式是否正確執行
- 驗證輸出是否符合預期
- 確認檔案是否正確建立/修改
- 提供改進建議

Evaluator 可以追蹤多個 Executor（透過 `follow()` 方法）。

### 3.5 Guard 設計

Guard 是安全審查員，防止危險操作：
- 攔截所有 Shell 命令
- 使用 LLM 判斷命令安全性
- 檢查是否存取本目錄外的檔案
- 必要時詢問使用者確認

安全原則：
1. 允許讀取檔案、瀏覽目錄
2. 允許無害的開發工具（git, ls, grep 等）
3. 禁止刪除資料的命令（rm -rf, dd 等）
4. 禁止修改系統的命令（sudo, chmod 777 等）

## 4. Session 管理

### 4.1 Session 概念

Session 代表一個獨立的工作執行緒，類似 Git 的分支概念：
- 每個 Session 有自己的 Planner、Executors、Evaluators
- 多個 Session 可同時存在於同一伺服器
- 每個 Client 可加入一個 Session

### 4.2 SessionManager

SessionManager 負責管理所有 Session：
```python
class SessionManager:
    model: str                           # Ollama 模型名稱
    sessions: dict[str, Session]         # Session 映射表
    current_session: Optional[Session]   # 當前 Session
    guard: Guard                         # 共享的安全審查員
```

### 4.3 Session 生命週期

```
建立 → 加入 → 使用 → 離開 → 刪除
  │       │       │       │       │
  ▼       ▼       ▼       ▼       ▼
 session.new  session.join  agent.*  session.leave  session.delete
```

### 4.4 Session 持久化

Session 狀態可序列化保存：
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "name": self.name,
        "model": self.model,
        "planner": self.planner.to_dict(),
        "executors": [e.to_dict() for e in self.executors],
        "evaluators": [ev.to_dict() for ev in self.evaluators],
    }
```

## 5. 客戶端設計

### 5.1 雙模式支援

客戶端支援兩種使用模式：

**One-shot 模式**：
```bash
agtw session new myproject
agtw agent exec "Write hello"
```
每次指令建立新連線，適合腳本化和自動化。

**REPL 模式**：
```bash
agtw shell
[myproject] agtw> agent exec "Write hello"
```
維持持久連線，適合互動式操作和監控。

### 5.2 Session 持久化

為了解決 One-shot 模式下 Session 狀態保持問題，客戶端將當前 Session ID 寫入設定檔：

```python
CONFIG_FILE = "~/.agtw/client.json"

def _save_config(self):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    data = {
        "host": self.host,
        "port": self.port,
        "current_session": self.current_session,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)
```

### 5.3 訊息處理

客戶端處理兩種訊息：

**同步回應**：發送請求後等待回應
**推播訊息**：伺服器主動發送的更新（如 agent 啟動、完成通知）

```python
async def _send(self, cmd, *args, **kwargs):
    await self._connect()
    # ... 發送請求 ...
    while True:
        msg = await self.ws.recv()
        data = json.loads(msg)
        if "status" in data:      # 同步回應
            return data
        if data.get("type"):      # 推播訊息
            self._handle_push(data)
```

## 6. 伺服器設計

### 6.1 架構

伺服器採用 asyncio 架構處理 WebSocket 連線：

```python
class Server:
    state: ServerState                    # 共享狀態
    server: WebSocketServer              # asyncio 伺服器

class ServerState:
    model: str                            # Ollama 模型
    session_manager: SessionManager        # Session 管理
    clients: dict[str, dict]              # 連線的客戶端
```

### 6.2 請求處理

伺服器維護客戶端-工作階段對應關係：

```python
clients: {
    "client_id_1": {
        "ws": WebSocket,
        "session_id": "session_abc",
        "connected_at": timestamp
    },
    "client_id_2": {...}
}
```

請求處理流程：
1. 接收 WebSocket 訊息
2. 解析 JSON 格式的請求
3. 查找或建立客戶端狀態
4. 執行對應的指令處理函式
5. 發送回應

### 6.3 廣播機制

伺服器支援向所有客戶端廣播推播訊息：

```python
async def broadcast(self, message: dict, exclude: set[str] = None):
    for client_id, client in self.clients.items():
        if client_id in exclude:
            continue
        try:
            await client["ws"].send(json.dumps(message))
        except:
            # 處理斷線客戶端
            disconnected.append(client_id)
```

## 7. 安全機制

### 7.1 Shell 命令審查

所有 Shell 命令都經過 Guard 審查：

```python
async def check_and_execute(self, cmd: str, cwd: str) -> tuple[str, str]:
    # 1. LLM 判斷安全性
    is_safe, reason = await self.review_command(cmd)
    if not is_safe:
        return "", f"阻止：{reason}"

    # 2. 檢查目錄外存取
    needs_access, path = check_outside_access(cmd, cwd)
    if needs_access:
        if not self.ask_outside_access(path):
            return "", f"拒絕：{path}"

    # 3. 執行命令
    result = subprocess.run(cmd, ...)
    return output, ""
```

### 7.2 路徑存取檢查

```python
def check_outside_access(cmd: str, cwd: str) -> tuple[bool, str]:
    # 檢查絕對路徑
    # 檢查相對路徑 (..)
    # 確保不超出工作目錄
```

## 8. 使用範例

### 8.1 基本工作流程

```bash
# 啟動伺服器
$ agtw server

# 在另一終端建立 Session
$ agtw session new myproject
已建立 session: myproject (id=abc123)

# 加入 Session
$ agtw session join abc123
已加入 session: myproject

# 建立 Executor 執行任務
$ agtw agent exec "寫一個 hello.py"
已啟動 Executor: Executor[myproject-1]

# 列出 agents
$ agtw agent list
Session: myproject
  Planner: Planner[myproject]
  Executors (1):
    - Executor[myproject-1]
  Evaluators (0):
```

### 8.2 REPL 互動模式

```bash
$ agtw shell
已連線到 ws://localhost:8765/ws
輸入 help 查看指令，exit 或 quit 結束

[無 session] agtw> session new project1
已建立 session: project1
[project1] agtw> agent exec "分析專案結構"
已啟動 Executor

← [伺服器] Executor[project1-1]: 完成

[project1] agtw> agent list
Session: project1
  Planner: Planner[project1]
  Executors (1):
    - Executor[project1-1]
[project1] agtw> exit
再見！
```

## 9. 未來擴展

### 9.1 可能的功能擴展

- **Session 持久化**：將 Session 狀態寫入磁碟
- **遠端代理**：支援在遠端機器執行代理
- **並發 Planner**：多個 Planner 協作
- **代理間通訊**：Executor 可呼叫其他 Executor
- **歷史記錄**：儲存對話歷史供日後查詢

### 9.2 改進方向

- 支援更多 LLM 提供者（OpenAI、Anthropic 等）
- 提供 Web UI 介面
- 增加更多安全檢查規則
- 支援 Session 匯入/匯出
- 增加效能監控儀表板

## 10. 結論

AGTW 提供了一個結構化的多代理協調框架，透過 Git 風格的命令列介面，讓使用者能夠輕鬆管理多個工作階段和代理。系統設計注重安全性和可擴展性，採用 WebSocket 實現持久連線和即時推播支援。

核心設計特點：
1. **模組化代理架構**：Planner、Executor、Evaluator、Guard 各司其職
2. **統一的命令列介面**：Git 風格，直覺易用
3. **雙模式支援**：One-shot 和 REPL 適用不同場景
4. **Session 持久化**：客戶端自動記憶當前工作階段
5. **安全第一**：Shell 命令審查機制防止危險操作
