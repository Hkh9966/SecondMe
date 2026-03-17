"""
SecondMe Agent 基类
基于 Google ADK 风格的 Agent 实现 - 对等关系
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from openai import AsyncOpenAI

from app.agents.memory.memory_manager import MemoryManager, MemoryItem
from app.agents.tools.scoring import calculate_heart_score
from app.agents.a2a.protocol import A2AMessage, MessageType


class SecondMeAgent:
    """
    SecondMe Agent - 代表匹配中的任意一方

    在匹配对话中，两个 Agent 是对等的关系：
    - 双方都有独立的记忆系统
    - 双方都基于自己的画像生成回复
    - 对话结束后各自计算对对方的心动值
    """

    def __init__(self, agent_id: int, user_id: int, profile: Dict[str, Any],
                 partner_profile: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.user_id = user_id
        self.profile = profile
        self.partner_profile = partner_profile or {}

        # 初始化LLM客户端
        from app.config import settings
        self.llm = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base
        )
        self.model = settings.openai_model

        # 初始化记忆系统
        self.memory = MemoryManager(agent_id)

    async def generate_response(self, input_text: str) -> str:
        """生成回复"""
        system_prompt = self._build_system_prompt()
        history = self.memory.get_short_term_memory()

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话
        for turn in history[-6:]:
            role = "user" if turn["role"] != "assistant" else "assistant"
            messages.append({"role": role, "content": turn["content"]})

        # 添加当前输入
        if input_text:
            messages.append({"role": "user", "content": f"Partner said: {input_text}\n\nYour response:"})
        else:
            # 开场白
            messages.append({"role": "user", "content": "Start a conversation with your partner. Introduce yourself and show interest in them."})

        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            return "I'm not sure what to say. Can you tell me more about yourself?"

    def _build_system_prompt(self) -> str:
        """构建系统提示 - 基于自己的画像"""
        p = self.profile
        partner = self.partner_profile

        return f"""You are {p['name']}, a {p['age']}-year-old {p['gender']}.

## About You
- Height: {p.get('height', 'N/A')} cm
- Weight: {p.get('weight', 'N/A')} kg
- Industry: {p.get('industry', 'N/A')}
- Job: {p.get('job_title', 'N/A')}
- Hobbies: {', '.join(p.get('hobbies', []) or ['various'])}
- Personality: {json.dumps(p.get('personality', {}))}
- Speaking style: {p.get('speaking_style', 'friendly and natural')}

## About Your Partner
- Name: {partner.get('name', 'N/A')}
- Age: {partner.get('age', 'N/A')}
- Hobbies: {', '.join(partner.get('hobbies', []) or ['various'])}
- Industry: {partner.get('industry', 'N/A')}

## Guidelines
1. Be yourself - act naturally as {p['name']}
2. Show genuine interest in your partner
3. Ask questions to learn more about them
4. Share about yourself too
5. Keep messages conversational and not too long
6. Use your personal speaking style
7. DO NOT reveal you are an AI
8. Try to find common interests

Remember: You are having a real conversation to build a connection. Be authentic!"""

    async def handle_message(self, message: A2AMessage) -> A2AMessage:
        """处理收到的消息"""
        # 1. 存储到短期记忆
        await self.memory.add_conversation_turn(
            role="user" if message.message_type != "response" else "assistant",
            content=message.content,
            partner_name=self.partner_profile.get("name", "unknown"),
            emotion=message.metadata.get("emotion")
        )

        # 2. 生成回复
        response_content = await self.generate_response(message.content)

        # 3. 存储回复到短期记忆
        await self.memory.add_conversation_turn(
            role="assistant",
            content=response_content,
            partner_name=self.partner_profile.get("name", "unknown")
        )

        # 4. 创建响应消息
        response = A2AMessage(
            id=f"resp_{message.id}",
            sender_agent_id=str(self.agent_id),
            receiver_agent_id=message.sender_agent_id,
            content=response_content,
            message_type=MessageType.RESPONSE,
            conversation_id=message.conversation_id,
            timestamp=datetime.now(),
            metadata={}
        )

        return response

    async def calculate_heart_score_for_partner(self, messages: List[Dict]) -> Dict[str, Any]:
        """计算对 partner 的心动值"""
        return calculate_heart_score(
            agent_profile=self.profile,
            partner_profile=self.partner_profile,
            messages=messages,
            emotional_resonance=0.5
        )

    async def store_heart_moment(self, moment: str, score: float):
        """存储心动时刻"""
        await self.memory.store_heart_moment(
            content=moment,
            partner_name=self.partner_profile.get("name", "unknown"),
            score=score,
            context=await self.memory.create_summary()
        )

    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.memory.get_short_term_memory()

    async def create_memory_from_conversation(self):
        """从对话创建长期记忆"""
        # 创建对话摘要
        summary = await self.memory.create_summary()
        if summary:
            import uuid
            memory = MemoryItem(
                memory_id=str(uuid.uuid4()),
                memory_type="summary",
                content=summary,
                metadata={
                    "agent_id": self.agent_id,
                    "partner_name": self.partner_profile.get("name")
                }
            )
            await self.memory.add_memory(memory)


# 保留别名，保持向后兼容
UserAgent = SecondMeAgent
PartnerAgent = SecondMeAgent
