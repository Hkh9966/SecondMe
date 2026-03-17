from typing import Dict, Any, List
from app.models import Agent, Conversation, Message


class HeartScoreService:
    """Service for calculating heart scores between agents"""

    # Weight factors for heart score calculation
    PERSONALITY_WEIGHT = 0.40
    HOBBIES_WEIGHT = 0.30
    INDUSTRY_WEIGHT = 0.20
    INTERACTION_WEIGHT = 0.10

    def calculate_personality_match(
        self,
        agent1_personality: Dict[str, Any],
        agent2_personality: Dict[str, Any]
    ) -> float:
        """Calculate personality match score (0-100)"""
        if not agent1_personality or not agent2_personality:
            return 50.0  # Default score

        # Simple trait-based matching
        score = 0.0
        total_traits = 0

        for key in agent1_personality:
            if key in agent2_personality:
                total_traits += 1
                # Exact match gets full points, partial gets partial
                if agent1_personality[key] == agent2_personality[key]:
                    score += 100.0
                else:
                    # Calculate similarity for numeric traits
                    try:
                        val1 = float(agent1_personality[key])
                        val2 = float(agent2_personality[key])
                        diff = abs(val1 - val2)
                        similarity = max(0, 100 - diff)
                        score += similarity
                    except:
                        score += 50.0  # Partial match for non-numeric

        if total_traits == 0:
            return 50.0

        return score / total_traits

    def calculate_hobbies_match(
        self,
        agent1_hobbies: List[str],
        agent2_hobbies: List[str]
    ) -> float:
        """Calculate hobbies match score (0-100)"""
        if not agent1_hobbies or not agent2_hobbies:
            return 0.0

        set1 = set(agent1_hobbies)
        set2 = set(agent2_hobbies)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        # Jaccard similarity
        jaccard = intersection / union
        return jaccard * 100

    def calculate_industry_match(
        self,
        agent1_industry: str,
        agent2_industry: str
    ) -> float:
        """Calculate industry match score (0-100)"""
        if not agent1_industry or not agent2_industry:
            return 0.0

        if agent1_industry.lower() == agent2_industry.lower():
            return 100.0

        # Could add more sophisticated matching here
        return 0.0

    def calculate_interaction_score(
        self,
        messages: List[Message]
    ) -> float:
        """Calculate interaction quality score (0-100)"""
        if not messages:
            return 0.0

        # Simple metrics:
        # 1. Message count - more messages = more engagement
        # 2. Average message length - longer messages might indicate interest
        # 3. Response time patterns (would need timestamps)

        message_count = len(messages)
        total_length = sum(len(m.content) for m in messages)
        avg_length = total_length / message_count if message_count > 0 else 0

        # Score based on engagement
        # Cap at 10 messages for scoring
        engagement_score = min(message_count / 10, 1.0) * 50

        # Score based on message quality
        quality_score = min(avg_length / 50, 1.0) * 50

        return engagement_score + quality_score

    async def calculate_heart_score(
        self,
        agent1: Agent,
        agent2: Agent,
        conversation: Conversation,
        messages: List[Message]
    ) -> Dict[str, Any]:
        """Calculate heart score for agent1 towards agent2"""

        # Personality match
        personality_score = self.calculate_personality_match(
            agent1.personality or {},
            agent2.personality or {}
        )

        # Hobbies match
        hobbies_score = self.calculate_hobbies_match(
            agent1.hobbies or [],
            agent2.hobbies or []
        )

        # Industry match
        industry_score = self.calculate_industry_match(
            agent1.industry,
            agent2.industry
        )

        # Interaction score
        interaction_score = self.calculate_interaction_score(messages)

        # Calculate weighted total
        total_score = (
            personality_score * self.PERSONALITY_WEIGHT +
            hobbies_score * self.HOBBIES_WEIGHT +
            industry_score * self.INDUSTRY_WEIGHT +
            interaction_score * self.INTERACTION_WEIGHT
        )

        return {
            "total_score": round(total_score, 2),
            "personality_score": round(personality_score, 2),
            "hobbies_score": round(hobbies_score, 2),
            "industry_score": round(industry_score, 2),
            "interaction_score": round(interaction_score, 2),
            "weights": {
                "personality": self.PERSONALITY_WEIGHT,
                "hobbies": self.HOBBIES_WEIGHT,
                "industry": self.INDUSTRY_WEIGHT,
                "interaction": self.INTERACTION_WEIGHT
            }
        }
