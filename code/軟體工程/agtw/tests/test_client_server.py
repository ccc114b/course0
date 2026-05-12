#!/usr/bin/env python3
"""
Tests for client and server WebSocket communication
"""

import asyncio
import json
import pytest
import websockets
from agtw.server import Server
from agtw.client import Client


@pytest.fixture
def server():
    """Create a test server instance"""
    server = Server(host="localhost", port=19876, model="test-model")
    return server


class TestServer:
    def test_server_creation(self, server):
        assert server.model == "test-model"
        assert server.port == 19876
        assert len(server.state.session_manager.sessions) >= 2
        assert len(server.state.clients) == 0

    def test_server_state_exists(self, server):
        assert server.state is not None
        assert server.state.session_manager is not None


class TestServerCommands:
    @pytest.mark.asyncio
    async def test_process_status(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_status(client_id, client, [], {})

        assert result["status"] == "ok"
        assert result["model"] == "test-model"
        assert result["client_id"] == client_id
        assert result["current_session"] is None

    @pytest.mark.asyncio
    async def test_process_session_new(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_new(client_id, client, ["my_session"], {})

        assert result["status"] == "ok"
        assert result["session"]["name"] == "my_session"
        assert "id" in result["session"]
        assert result["current_session"] == result["session"]["id"]
        assert client["session_id"] == result["session"]["id"]

    @pytest.mark.asyncio
    async def test_process_session_new_auto_name(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_new(client_id, client, [], {})

        assert result["status"] == "ok"
        assert result["session"]["name"].startswith("session")

    @pytest.mark.asyncio
    async def test_process_session_list(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        await server._cmd_session_new(client_id, client, ["session1"], {})

        server.state.clients["other-client"] = {"session_id": None, "ws": None}
        await server._cmd_session_new(
            "other-client", server.state.clients["other-client"], ["session2"], {}
        )

        result = await server._cmd_session_list(client_id, client, [], {})

        assert result["status"] == "ok"
        assert len(result["sessions"]) >= 2

    @pytest.mark.asyncio
    async def test_process_session_join(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        new_session = await server._cmd_session_new(client_id, client, ["target"], {})
        session_id = new_session["session"]["id"]

        client2 = {"session_id": None, "ws": None}
        server.state.clients["client2"] = client2
        result = await server._cmd_session_join("client2", client2, [session_id], {})

        assert result["status"] == "ok"
        assert result["session"]["name"] == "target"
        assert client2["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_process_session_join_invalid(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_join(client_id, client, ["invalid_id"], {})

        assert result["status"] == "error"
        assert "找不到" in result["message"]

    @pytest.mark.asyncio
    async def test_process_session_leave(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": "some-session", "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_leave(client_id, client, [], {})

        assert result["status"] == "ok"
        assert client["session_id"] is None

    @pytest.mark.asyncio
    async def test_process_session_leave_no_session(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_leave(client_id, client, [], {})

        assert result["status"] == "error"
        assert "不在" in result["message"]

    @pytest.mark.asyncio
    async def test_process_session_delete(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        new_session = await server._cmd_session_new(
            client_id, client, ["to_delete"], {}
        )
        session_id = new_session["session"]["id"]

        result = await server._cmd_session_delete(client_id, client, [session_id], {})

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_process_session_delete_invalid(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_session_delete(client_id, client, ["invalid_id"], {})

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_process_agent_list(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        new_sess = await server._cmd_session_new(client_id, client, [], {})
        client["session_id"] = new_sess["session"]["id"]

        result = await server._cmd_agent_list(client_id, client, [], {})

        assert result["status"] == "ok"
        assert "Planner" in result["agents"]

    @pytest.mark.asyncio
    async def test_process_agent_list_no_session(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_agent_list(client_id, client, [], {})

        assert result["status"] == "error"
        assert "加入" in result["message"]

    @pytest.mark.asyncio
    async def test_process_agent_exec(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        new_sess = await server._cmd_session_new(client_id, client, [], {})

        result = await server._cmd_agent_exec(client_id, client, ["Write tests"], {})

        assert result["status"] == "ok"
        assert "Executor" in result["executor"]["name"]
        assert result["executor"]["task"] == "Write tests"

    @pytest.mark.asyncio
    async def test_process_agent_exec_no_session(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_agent_exec(client_id, client, ["Write tests"], {})

        assert result["status"] == "error"
        assert "加入" in result["message"]

    @pytest.mark.asyncio
    async def test_process_agent_eval(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        new_sess = await server._cmd_session_new(client_id, client, [], {})

        result = await server._cmd_agent_eval(client_id, client, ["Check quality"], {})

        assert result["status"] == "ok"
        assert "Evaluator" in result["evaluator"]["name"]

    @pytest.mark.asyncio
    async def test_process_unknown_command(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}

        request = {"cmd": "unknown.cmd", "args": [], "kwargs": {}}
        result = await server._process_request(client_id, request)

        assert result["status"] == "error"
        assert "未知命令" in result["message"]

    @pytest.mark.asyncio
    async def test_process_planner_no_session(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_planner(client_id, client, ["test prompt"], {})

        assert result["status"] == "error"
        assert "加入" in result["message"]

    @pytest.mark.asyncio
    async def test_process_agent_exec(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        await server._cmd_session_new(client_id, client, [], {})

        result = await server._cmd_agent_exec(client_id, client, ["Write tests"], {})

        assert result["status"] == "ok"
        assert "Executor" in result["executor"]["name"]
        assert result["executor"]["task"] == "Write tests"

    @pytest.mark.asyncio
    async def test_process_agent_exec_no_session(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        result = await server._cmd_agent_exec(client_id, client, ["Write tests"], {})

        assert result["status"] == "error"
        assert "加入" in result["message"]

    @pytest.mark.asyncio
    async def test_process_agent_eval(self, server):
        client_id = "test-client"
        server.state.clients[client_id] = {"session_id": None, "ws": None}
        client = server.state.clients[client_id]

        await server._cmd_session_new(client_id, client, [], {})

        result = await server._cmd_agent_eval(client_id, client, ["Check quality"], {})

        assert result["status"] == "ok"
        assert "Evaluator" in result["evaluator"]["name"]

    @pytest.mark.asyncio
    async def test_process_unknown_command(self, server):
        client_id = "test-client"
        client = {"session_id": None, "ws": None}

        request = {"cmd": "unknown.cmd", "args": [], "kwargs": {}}
        result = await server._process_request(client_id, request)

        assert result["status"] == "error"
        assert "未知命令" in result["message"]

    @pytest.mark.asyncio
    async def test_process_planner_no_session(self, server):
        client_id = "test-client"
        client = {"session_id": None, "ws": None}

        result = await server._cmd_planner(client_id, client, ["test prompt"], {})

        assert result["status"] == "error"
        assert "加入" in result["message"]


class TestClient:
    def test_client_default_values(self):
        client = Client()
        assert client.host == "localhost"
        assert client.port == 8765
        assert client.url == "ws://localhost:8765/ws"

    def test_client_custom_values(self):
        client = Client(host="127.0.0.1", port=9999)
        assert client.host == "127.0.0.1"
        assert client.port == 9999
        assert client.url == "ws://127.0.0.1:9999/ws"

    def test_client_initial_state(self):
        client = Client()
        assert client.ws is None
        assert client.client_id is None
        assert client.current_session is None


class TestClientMethods:
    def test_session_new_method(self):
        client = Client()
        client.ws = None
        assert client.session_new.__doc__ is not None

    def test_session_list_method(self):
        client = Client()
        assert client.session_list.__doc__ is not None

    def test_session_join_method(self):
        client = Client()
        assert client.session_join.__doc__ is not None

    def test_agent_list_method(self):
        client = Client()
        assert client.agent_list.__doc__ is not None

    def test_agent_exec_method(self):
        client = Client()
        assert client.agent_exec.__doc__ is not None

    def test_status_method(self):
        client = Client()
        assert client.status.__doc__ is not None
