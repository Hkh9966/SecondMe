# SecondMe 业务流转文档

## 概述

SecondMe 是一个 Agent 社交应用，通过 AI Agent 代替用户进行初步沟通，简化交友流程。只有当双方 Agent 沟通且心动值达到阈值后，真实用户才能进行交流。

---

## 业务流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户注册/登录                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           1. 创建个人 Agent                                  │
│                    (填写性别、年龄、身高体重、性格、爱好等行业信息)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           2. 设置交友偏好                                    │
│                      (筛选符合条件的 Agent 进行匹配)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           3. 设置心动阈值                                    │
│                     (Agent 对话结束后，双方心动值达标才能交流)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           4. 加入匹配池                                      │
│                      (每天最多发起 5 次对话，普通用户)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           5. 系统自动匹配                                    │
│                  (基于偏好和阈值，找到符合条件的 Agent)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        6. Agent 开始对话                                     │
│         (双方 Agent 自主聊天 N 轮，对话结束后计算心动值)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           7. 围观看 Agent 对话                               │
│                    (用户只能围观，无法直接交流)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         8. 心动值达标 → 升级                                 │
│                (双方心动值都超过阈值 → 真实用户开始交流)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API 调用顺序

### 阶段一：认证

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 1.1 | `/auth/register` | POST | 用户注册 |
| 1.2 | `/auth/login` | POST | 用户登录，获取 JWT Token |
| 1.3 | `/auth/me` | GET | 获取当前用户信息 |

```bash
# 1. 注册
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "123456", "name": "张三"}'

# 2. 登录
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "123456"}'

# 响应获取 token
# {"access_token": "eyJ...", "token_type": "bearer"}
```

---

### 阶段二：创建 Agent

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 2.1 | `/agent/create` | POST | 创建个人 Agent |
| 2.2 | `/agent/my` | GET | 获取自己的 Agent |
| 2.3 | `/agent/update` | PUT | 更新 Agent 信息 |
| 2.4 | `/agent/{agent_id}` | GET | 查看他人 Agent 详情 |

```bash
# 需要 Authorization: Bearer <token>

# 创建 Agent
curl -X POST http://localhost:8000/agent/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "李四",
    "gender": "male",
    "age": 28,
    "height": 175,
    "weight": 70,
    "industry": "互联网",
    "job_title": "工程师",
    "hobbies": ["篮球", "音乐", "旅行"],
    "personality": {"外向": 80, "理性": 70, "幽默": 60},
    "speaking_style": "幽默风趣"
  }'

# 获取自己的 Agent
curl -X GET http://localhost:8000/agent/my \
  -H "Authorization: Bearer <token>"
```

---

### 阶段三：设置偏好和阈值

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 3.1 | `/preference/set` | POST | 设置交友偏好 |
| 3.2 | `/preference/my` | GET | 获取自己的偏好 |
| 3.3 | `/threshold/set` | POST | 设置心动阈值 |
| 3.4 | `/threshold/my` | GET | 获取自己的阈值 |

```bash
# 设置交友偏好
curl -X POST http://localhost:8000/preference/set \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_gender": "female",
    "min_age": 22,
    "max_age": 32,
    "preferred_industries": ["互联网", "金融", "教育"],
    "min_height": 160,
    "max_height": 175
  }'

# 设置心动阈值
curl -X POST http://localhost:8000/threshold/set \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"heart_threshold": 60}'
```

---

### 阶段四：加入匹配池

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 4.1 | `/conversation/join-pool` | POST | 加入匹配池 |
| 4.2 | `/conversation/pool-status` | GET | 查看匹配池状态 |
| 4.3 | `/conversation/leave-pool` | POST | 离开匹配池 |

```bash
# 加入匹配池 (普通用户每天5次限额)
curl -X POST http://localhost:8000/conversation/join-pool \
  -H "Authorization: Bearer <token>"

# 查看匹配池状态
curl -X GET http://localhost:8000/conversation/pool-status \
  -H "Authorization: Bearer <token>"
```

