#!/usr/bin/env python3
"""
Client for agtw server via WebSocket
Supports both one-shot commands and REPL shell mode
"""

import asyncio
import json
import os
import sys
from typing import Optional

import websockets

CONFIG_DIR = os.path.expanduser("~/.agtw")
CONFIG_FILE = os.path.join(CONFIG_DIR, "client.json")


class Client:
    """WebSocket Client for connecting to agtw server"""

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8765
    WS_PATH = "/ws"

    def __init__(self, host: str = None, port: int = None):
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.url = f"ws://{self.host}:{self.port}{self.WS_PATH}"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self._load_config()

    def _load_config(self):
        """Load client config from file"""
        self.current_session: Optional[str] = None
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if data.get("host") == self.host and data.get("port") == self.port:
                        self.current_session = data.get("current_session")
        except:
            pass

    def _save_config(self):
        """Save client config to file"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = {
            "host": self.host,
            "port": self.port,
            "current_session": self.current_session,
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    async def _connect(self):
        """Establish WebSocket connection"""
        if self.ws:
            return
        self.ws = await websockets.connect(self.url)
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("type") == "connected":
            self.client_id = data.get("client_id")

    async def _send(self, cmd: str, *args, **kwargs) -> dict:
        """Send command and return response"""
        await self._connect()
        if self.current_session and cmd not in (
            "session.new",
            "session.join",
            "session.leave",
            "session.list",
            "session.delete",
            "status",
        ):
            kwargs["session_id"] = self.current_session
        request = {"cmd": cmd, "args": list(args), "kwargs": kwargs}
        await self.ws.send(json.dumps(request))

        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            if "status" in data:
                break
            if data.get("type") == "connected":
                continue

        if data.get("current_session"):
            self.current_session = data["current_session"]
            self._save_config()

        return data

    async def _close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.ws = None

    def send(self, cmd: str, *args, **kwargs) -> dict:
        """One-shot: connect, send, disconnect"""
        return asyncio.run(self._send_and_close(cmd, *args, **kwargs))

    async def _send_and_close(self, cmd: str, *args, **kwargs) -> dict:
        try:
            return await self._send(cmd, *args, **kwargs)
        finally:
            await self._close()

    async def shell_async(self):
        """REPL shell mode with persistent connection"""
        await self._connect()

        print(f"已連線到 {self.url}")
        print("輸入 help 查看指令，exit 或 quit 結束")
        print()

        async def receive_messages():
            """Background task to receive server push messages"""
            try:
                while True:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
                    data = json.loads(msg)
                    self._handle_push(data)
            except asyncio.TimeoutError:
                pass
            except websockets.exceptions.ConnectionClosed:
                print("\n[連線已斷開]")
                sys.exit(1)

        while True:
            try:
                asyncio.create_task(receive_messages())

                prompt = self._get_prompt()
                try:
                    user_input = input(prompt)
                except (EOFError, KeyboardInterrupt):
                    print("\n再見！")
                    break

                if not user_input.strip():
                    continue

                if user_input in ("exit", "quit", "disconnect"):
                    print("再見！")
                    break

                result = await self._handle_input(user_input)
                if result == "exit":
                    break

            except KeyboardInterrupt:
                print("\n再見！")
                break

        await self._close()

    def shell(self):
        """Start REPL shell mode"""
        asyncio.run(self.shell_async())

    def _get_prompt(self) -> str:
        """Get shell prompt with current session"""
        if self.current_session:
            return f"[{self.current_session[:8]}] agtw> "
        return "[無 session] agtw> "

    def _handle_push(self, data: dict):
        """Handle push messages from server"""
        msg_type = data.get("type", "")

        if msg_type == "session_created":
            print(
                f"\n← [伺服器] 新 session 建立：{data['session']['name']} (id={data['session']['id'][:8]})"
            )

        elif msg_type == "session_deleted":
            print(f"\n← [伺服器] Session 已刪除：{data['session_id'][:8]}")

        elif msg_type == "agent_started":
            print(f"\n← [伺服器] Agent 啟動：{data['agent']['name']}")

        elif msg_type == "client_joined":
            print(f"\n← [伺服器] {data['client_id']} 加入 session")

        elif msg_type == "client_left":
            print(f"\n← [伺服器] {data['client_id']} 離開 session")

    async def _handle_input(self, user_input: str) -> str:
        """Parse and handle user input"""
        parts = user_input.split(maxsplit=1)
        cmd = parts[0] if parts else ""
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self._print_help()
            return

        if cmd == "session":
            if not arg:
                print("用法：session new|list|join|leave|delete")
                return
            subcmd, subarg = arg.split(maxsplit=1) if " " in arg else (arg, "")
            if subcmd == "new":
                result = await self._send("session.new", subarg if subarg else None)
            elif subcmd == "list":
                result = await self._send("session.list")
            elif subcmd == "join":
                result = await self._send("session.join", subarg)
            elif subcmd == "leave":
                result = await self._send("session.leave")
            elif subcmd == "delete":
                result = await self._send("session.delete", subarg)
            else:
                print(f"未知指令：session {subcmd}")
                return
            self._print_result(result)
            return

        if cmd == "agent":
            if not arg:
                print("用法：agent list|exec|eval")
                return
            subcmd, subarg = arg.split(maxsplit=1) if " " in arg else (arg, "")
            if subcmd == "list":
                result = await self._send("agent.list")
            elif subcmd == "exec":
                result = await self._send("agent.exec", subarg)
            elif subcmd == "eval":
                result = await self._send("agent.eval", subarg)
            else:
                print(f"未知指令：agent {subcmd}")
                return
            self._print_result(result)
            return

        if cmd == "planner":
            result = await self._send("planner", arg)
            self._print_result(result)
            return

        if cmd == "status":
            result = await self._send("status")
            self._print_result(result)
            return

        print(f"未知指令：{cmd}，輸入 help 查看說明")

    def _print_help(self):
        """Print help message"""
        print("""
可用指令：
  session new [name]   - 建立新 session
  session list         - 列出所有 session
  session join <id>    - 加入 session
  session leave        - 離開目前 session
  session delete <id>  - 刪除 session
  agent list           - 列出 agents
  agent exec <task>    - 建立 executor
  agent eval <desc>    - 建立 evaluator
  planner <prompt>     - 執行 planner
  status               - 顯示狀態
  exit, quit           - 結束程式
        """)

    def _print_result(self, result: dict):
        """Print command result"""
        if result["status"] == "ok":
            for key, value in result.items():
                if key != "status" and key != "current_session":
                    print(f"{key}: {value}")
        else:
            print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)

    def session_new(self, name: str = None) -> dict:
        """Create a new session"""
        return self.send("session.new", name)

    def session_list(self) -> dict:
        """List all sessions"""
        return self.send("session.list")

    def session_join(self, session_id: str) -> dict:
        """Join a session"""
        return self.send("session.join", session_id)

    def session_leave(self) -> dict:
        """Leave current session"""
        return self.send("session.leave")

    def session_delete(self, session_id: str) -> dict:
        """Delete a session"""
        return self.send("session.delete", session_id)

    def agent_list(self) -> dict:
        """List agents in current session"""
        return self.send("agent.list")

    def agent_exec(self, task: str) -> dict:
        """Create and run an executor"""
        return self.send("agent.exec", task)

    def agent_eval(self, desc: str) -> dict:
        """Create an evaluator"""
        return self.send("agent.eval", desc)

    def planner(self, prompt: str) -> dict:
        """Run planner with a prompt"""
        return self.send("planner", prompt)

    def status(self) -> dict:
        """Get server status"""
        return self.send("status")
