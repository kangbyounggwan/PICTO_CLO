"""기본 에이전트 클래스"""

from abc import ABC, abstractmethod
from config.agents import AGENT_PROFILES
from services.gemini_service import gemini_service


class BaseAgent(ABC):
    """모든 AI 에이전트의 기본 클래스"""

    agent_type: str = "general"

    def __init__(self):
        profile = AGENT_PROFILES.get(self.agent_type, AGENT_PROFILES["general"])
        self.name = profile["name"]
        self.emoji = profile["emoji"]
        self.triggers = profile["triggers"]
        self.system_prompt = profile["system_prompt"]

    async def respond(
        self,
        message: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """메시지에 대한 응답 생성"""
        response = await gemini_service.chat(
            message=message,
            system_prompt=self.system_prompt,
            conversation_history=conversation_history,
        )
        return f"{self.emoji} **{self.name}**\n\n{response}"

    def matches_trigger(self, message: str) -> bool:
        """메시지가 이 에이전트의 트리거와 일치하는지 확인"""
        message_lower = message.lower()
        return any(trigger.lower() in message_lower for trigger in self.triggers)

    @abstractmethod
    async def process(self, message: str, **kwargs) -> str:
        """에이전트별 특화 처리 (하위 클래스에서 구현)"""
        pass
