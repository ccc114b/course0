#!/usr/bin/env python3
"""
agtw - Agent Team Work
A git-style multi-agent coordination system
"""

__version__ = "0.1.0"

from .agents import Agent, Guard, Planner, Executor, Evaluator
from .session import Session, SessionManager

__all__ = [
    "Agent",
    "Guard",
    "Planner",
    "Executor",
    "Evaluator",
    "Session",
    "SessionManager",
]
