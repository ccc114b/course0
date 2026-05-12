#!/usr/bin/env python3
"""
Tests for agent classes
"""

import pytest
from agtw.agents import Agent, Guard, Planner, Executor, Evaluator, check_outside_access


class TestCheckOutsideAccess:
    def test_absolute_path_outside_cwd(self):
        is_outside, path = check_outside_access("cat /etc/passwd", "/home/user/project")
        assert is_outside is True
        assert "/etc/passwd" in path

    def test_relative_path_outside_cwd(self):
        is_outside, path = check_outside_access(
            "cat ../secret.txt", "/home/user/project"
        )
        assert is_outside is True

    def test_path_inside_cwd(self):
        is_outside, path = check_outside_access("cat file.txt", "/home/user/project")
        assert is_outside is False

    def test_path_with_subdirectory(self):
        is_outside, path = check_outside_access("ls src/utils", "/home/user/project")
        assert is_outside is False

    def test_multiple_commands(self):
        cmd = "cat /etc/hosts && ls ../outside"
        is_outside, _ = check_outside_access(cmd, "/home/user/project")
        assert is_outside is True


class TestAgent:
    def test_agent_creation(self):
        agent = Agent("TestAgent", "You are a test agent.")
        assert agent.name == "TestAgent"
        assert agent.system == "You are a test agent."
        assert agent.memory == ""
        assert agent.messages == []

    def test_read_write(self):
        agent = Agent("TestAgent")
        agent.read("Hello")
        agent.write("World")
        assert len(agent.messages) == 2
        assert agent.messages[0] == "Hello"
        assert agent.messages[1] == "World"

    def test_get_context_empty(self):
        agent = Agent("TestAgent")
        context = agent.get_context()
        assert context == ""

    def test_get_context_with_memory(self):
        agent = Agent("TestAgent")
        agent.memory = "Important: Use UTF-8"
        context = agent.get_context()
        assert "<memory>" in context
        assert "Important: Use UTF-8" in context

    def test_get_context_with_messages(self):
        agent = Agent("TestAgent")
        agent.read("User message")
        agent.write("Assistant response")
        context = agent.get_context()
        assert "<history>" in context
        assert "User message" in context
        assert "Assistant response" in context

    def test_record(self):
        agent = Agent("TestAgent")
        agent.record("Hello", "Hi there!")
        assert len(agent.messages) == 2
        assert "Hello" in agent.messages[0]
        assert "Hi there!" in agent.messages[1]

    def test_record_max_turns(self):
        agent = Agent("TestAgent")
        agent.max_turns = 2
        for i in range(10):
            agent.record(f"user{i}", f"assistant{i}")
        assert len(agent.messages) <= agent.max_turns * 4

    def test_to_dict(self):
        agent = Agent("TestAgent")
        agent.memory = "Test memory"
        agent.read("Test message")
        data = agent.to_dict()
        assert data["name"] == "TestAgent"
        assert data["memory"] == "Test memory"
        assert "Test message" in data["messages"]

    def test_from_dict(self):
        data = {
            "name": "TestAgent",
            "memory": "Restored memory",
            "messages": ["msg1", "msg2"],
        }
        agent = Agent.from_dict(data, name="DifferentName")
        assert agent.name == "DifferentName"
        assert agent.memory == "Restored memory"
        assert len(agent.messages) == 2


class TestGuard:
    def test_guard_creation(self):
        guard = Guard()
        assert isinstance(guard.allowed_paths, set)
        assert len(guard.allowed_paths) == 0

    def test_to_dict(self):
        guard = Guard()
        guard.allowed_paths.add("/tmp/test")
        data = guard.to_dict()
        assert "/tmp/test" in data["allowed_paths"]

    def test_from_dict(self):
        data = {"allowed_paths": ["/tmp/test1", "/tmp/test2"]}
        guard = Guard.from_dict(data)
        assert "/tmp/test1" in guard.allowed_paths
        assert "/tmp/test2" in guard.allowed_paths


class TestPlanner:
    def test_planner_creation(self):
        guard = Guard()
        planner = Planner(guard, "TestPlanner")
        assert planner.name == "TestPlanner"
        assert planner.guard is guard
        assert "Planner" in planner.system

    def test_planner_request_exec(self):
        guard = Guard()
        planner = Planner(guard)
        result = planner.request_exec("Write a function")
        assert result["action"] == "exec"
        assert result["task"] == "Write a function"

    def test_planner_request_eval(self):
        guard = Guard()
        planner = Planner(guard)
        result = planner.request_eval("Check the output")
        assert result["action"] == "eval"
        assert result["desc"] == "Check the output"


class TestExecutor:
    def test_executor_creation(self):
        guard = Guard()
        executor = Executor(guard, "TestExecutor")
        assert executor.name == "TestExecutor"
        assert executor.guard is guard
        assert executor.assigned_task == ""

    def test_executor_with_task(self):
        guard = Guard()
        executor = Executor(guard)
        executor.assigned_task = "Build the project"
        assert executor.assigned_task == "Build the project"


class TestEvaluator:
    def test_evaluator_creation(self):
        guard = Guard()
        evaluator = Evaluator(guard, "TestEvaluator")
        assert evaluator.name == "TestEvaluator"
        assert evaluator.guard is guard
        assert evaluator.target_executors == []

    def test_evaluator_follow(self):
        guard = Guard()
        evaluator = Evaluator(guard)
        executor1 = Executor(guard)
        executor2 = Executor(guard)

        evaluator.follow(executor1)
        assert len(evaluator.target_executors) == 1
        assert executor1 in evaluator.target_executors

        evaluator.follow(executor2)
        assert len(evaluator.target_executors) == 2

    def test_evaluator_follow_no_duplicates(self):
        guard = Guard()
        evaluator = Evaluator(guard)
        executor = Executor(guard)

        evaluator.follow(executor)
        evaluator.follow(executor)
        assert len(evaluator.target_executors) == 1
