#!/usr/bin/env python3
"""
Server daemon for agtw system
Handles requests from CLI clients via WebSocket
"""

import asyncio
import json
import os
import sys
import uuid
from typing import Optional

import websockets
from websockets.server import WebSocketServerProtocol

from .agents import call_ollama
from .session import SessionManager


class ServerState:
    def __init__(self, model: str):
        self.model = model
        self.session_manager = SessionManager(model)
        self.session_manager.create_session("main")
        self.clients: dict[str, dict] = {}

    async def broadcast(self, message: dict, exclude: set[str] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        disconnected = []
        for client_id, client in self.clients.items():
            if client_id in exclude:
                continue
            try:
                await client["ws"].send(json.dumps(message))
            except:
                disconnected.append(client_id)
        for client_id in disconnected:
            del self.clients[client_id]


class Server:
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8765
    WS_PATH = "/ws"

    def __init__(
        self, host: str = None, port: int = None, model: str = "minimax-m2.5:cloud"
    ):
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.model = model
        self.state = ServerState(model)
        self.server = None
        self._running = False

    async def _handle_client(self, ws: WebSocketServerProtocol):
        """Handle a WebSocket client connection"""
        client_id = str(uuid.uuid4())[:8]
        self.state.clients[client_id] = {
            "ws": ws,
            "session_id": None,
            "connected_at": asyncio.get_event_loop().time(),
        }

        try:
            await ws.send(
                json.dumps(
                    {
                        "type": "connected",
                        "client_id": client_id,
                        "message": f"已連線，請使用 session join 加入 session",
                    }
                )
            )

            async for message in ws:
                try:
                    request = json.loads(message)
                    response = await self._process_request(client_id, request)
                    await ws.send(json.dumps(response))
                except json.JSONDecodeError:
                    await ws.send(
                        json.dumps(
                            {
                                "status": "error",
                                "message": "無效的 JSON 格式",
                            }
                        )
                    )
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if client_id in self.state.clients:
                del self.state.clients[client_id]

    async def _process_request(self, client_id: str, request: dict) -> dict:
        """Process a request and return response"""
        cmd = request.get("cmd", "")
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})

        if client_id not in self.state.clients:
            self.state.clients[client_id] = {"session_id": None, "ws": None}
        client = self.state.clients[client_id]

        if kwargs.get("session_id"):
            client["session_id"] = kwargs["session_id"]

        handlers = {
            "session.new": self._cmd_session_new,
            "session.list": self._cmd_session_list,
            "session.join": self._cmd_session_join,
            "session.leave": self._cmd_session_leave,
            "session.delete": self._cmd_session_delete,
            "agent.list": self._cmd_agent_list,
            "agent.exec": self._cmd_agent_exec,
            "agent.eval": self._cmd_agent_eval,
            "planner": self._cmd_planner,
            "status": self._cmd_status,
        }

        handler = handlers.get(cmd)
        if not handler:
            return {"status": "error", "message": f"未知命令：{cmd}"}

        return await handler(client_id, client, args, kwargs)

    async def _cmd_session_new(
        self, client_id: str, client: dict, args, kwargs
    ) -> dict:
        name = args[0] if args else kwargs.get("name")
        session = self.state.session_manager.create_session(name)
        self.state.clients[client_id]["session_id"] = session.id

        await self.state.broadcast(
            {
                "type": "session_created",
                "session": {"id": session.id, "name": session.name},
                "by": client_id,
            }
        )

        return {
            "status": "ok",
            "session": {"id": session.id, "name": session.name},
            "current_session": session.id,
        }

    async def _cmd_session_list(
        self, client_id: str, client: dict, args, kwargs
    ) -> dict:
        sessions = []
        for name, s in self.state.session_manager.sessions.items():
            if name != s.id:
                watching = [
                    cid
                    for cid, c in self.state.clients.items()
                    if c.get("session_id") == s.id
                ]
                sessions.append(
                    {
                        "id": s.id,
                        "name": s.name,
                        "watching": watching,
                        "is_current": self.state.clients.get(client_id, {}).get(
                            "session_id"
                        )
                        == s.id,
                    }
                )

        return {
            "status": "ok",
            "sessions": sessions,
        }

    async def _cmd_session_join(
        self, client_id: str, client: dict, args, kwargs
    ) -> dict:
        session_id = args[0] if args else kwargs.get("id", "")
        session = self.state.session_manager.switch_session(session_id)

        if not session:
            return {"status": "error", "message": f"找不到 session：{session_id}"}

        self.state.clients[client_id]["session_id"] = session.id

        await self.state.broadcast(
            {
                "type": "client_joined",
                "client_id": client_id,
                "session": {"id": session.id, "name": session.name},
            }
        )

        return {
            "status": "ok",
            "session": {"id": session.id, "name": session.name},
            "current_session": session.id,
        }

    async def _cmd_session_leave(
        self, client_id: str, client: dict, args, kwargs
    ) -> dict:
        if not client.get("session_id"):
            return {"status": "error", "message": "目前不在任何 session 中"}

        old_session_id = client["session_id"]
        client["session_id"] = None

        await self.state.broadcast(
            {
                "type": "client_left",
                "client_id": client_id,
                "session_id": old_session_id,
            }
        )

        return {"status": "ok", "message": "已離開 session"}

    async def _cmd_session_delete(
        self, client_id: str, client: dict, args, kwargs
    ) -> dict:
        session_id = args[0] if args else kwargs.get("id", "")
        session = self.state.session_manager.sessions.get(session_id)

        if not session:
            return {"status": "error", "message": f"找不到 session：{session_id}"}

        if self.state.session_manager.delete_session(session_id):
            await self.state.broadcast(
                {
                    "type": "session_deleted",
                    "session_id": session_id,
                }
            )
            return {"status": "ok"}
        return {"status": "error", "message": f"刪除失敗：{session_id}"}

    async def _cmd_agent_list(self, client_id: str, client: dict, args, kwargs) -> dict:
        session_id = client.get("session_id")
        if not session_id:
            return {"status": "error", "message": "請先加入 session（session join）"}

        session = self.state.session_manager.sessions.get(session_id)
        if not session:
            return {"status": "error", "message": f"找不到 session：{session_id}"}

        return {
            "status": "ok",
            "agents": session.list_agents(),
            "session_id": session_id,
        }

    async def _cmd_agent_exec(self, client_id: str, client: dict, args, kwargs) -> dict:
        task = args[0] if args else ""
        session_id = client.get("session_id")

        if not session_id:
            return {"status": "error", "message": "請先加入 session"}

        session = self.state.session_manager.sessions.get(session_id)
        if not session:
            return {"status": "error", "message": f"找不到 session"}

        executor = session.create_executor(task)

        await self.state.broadcast(
            {
                "type": "agent_started",
                "agent": {"name": executor.name, "task": task},
                "session_id": session_id,
            }
        )

        return {
            "status": "ok",
            "executor": {"name": executor.name, "task": task},
        }

    async def _cmd_agent_eval(self, client_id: str, client: dict, args, kwargs) -> dict:
        desc = args[0] if args else ""
        session_id = client.get("session_id")

        if not session_id:
            return {"status": "error", "message": "請先加入 session"}

        session = self.state.session_manager.sessions.get(session_id)
        if not session:
            return {"status": "error", "message": f"找不到 session"}

        evaluator = session.create_evaluator()

        await self.state.broadcast(
            {
                "type": "agent_started",
                "agent": {"name": evaluator.name, "desc": desc},
                "session_id": session_id,
            }
        )

        return {
            "status": "ok",
            "evaluator": {"name": evaluator.name, "desc": desc},
        }

    async def _cmd_planner(self, client_id: str, client: dict, args, kwargs) -> dict:
        prompt = args[0] if args else ""
        session_id = client.get("session_id")

        if not session_id:
            return {"status": "error", "message": "請先加入 session"}

        session = self.state.session_manager.sessions.get(session_id)
        if not session:
            return {"status": "error", "message": f"找不到 session"}

        try:
            response = await session.planner.think(prompt)
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _cmd_status(self, client_id: str, client: dict, args, kwargs) -> dict:
        session_id = client.get("session_id")
        session = (
            self.state.session_manager.sessions.get(session_id) if session_id else None
        )

        return {
            "status": "ok",
            "model": self.model,
            "current_session": {
                "id": session.id,
                "name": session.name,
            }
            if session
            else None,
            "client_id": client_id,
            "connected_clients": len(self.state.clients),
        }

    async def start_async(self):
        """Start the WebSocket server"""
        self._running = True
        url = f"ws://{self.host}:{self.port}{self.WS_PATH}"

        print(f"agtw server 啟動中...")
        print(f"  主機：{self.host}")
        print(f"  連接埠：{self.port}")
        print(f"  WebSocket：{url}")
        print(f"  模型：{self.model}")
        print(f"  工作區：{os.path.expanduser('~/.agtw')}")
        print()

        self.server = await websockets.serve(self._handle_client, self.host, self.port)

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass

    def start(self):
        """Start the server (blocking)"""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            print("\n正在關閉伺服器...")
            self.stop()

    def stop(self):
        """Stop the server"""
        self._running = False
        if self.server:
            self.server.close()
        self.state.session_manager.shutdown_all()
        print("伺服器已關閉")


def start_server(host: str = None, port: int = None, model: str = "minimax-m2.5:cloud"):
    """Start the agtw server"""
    server = Server(host, port, model)
    server.start()
