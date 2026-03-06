"""기본 에이전트 클래스"""

from abc import ABC, abstractmethod
from datetime import datetime
from zoneinfo import ZoneInfo

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
        self._base_system_prompt = profile["system_prompt"]

    @staticmethod
    def get_today_kst() -> str:
        """현재 날짜를 KST 기준으로 반환"""
        kst = ZoneInfo("Asia/Seoul")
        return datetime.now(kst).strftime("%Y년 %m월 %d일")

    @property
    def system_prompt(self) -> str:
        """동적으로 오늘 날짜가 포함된 시스템 프롬프트 반환"""
        today = self.get_today_kst()
        date_prefix = f"[필수] 오늘 날짜: {today} (KST 기준)\n모든 응답에서 이 날짜를 사용해. 다른 날짜 사용 금지!\n\n"
        return date_prefix + self._base_system_prompt

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
