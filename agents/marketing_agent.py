"""마케팅 AI 에이전트"""

from .base_agent import BaseAgent


class MarketingAgent(BaseAgent):
    """마케팅 전략 및 콘텐츠 생성 에이전트"""

    agent_type = "marketing"

    async def process(self, message: str, **kwargs) -> str:
        """마케팅 관련 메시지 처리"""
        # 트리거 키워드 제거
        clean_message = message
        for trigger in self.triggers:
            clean_message = clean_message.replace(trigger, "").strip()

        if not clean_message:
            clean_message = "마케팅 관련 도움이 필요하신가요? 어떤 내용을 도와드릴까요?"

        return await self.respond(clean_message, kwargs.get("history"))

    async def generate_content(self, topic: str, content_type: str = "SNS") -> str:
        """마케팅 콘텐츠 생성"""
        prompt = f"""
다음 주제로 {content_type} 콘텐츠를 작성해주세요:
주제: {topic}

요구사항:
- 매력적인 헤드라인
- 핵심 메시지
- 해시태그 제안 (SNS인 경우)
- CTA(Call to Action)
"""
        return await self.respond(prompt)

    async def analyze_campaign(self, campaign_info: str) -> str:
        """마케팅 캠페인 분석"""
        prompt = f"""
다음 마케팅 캠페인을 분석해주세요:
{campaign_info}

분석 항목:
- 타겟 적합성
- 메시지 효과성
- 개선 제안
- 예상 성과
"""
        return await self.respond(prompt)
