#!/usr/bin/env python3
"""
Tests for session classes
"""

import pytest
from agtw.session import Session, SessionManager
from agtw.agents import Guard


class TestSession:
    def test_session_creation(self):
        guard = Guard()
        session = Session("test_session", guard, "test-model")

        assert session.name == "test_session"
        assert session.model == "test-model"
        assert session.guard is guard
        assert session.planner is not None
        assert session.planner.name == "Planner[test_session]"
        assert len(session.executors) == 0
        assert len(session.evaluators) == 0

    def test_session_id_is_unique(self):
        guard = Guard()
        session1 = Session("s1", guard, "model")
        session2 = Session("s2", guard, "model")
        assert session1.id != session2.id
        assert len(session1.id) == 8
        assert len(session2.id) == 8

    def test_create_executor(self):
        guard = Guard()
        session = Session("test", guard, "model")
        executor = session.create_executor("Write code")

        assert executor is not None
        assert len(session.executors) == 1
        assert executor.assigned_task == "Write code"
        assert "Executor" in executor.name

    def test_create_multiple_executors(self):
        guard = Guard()
        session = Session("test", guard, "model")

        session.create_executor("Task 1")
        session.create_executor("Task 2")
        session.create_executor("Task 3")

        assert len(session.executors) == 3
        assert session.executors[0].assigned_task == "Task 1"
        assert session.executors[1].assigned_task == "Task 2"
        assert session.executors[2].assigned_task == "Task 3"

    def test_create_evaluator(self):
        guard = Guard()
        session = Session("test", guard, "model")
        evaluator = session.create_evaluator()

        assert evaluator is not None
        assert len(session.evaluators) == 1
        assert "Evaluator" in evaluator.name

    def test_create_evaluator_following_executors(self):
        guard = Guard()
        session = Session("test", guard, "model")
        executor = session.create_executor("Task")
        evaluator = session.create_evaluator(executor)

        assert executor in evaluator.target_executors

    def test_get_executors(self):
        guard = Guard()
        session = Session("test", guard, "model")
        e1 = session.create_executor("Task 1")
        e2 = session.create_executor("Task 2")

        all_execs = session.get_executors()
        assert len(all_execs) == 2

        filtered = session.get_executors(lambda e: "Task 1" in e.assigned_task)
        assert len(filtered) == 1
        assert filtered[0] is e1

    def test_get_executor_by_name(self):
        guard = Guard()
        session = Session("test", guard, "model")
        session.create_executor("Task 1")
        session.create_executor("Task 2")

        found = session.get_executor("Executor[test-1]")
        assert found is not None
        assert found.assigned_task == "Task 1"

    def test_get_evaluator_by_name(self):
        guard = Guard()
        session = Session("test", guard, "model")
        session.create_evaluator()

        found = session.get_evaluator("Evaluator")
        assert found is not None

    def test_list_agents(self):
        guard = Guard()
        session = Session("test", guard, "model")
        session.create_executor("Task 1")
        session.create_evaluator()

        listing = session.list_agents()
        assert "Session: test" in listing
        assert "Planner" in listing
        assert "Executor" in listing
        assert "Evaluator" in listing

    def test_shutdown(self):
        guard = Guard()
        session = Session("test", guard, "model")
        session.create_executor("Task")
        session.create_evaluator()

        session.planner.start()
        for e in session.executors:
            e.start()
        for ev in session.evaluators:
            ev.start()

        session.shutdown()
        assert session.planner.thread is None or not session.planner.thread.is_alive()

    def test_to_dict(self):
        guard = Guard()
        session = Session("test", guard, "model")
        session.memory = "Important info"
        executor = session.create_executor("Task")
        evaluator = session.create_evaluator(executor)

        data = session.to_dict()
        assert data["name"] == "test"
        assert data["memory"] == "Important info"
        assert len(data["executors"]) == 1
        assert len(data["evaluators"]) == 1
        assert data["planner"]["name"] == "Planner[test]"

    def test_from_dict(self):
        guard = Guard()
        data = {
            "id": "abc12345",
            "name": "restored_session",
            "model": "test-model",
            "memory": "Restored memory",
            "planner": {
                "name": "Planner[restored]",
                "memory": "Planner memory",
                "messages": ["msg1"],
            },
            "executors": [
                {"name": "Exec1", "memory": "", "messages": []},
            ],
            "evaluators": [
                {"name": "Eval1", "memory": "", "messages": []},
            ],
        }

        session = Session.from_dict(data, guard)
        assert session.id == "abc12345"
        assert session.name == "restored_session"
        assert session.memory == "Restored memory"
        assert len(session.executors) == 1
        assert len(session.evaluators) == 1


