"""
Agent Tools - 心动值计算工具
"""
from typing import Dict, Any
from pydantic import BaseModel


class HeartScoreInput(BaseModel):
    """心动值计算输入"""
    partner_personality: Dict[str, Any]
    partner_hobbies: list
    partner_industry: str
    conversation_quality: float
    emotional_resonance: float


def calculate_personality_match(personality1: Dict, personality2: Dict) -> float:
    """计算性格匹配度"""
    if not personality1 or not personality2:
        return 50.0

    score = 0.0
    total = 0

    for key in personality1:
        if key in personality2:
            total += 1
            # 数值型性格特质计算差异
            try:
                val1 = float(personality1[key])
                val2 = float(personality2[key])
                diff = abs(val1 - val2)
                # 归一化到0-100
                similarity = max(0, 100 - diff)
                score += similarity
            except:
                # 文字型特质完全匹配得100分
                if personality1[key] == personality2[key]:
                    score += 100
                else:
                    score += 50

    return score / total if total > 0 else 50.0


def calculate_hobbies_match(hobbies1: list, hobbies2: list) -> float:
    """计算兴趣爱好匹配度 (Jaccard相似度)"""
    if not hobbies1 or not hobbies2:
        return 0.0

    set1 = set(hobbies1)
    set2 = set(hobbies2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return (intersection / union * 100) if union > 0 else 0.0


def calculate_industry_match(industry1: str, industry2: str) -> float:
    """计算行业匹配度"""
    if not industry1 or not industry2:
        return 0.0

    if industry1.lower() == industry2.lower():
        return 100.0

    # 可以添加行业相关性判断
    related_industries = {
        "tech": ["software", "internet", "ai", "data"],
        "finance": ["banking", "investment", "fintech"],
        "creative": ["design", "art", "media", "marketing"]
    }

    for category, keywords in related_industries.items():
        if any(k in industry1.lower() for k in keywords):
            if any(k in industry2.lower() for k in keywords):
                return 80.0

    return 20.0


def calculate_conversation_quality(messages: list) -> float:
    """计算对话质量"""
    if not messages:
        return 0.0

    # 指标1: 消息数量 (更多 = 更投入)
    message_count = len(messages)
    count_score = min(message_count / 10 * 50, 50)

    # 指标2: 平均消息长度 (适当长度 = 更真诚)
    total_length = sum(len(m.get("content", "")) for m in messages)
    avg_length = total_length / message_count if message_count > 0 else 0
    length_score = min(avg_length / 50 * 30, 30)

    # 指标3: 互动深度 (问题数量)
    question_count = sum(1 for m in messages if "?" in m.get("content", ""))
    question_score = min(question_count / 5 * 20, 20)

    return count_score + length_score + question_score


def calculate_heart_score(agent_profile: Dict, partner_profile: Dict,
                          messages: list, emotional_resonance: float = 0.5) -> Dict[str, Any]:
    """
    计算心动值

    权重:
    - 性格匹配度: 40%
    - 兴趣爱好: 30%
    - 行业相关性: 20%
    - 对话质量: 10%
    """

    # 1. 性格匹配度
    personality_score = calculate_personality_match(
        agent_profile.get("personality", {}),
        partner_profile.get("personality", {})
    )

    # 2. 兴趣爱好匹配度
    hobbies_score = calculate_hobbies_match(
        agent_profile.get("hobbies", []),
        partner_profile.get("hobbies", [])
    )

    # 3. 行业匹配度
    industry_score = calculate_industry_match(
        agent_profile.get("industry", ""),
        partner_profile.get("industry", "")
    )

    # 4. 对话质量
    conversation_score = calculate_conversation_quality(messages)

    # 5. 情感共鸣 (额外加成)
    emotional_boost = emotional_resonance * 10  # 最多+10分

    # 加权计算总分
    total_score = (
        personality_score * 0.40 +
        hobbies_score * 0.30 +
        industry_score * 0.20 +
        conversation_score * 0.10 +
        emotional_boost
    )

    return {
        "total_score": round(total_score, 2),
        "breakdown": {
            "personality_score": round(personality_score, 2),
            "hobbies_score": round(hobbies_score, 2),
            "industry_score": round(industry_score, 2),
            "conversation_score": round(conversation_score, 2),
            "emotional_boost": round(emotional_boost, 2)
        },
        "weights": {
            "personality": 0.40,
            "hobbies": 0.30,
            "industry": 0.20,
            "conversation": 0.10
        },
        "interpretation": _interpret_score(total_score)
    }


def _interpret_score(score: float) -> str:
    """解读心动值"""
    if score >= 80:
        return "非常心动！强烈建议进一步交流"
    elif score >= 60:
        return "有好感，可以深入了解"
    elif score >= 40:
        return "一般般，需要更多了解"
    else:
        return "不太适合做情侣"
