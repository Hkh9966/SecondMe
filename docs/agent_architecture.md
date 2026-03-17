# SecondMe Agent架构设计 (ADK + A2A + Vector Memory)

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Router    │  │   Router    │  │     Matching Engine     │ │
│  │   (Auth)    │  │  (Agent)    │  │  (Match + Escalate)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     A2A Communication Layer                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  A2AServer  │  A2AClient  │  MessageRouter  │  TaskQueue ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    Google ADK Agent Layer                        │
│  ┌──────────────────────┐    ┌──────────────────────┐         │
│  │   UserAgent          │◄──►│   PartnerAgent       │         │
│  │   (代表真实用户)      │ A2A│   (代表匹配用户)      │         │
│  │                      │    │                      │         │
│  │  ┌────────────────┐ │    │  ┌────────────────┐ │         │
│  │  │ LLM (Minimax)   │ │    │  │ LLM (Minimax)  │ │         │
│  │  └────────────────┘ │    │  └────────────────┘ │         │
│  │  ┌────────────────┐ │    │  ┌────────────────┐ │         │
│  │  │ Vector Memory  │ │    │  │ Vector Memory  │ │         │
│  │  │ (长期记忆)      │ │    │  │ (长期记忆)      │ │         │
│  │  └────────────────┘ │    │  └────────────────┘ │         │
│  └──────────────────────┘    └──────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Vector Database  │
                    │     (Qdrant)        │
                    └─────────────────────┘
```

## 核心组件设计

### 1. A2A Protocol (Agent-to-Agent)

```python
# A2A 消息协议
class A2AMessage:
    sender_id: str
    receiver_id: str
    content: str
    message_type: MessageType  # greeting, response, query, reaction
    conversation_id: str
    timestamp: datetime
    metadata: dict  # 情感分析、兴趣标签等
```

### 2. Agent Memory System

- **短期记忆**: 当前对话上下文 (LLM context)
- **长期记忆**: 向量数据库存储
  - 用户画像向量
  - 对话摘要
  - 兴趣偏好
  - 心动时刻

### 3. Google ADK Agent Structure

```python
class SecondMeAgent(Agent):
    # 核心能力
    - llm: 使用的LLM
    - memory: 向量记忆系统
    - user_profile: 用户画像

    # 工具 (Tools)
    - search_partner_info
    - update_memory
    - calculate_heart_score
    - express_feeling

    # 工作流
    - init_conversation()
    - generate_response()
    - evaluate_interest()
    - decide_escalate()
```

## 文件结构更新

```
app/
├── agents/
│   ├── __init__.py
│   ├── base.py              # 基础Agent类
│   ├── user_agent.py        # UserAgent实现
│   ├── partner_agent.py      # PartnerAgent实现
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── vector_store.py   # 向量存储接口
│   │   ├── qdrant_store.py  # Qdrant实现
│   │   └── memory_manager.py # 记忆管理
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py        # 搜索工具
│   │   ├── memory.py        # 记忆工具
│   │   └── scoring.py       # 心动值计算工具
│   └── a2a/
│       ├── __init__.py
│       ├── protocol.py      # A2A协议定义
│       ├── client.py       # A2A客户端
│       ├── server.py       # A2A服务器
│       └── message.py      # 消息处理
├── services/
│   ├── matching_service.py  # 匹配服务
│   └── conversation_service.py
```

## 实现步骤

1. 安装依赖 (google-adk, qdrant-client)
2. 创建向量数据库接口
3. 实现 A2A 协议
4. 实现 Agent 基类
5. 实现 Memory System
6. 实现 Tools
7. 集成 ADK
