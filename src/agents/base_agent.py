"""Agent 基类 — 定义所有 Agent 的通用接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(Enum):
    """Agent 状态枚举。"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Agent 执行结果。"""
    agent_name: str
    status: AgentStatus
    data: Any = None
    error: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BaseAgent(ABC):
    """Agent 基类。"""

    def __init__(self, name: str):
        self.name = name
        self.status = AgentStatus.IDLE

    @abstractmethod
    def execute(self, **kwargs) -> AgentResult:
        """执行 Agent 任务。

        Args:
            **kwargs: 任务参数

        Returns:
            AgentResult: 执行结果
        """
        pass

    def _success(self, data: Any = None) -> AgentResult:
        """返回成功结果。"""
        self.status = AgentStatus.SUCCESS
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            data=data,
        )

    def _failed(self, error: str) -> AgentResult:
        """返回失败结果。"""
        self.status = AgentStatus.FAILED
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            error=error,
        )