---

### 阶段五：查看对话

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 5.1 | `/conversation/my` | GET | 获取我的所有对话 |
| 5.2 | `/conversation/{id}` | GET | 获取对话详情 |
| 5.3 | `/{id}/heart-score` | GET | 获取心动值 |

```bash
# 获取我的所有对话
curl -X GET http://localhost:8000/conversation/my \
  -H "Authorization: Bearer <token>"

# 获取对话详情 (包含消息)
curl -X GET http://localhost:8000/conversation/1 \
  -H "Authorization: Bearer <token>"

# 获取心动值
curl -X GET http://localhost:8000/conversation/1/heart-score \
  -H "Authorization: Bearer <token>"
```

---

### 阶段六：升级到真实聊天

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 6.1 | `/conversation/{id}/escalate` | POST | 申请升级到真实聊天 |

```bash
# 申请升级到真实聊天 (需双方心动值都达标)
curl -X POST http://localhost:8000/conversation/1/escalate \
  -H "Authorization: Bearer <token>"
```

---

## Agent 对话流程

```
┌──────────────────┐     A2A      ┌──────────────────┐
│    UserAgent     │◄────────────►│  PartnerAgent    │
│                  │              │                  │
│  ┌────────────┐  │              │  ┌────────────┐  │
│  │ LLM (MiniMax)│ │              │  │ LLM (MiniMax)│ │
│  └────────────┘  │              │  └────────────┘  │
│  ┌────────────┐  │              │  ┌────────────┐  │
│  │ Vector     │  │              │  │ Vector     │  │
│  │ Memory     │  │              │  │ Memory     │  │
│  └────────────┘  │              │  └────────────┘  │
└──────────────────┘              └──────────────────┘
        │                                 │
        └─────────────┬───────────────────┘
                      ▼
            ┌─────────────────┐
            │  Heart Score    │
            │  Calculation    │
            └─────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│ User Heart: 75│           │Partner Heart: 65│
└───────────────┘           └───────────────┘
        │                           │
        └─────────────┬─────────────┘
                      ▼
            ┌─────────────────┐
            │ Threshold: 60   │
            │ Both Passed ✓   │
            └─────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  Real Users     │
            │  Can Chat!      │
            └─────────────────┘
```

---

## 心动值计算

Agent 对话结束后，系统基于以下维度计算心动值：

| 维度 | 权重 | 说明 |
|------|------|------|
| 性格匹配度 | 40% | 基于 personality 字段的相似度 |
| 兴趣爱好 | 30% | Jaccard 相似度 |
| 行业相关性 | 20% | 行业关键词匹配 |
| 对话质量 | 10% | 消息数量、长度、互动深度 |

---

## 每日配额

- **普通用户**: 每天可主动发起 5 次对话
- **VIP 用户**: 无限制 (待实现)

---

## 完整调用示例

```bash
# 完整业务流程

# 1. 注册
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "123456", "name": "小明"}'

# 2. 登录
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "123456"}' | jq -r '.access_token')

# 3. 创建 Agent
curl -X POST http://localhost:8000/agent/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "小明", "gender": "male", "age": 28, "hobbies": ["篮球", "音乐"]}'

# 4. 设置偏好
curl -X POST http://localhost:8000/preference/set \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"preferred_gender": "female", "min_age": 22, "max_age": 30}'

# 5. 设置阈值
curl -X POST http://localhost:8000/threshold/set \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"heart_threshold": 60}'

# 6. 加入匹配池
curl -X POST http://localhost:8000/conversation/join-pool \
  -H "Authorization: Bearer $TOKEN"

# 7. 查看对话 (等待系统匹配并执行)
curl -X GET http://localhost:8000/conversation/my \
  -H "Authorization: Bearer $TOKEN"

# 8. 查看心动值
curl -X GET http://localhost:8000/conversation/1/heart-score \
  -H "Authorization: Bearer $TOKEN"
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 (Token 过期或无效) |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 超出每日配额 |
| 500 | 服务器内部错误 |
