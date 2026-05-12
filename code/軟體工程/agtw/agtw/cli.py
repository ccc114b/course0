#!/usr/bin/env python3
"""
CLI for agtw - Agent Team Work

Git-style commands:
  agtw server              - Start the agtw server
  agtw shell               - Enter interactive REPL mode
  agtw session new [name]  - Create a new session
  agtw session list        - List all sessions
  agtw session join <id>  - Join a session
  agtw session leave       - Leave current session
  agtw session delete <id> - Delete a session
  agtw agent list          - List agents in current session
  agtw agent exec <task>   - Create and run an executor
  agtw agent eval <desc>   - Create an evaluator
  agtw planner <prompt>    - Run planner with prompt
  agtw status              - Show server status
"""

import argparse
import sys

from .client import Client
from .server import Server


def cmd_server(host: str, port: int, model: str):
    """Start the server"""
    server = Server(host=host, port=port, model=model)
    server.start()


def cmd_shell(host: str, port: int):
    """Enter interactive REPL shell mode"""
    client = Client(host=host, port=port)
    client.shell()


def cmd_session_new(host: str, port: int, name: str = None):
    """Create a new session"""
    client = Client(host=host, port=port)
    result = client.session_new(name)
    if result["status"] == "ok":
        print(
            f"已建立 session: {result['session']['name']} (id={result['session']['id'][:8]})"
        )
        print(f"目前 session: {result['session']['id'][:8]}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_list(host: str, port: int):
    """List all sessions"""
    client = Client(host=host, port=port)
    result = client.session_list()
    if result["status"] == "ok":
        print("所有 Session:")
        print(f"{'ID':<12} {'Name':<20} {'Watching'}")
        print("-" * 45)
        for s in result["sessions"]:
            marker = " ← 目前" if s.get("is_current") else ""
            watching = ", ".join(s.get("watching", [])) or "-"
            print(f"{s['id']:<12} {s['name']:<20} {watching}{marker}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_join(host: str, port: int, session_id: str):
    """Join a session"""
    client = Client(host=host, port=port)
    result = client.session_join(session_id)
    if result["status"] == "ok":
        print(
            f"已加入 session: {result['session']['name']} (id={result['session']['id'][:8]})"
        )
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_leave(host: str, port: int):
    """Leave current session"""
    client = Client(host=host, port=port)
    result = client.session_leave()
    if result["status"] == "ok":
        print("已離開 session")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_session_delete(host: str, port: int, session_id: str):
    """Delete a session"""
    client = Client(host=host, port=port)
    result = client.session_delete(session_id)
    if result["status"] == "ok":
        print(f"已刪除 session: {session_id[:8]}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_list(host: str, port: int):
    """List agents"""
    client = Client(host=host, port=port)
    result = client.agent_list()
    if result["status"] == "ok":
        print(result["agents"])
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_exec(host: str, port: int, task: str):
    """Create and run executor"""
    client = Client(host=host, port=port)
    result = client.agent_exec(task)
    if result["status"] == "ok":
        print(f"已啟動 Executor: {result['executor']['name']}")
        print(f"任務：{result['executor']['task']}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_agent_eval(host: str, port: int, desc: str):
    """Create evaluator"""
    client = Client(host=host, port=port)
    result = client.agent_eval(desc)
    if result["status"] == "ok":
        print(f"已啟動 Evaluator: {result['evaluator']['name']}")
        print(f"描述：{result['evaluator']['desc']}")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_planner(host: str, port: int, prompt: str):
    """Run planner"""
    client = Client(host=host, port=port)
    result = client.planner(prompt)
    if result["status"] == "ok":
        print(result["response"])
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def cmd_status(host: str, port: int):
    """Show status"""
    client = Client(host=host, port=port)
    result = client.status()
    if result["status"] == "ok":
        print(f"模型：{result.get('model', 'N/A')}")
        print(f"客戶端 ID：{result.get('client_id', 'N/A')}")
        print(f"連線數：{result.get('connected_clients', 0)}")
        if result.get("current_session"):
            print(
                f"目前 Session：{result['current_session']['name']} (id={result['current_session']['id'][:8]})"
            )
        else:
            print("目前 Session：無（使用 agtw session join 加入）")
    else:
        print(f"錯誤：{result.get('message', '未知錯誤')}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="agtw - Agent Team Work",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  agtw server                      # 啟動伺服器
  agtw shell                       # 進入互動模式
  agtw session new myproject        # 建立新 session
  agtw session list                 # 列出所有 session
  agtw session join abc123          # 加入 session
  agtw session leave                # 離開 session
  agtw agent list                  # 列出目前 session 的 agents
  agtw agent exec 寫一個 hello.py  # 建立並執行 executor
  agtw planner 分析這個專案         # 執行 planner
  agtw status                      # 顯示狀態
        """,
    )

    parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Server port (default: 8765)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_server = subparsers.add_parser("server", help="Start the agtw server")
    p_server.add_argument("--host", help="Server host")
    p_server.add_argument("--port", type=int, help="Server port")
    p_server.add_argument("--model", default="minimax-m2.5:cloud", help="Ollama model")

    p_shell = subparsers.add_parser("shell", help="Enter interactive REPL mode")
    p_shell.add_argument("--host", help="Server host")
    p_shell.add_argument("--port", type=int, help="Server port")

    p_session = subparsers.add_parser("session", help="Session commands")
    sp = p_session.add_subparsers(dest="action", help="Session action")
    sp.add_parser("list", help="List sessions")
    sp.add_parser("leave", help="Leave current session")
    new_parser = sp.add_parser("new", help="Create new session")
    new_parser.add_argument("name", nargs="?", help="Session name")
    join_parser = sp.add_parser("join", help="Join session")
    join_parser.add_argument("id", help="Session ID")
    delete_parser = sp.add_parser("delete", help="Delete session")
    delete_parser.add_argument("id", help="Session ID")

    p_agent = subparsers.add_parser("agent", help="Agent commands")
    sp = p_agent.add_subparsers(dest="action", help="Agent action")
    sp.add_parser("list", help="List agents")
    exec_parser = sp.add_parser("exec", help="Execute task")
    exec_parser.add_argument("task", help="Task description")
    eval_parser = sp.add_parser("eval", help="Evaluate")
    eval_parser.add_argument("desc", help="Evaluation description")

    p_planner = subparsers.add_parser("planner", help="Run planner")
    p_planner.add_argument("prompt", help="Prompt for planner")

    subparsers.add_parser("status", help="Show server status")

    args = parser.parse_args()

    host = getattr(args, "host", None) or "localhost"
    port = getattr(args, "port", None) or 8765

    if args.command is None:
        parser.print_help()
    elif args.command == "server":
        cmd_server(host, port, getattr(args, "model", "minimax-m2.5:cloud"))
    elif args.command == "shell":
        cmd_shell(host, port)
    elif args.command == "session":
        if args.action == "new":
            cmd_session_new(host, port, getattr(args, "name", None))
        elif args.action == "list":
            cmd_session_list(host, port)
        elif args.action == "join":
            cmd_session_join(host, port, args.id)
        elif args.action == "leave":
            cmd_session_leave(host, port)
        elif args.action == "delete":
            cmd_session_delete(host, port, args.id)
    elif args.command == "agent":
        if args.action == "list":
            cmd_agent_list(host, port)
        elif args.action == "exec":
            cmd_agent_exec(host, port, args.task)
        elif args.action == "eval":
            cmd_agent_eval(host, port, args.desc)
    elif args.command == "planner":
        cmd_planner(host, port, args.prompt)
    elif args.command == "status":
        cmd_status(host, port)


if __name__ == "__main__":
    main()
