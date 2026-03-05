"""크롤링 AI 에이전트"""

from .base_agent import BaseAgent
from services.crawler_service import crawler_service


class CrawlerAgent(BaseAgent):
    """뉴스 및 정보 수집 에이전트"""

    agent_type = "crawler"

    async def process(self, message: str, **kwargs) -> str:
        """크롤링 관련 메시지 처리"""
        clean_message = message
        for trigger in self.triggers:
            clean_message = clean_message.replace(trigger, "").strip()

        # 뉴스 검색 키워드 추출
        if clean_message:
            # 뉴스 검색 수행
            news_data = await crawler_service.search_news(clean_message)

            # Claude로 분석 및 요약
            analysis_prompt = f"""
다음 뉴스 정보를 분석하고 인사이트를 제공해주세요:

{news_data}

요청 주제: {clean_message}

분석 항목:
- 핵심 트렌드 요약
- 비즈니스 시사점
- 주목할 포인트
- 추가 조사 필요 영역
"""
            return await self.respond(analysis_prompt, kwargs.get("history"))
        else:
            return await self.respond(
                "어떤 주제의 뉴스나 정보를 찾아드릴까요?",
                kwargs.get("history")
            )

    async def fetch_and_summarize(self, keyword: str) -> str:
        """뉴스 수집 및 요약"""
        news_data = await crawler_service.search_news(keyword)

        prompt = f"""
다음 뉴스를 요약해주세요:

{news_data}

요약 형식:
- 한 줄 요약
- 주요 내용 (3개 포인트)
- 관련 키워드
"""
        return await self.respond(prompt)

    async def trend_report(self, topic: str) -> str:
        """트렌드 리포트 생성"""
        news_data = await crawler_service.search_news(topic)

        prompt = f"""
'{topic}' 관련 트렌드 리포트를 작성해주세요.

수집된 정보:
{news_data}

리포트 형식:
## 📊 트렌드 리포트: {topic}

### 1. 현재 동향
### 2. 주요 이슈
### 3. 시장 영향
### 4. 향후 전망
### 5. 권장 액션
"""
        return await self.respond(prompt)
