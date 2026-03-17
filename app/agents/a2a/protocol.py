"""
A2A (Agent-to-Agent) Protocol Implementation
用于Agent之间的通信协议
"""
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class MessageType(str, Enum):
    GREETING = "greeting"        # 开场白
    RESPONSE = "response"        # 回复
    QUERY = "query"             # 询问
    REACTION = "reaction"        # 反应/情感表达
    ESCALATE = "escalate"       # 升级请求
    END = "end"                 # 结束对话


class A2AMessage(BaseModel):
    """A2A 消息格式"""
    id: str
    sender_agent_id: str
    receiver_agent_id: str
    content: str
    message_type: MessageType
    conversation_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}  # 情感分析、兴趣标签等

    class Config:
        use_enum_values = True


class A2ATask(BaseModel):
    """A2A 任务"""
    task_id: str
    conversation_id: str
    initiator_agent_id: str
    receiver_agent_id: str
    status: str = "pending"  # pending, running, completed, failed
    messages: List[A2AMessage] = []
    heart_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class A2AClient:
    """A2A 客户端 - 用于发送消息给其他Agent"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def send_message(self, receiver_agent_id: str, content: str,
                          message_type: MessageType, conversation_id: str,
                          metadata: Dict[str, Any] = None) -> A2AMessage:
        """发送消息给另一个Agent"""
        import uuid
        message = A2AMessage(
            id=str(uuid.uuid4()),
            sender_agent_id=self.agent_id,
            receiver_agent_id=receiver_agent_id,
            content=content,
            message_type=message_type,
            conversation_id=conversation_id,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        return message

    async def receive_message(self, message: A2AMessage) -> str:
        """接收并处理消息"""
        # 这里会调用Agent的处理逻辑
        return message.content


class A2AServer:
    """A2A 服务器 - 路由消息"""

    def __init__(self):
        self.agent_registry: Dict[str, Any] = {}

    def register_agent(self, agent_id: str, agent_instance: Any):
        """注册Agent"""
        self.agent_registry[agent_id] = agent_instance

    async def route_message(self, message: A2AMessage) -> A2AMessage:
        """路由消息到目标Agent"""
        receiver_id = message.receiver_agent_id
        agent = self.agent_registry.get(receiver_id)

        if not agent:
            raise ValueError(f"Agent {receiver_id} not found")

        # 调用Agent处理消息
        response = await agent.handle_message(message)
        return response


# 全局A2A服务器实例
a2a_server = A2AServer()
