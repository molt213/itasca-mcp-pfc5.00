# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
Task Lifecycle Management.

Task tracking, persistence, and status queries for long-running ITASCA scripts.

Python 3.6 compatible implementation.
"""

from .manager import TaskManager
from .task import ScriptTask

__all__ = [
    "TaskManager",
    "ScriptTask",
]