class TestSessionManager:
    def test_manager_creation(self):
        manager = SessionManager("test-model")
        assert manager.model == "test-model"
        assert len(manager.sessions) == 0
        assert manager.current_session is None
        assert manager.guard is not None

    def test_create_session(self):
        manager = SessionManager("model")
        session = manager.create_session()

        assert session is not None
        assert len(manager.sessions) == 2
        assert manager.current_session is session
        assert session.name == "session1"

    def test_create_named_session(self):
        manager = SessionManager("model")
        session = manager.create_session("myproject")

        assert session.name == "myproject"
        assert "myproject" in manager.sessions

    def test_create_duplicate_named_session(self):
        manager = SessionManager("model")
        s1 = manager.create_session("test")
        s2 = manager.create_session("test")

        assert s1.name == "test"
        assert s2.name.startswith("test_")
        assert s1 is not s2

    def test_switch_session(self):
        manager = SessionManager("model")
        s1 = manager.create_session("s1")
        s2 = manager.create_session("s2")

        result = manager.switch_session(s1.id)
        assert result is s1
        assert manager.current_session is s1

    def test_switch_session_by_name(self):
        manager = SessionManager("model")
        manager.create_session("first")
        second = manager.create_session("second")

        manager.switch_session("first")
        assert manager.current_session.name == "first"

        manager.switch_session("second")
        assert manager.current_session is second

    def test_delete_session(self):
        manager = SessionManager("model")
        session = manager.create_session("to_delete")
        session_id = session.id

        result = manager.delete_session(session_id)
        assert result is True
        assert session_id not in manager.sessions

    def test_delete_nonexistent_session(self):
        manager = SessionManager("model")
        result = manager.delete_session("nonexistent")
        assert result is False

    def test_delete_current_session(self):
        manager = SessionManager("model")
        manager.create_session("s1")
        s2 = manager.create_session("s2")

        manager.delete_session(s2.id)
        assert manager.current_session is None

    def test_list_sessions_empty(self):
        manager = SessionManager("model")
        listing = manager.list_sessions()
        assert "沒有任何 session" in listing

    def test_list_sessions(self):
        manager = SessionManager("model")
        s1 = manager.create_session("project1")
        manager.create_session("project2")

        listing = manager.list_sessions()
        assert "project1" in listing
        assert "project2" in listing
        assert "目前" in listing

    def test_get_current(self):
        manager = SessionManager("model")
        assert manager.get_current() is None

        session = manager.create_session()
        assert manager.get_current() is session

    def test_shutdown_all(self):
        manager = SessionManager("model")
        manager.create_session("s1")
        manager.create_session("s2")

        manager.shutdown_all()
        assert len(manager.sessions) == 0
        assert manager.current_session is None

    def test_to_dict(self):
        manager = SessionManager("model")
        session = manager.create_session("test")

        data = manager.to_dict()
        assert data["model"] == "model"
        assert "test" in data["sessions"]
        assert data["current_session_id"] == session.id

    def test_from_dict(self):
        data = {
            "model": "test-model",
            "sessions": {
                "test": {
                    "id": "abc123",
                    "name": "restored",
                    "model": "test-model",
                    "memory": "",
                    "planner": {"name": "Planner", "memory": "", "messages": []},
                    "executors": [],
                    "evaluators": [],
                }
            },
            "current_session_id": "abc123",
        }

        manager = SessionManager.from_dict(data)
        assert manager.model == "test-model"
        assert "test" in manager.sessions
        assert manager.current_session is not None
        assert manager.current_session.id == "abc123"
