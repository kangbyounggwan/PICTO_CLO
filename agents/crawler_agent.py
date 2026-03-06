"""스카우트(Scout) - P!CKTO 정보수집 AI 에이전트"""

from .base_agent import BaseAgent
from services.gemini_service import gemini_service


class CrawlerAgent(BaseAgent):
    """뉴스 및 정보 수집 에이전트 (Google Search Grounding 사용)"""

    agent_type = "crawler"

    # P!CKTO 스카우트 역할에 맞는 검색 프롬프트
    SCOUT_SEARCH_PROMPT = """
너는 P!CKTO(픽토) 팀의 정보 수집 AI "스카우트"야.
스포츠 예측 서비스 운영에 필요한 최신 뉴스와 트렌드를 모니터링하고
핵심 인사이트를 전달하는 역할이야.

[DOMAIN EXPERTISE]
- 종목: 축구(K리그), 야구(KBO), 농구(KBL), 배구(V리그)
- 기술: AI/ML 예측 모델, 스포츠 데이터 분석
- 서비스: 스포츠테크, 예측 앱, 배당률 분석 플랫폼

[수집 우선순위]
🔴 [긴급] P!CKTO 서비스에 직접 영향 (API 변경, 리그 일정 변동 등)
🟡 [중요] 예측 정확도에 영향 (선수 부상, 전력 변동)
🟢 [참고] 시장/기술 트렌드

[출력 형식]
📰 {카테고리} | {날짜}

▶ 제목: {뉴스 핵심 한줄}
📌 요약: {3줄 이내 핵심 내용}
🎯 P!CKTO 영향도: {상/중/하}
💡 액션 포인트: {서비스에 필요한 조치}

출처 명시 필수. 루머/추측은 명확히 구분 표시할 것.
"""

    async def process(self, message: str, **kwargs) -> str:
        """크롤링 관련 메시지 처리 - Google Search로 실시간 정보 검색"""
        clean_message = message
        for trigger in self.triggers:
            clean_message = clean_message.replace(trigger, "").strip()

        if clean_message:
            # Google Search Grounding으로 실시간 검색 및 분석
            return await gemini_service.chat_with_search(
                clean_message,
                self.SCOUT_SEARCH_PROMPT,
                kwargs.get("history")
            )
        else:
            return await self.respond(
                "어떤 주제의 뉴스나 정보를 찾아드릴까요?\n"
                "예: K리그 이적 뉴스, KBO 선발 로테이션, AI 스포츠 예측 기술 등",
                kwargs.get("history")
            )

    async def fetch_sports_news(self, sport: str = "전체") -> str:
        """스포츠 뉴스 수집 (K리그, KBO, KBL, V리그)"""
        sport_queries = {
            "축구": "K리그 축구 최신 뉴스 이적 부상",
            "야구": "KBO 야구 최신 뉴스 선발 로테이션",
            "농구": "KBL 농구 최신 뉴스 경기 결과",
            "배구": "V리그 배구 최신 뉴스 경기 일정",
            "전체": "K리그 KBO KBL V리그 오늘 경기 뉴스"
        }
        query = sport_queries.get(sport, sport_queries["전체"])

        prompt = f"""
{self.SCOUT_SEARCH_PROMPT}

다음 주제로 최신 스포츠 뉴스를 검색하고 P!CKTO 관점에서 분석해줘:
{query}

특히 예측 정확도에 영향을 줄 수 있는 정보(부상, 이적, 컨디션)에 집중해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)

    async def fetch_tech_news(self) -> str:
        """AI/기술 뉴스 수집"""
        query = "AI 스포츠 예측 기술 LLM 에이전트 최신 동향"
        prompt = f"""
{self.SCOUT_SEARCH_PROMPT}

다음 주제로 기술 뉴스를 검색해줘:
{query}

P!CKTO AI 예측 서비스 개선에 활용할 수 있는 기술 트렌드 위주로 분석해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)

    async def daily_briefing(self) -> str:
        """일간 브리핑 생성"""
        prompt = """
{self.SCOUT_SEARCH_PROMPT}

오늘의 P!CKTO 일간 브리핑을 작성해줘.

포함 내용:
1. 오늘 예정된 K리그/KBO/KBL/V리그 경기 일정
2. 주요 스포츠 뉴스 (부상, 이적, 감독 교체 등)
3. 각 경기별 주목 포인트

시간대: KST 기준으로 작성해줘.
"""
        query = "오늘 K리그 KBO KBL V리그 경기 일정 스포츠 뉴스"
        return await gemini_service.chat_with_search(query, prompt)

    async def trend_report(self, topic: str) -> str:
        """트렌드 리포트 생성"""
        prompt = f"""
{self.SCOUT_SEARCH_PROMPT}

'{topic}' 관련 트렌드 리포트를 작성해줘.

리포트 형식:
## 📊 P!CKTO 트렌드 리포트: {topic}

### 1. 현재 동향
- 최신 뉴스 및 트렌드 요약

### 2. 주요 이슈
- P!CKTO 서비스에 영향을 줄 수 있는 이슈

### 3. 경쟁사 동향
- 스포츠테크/예측 서비스 시장 현황

### 4. 향후 전망
- 단기/중기 전망

### 5. 권장 액션
- P!CKTO 팀이 취해야 할 조치

출처를 명시하고 데이터 기반으로 분석해줘.
"""
        return await gemini_service.chat_with_search(topic, prompt)

    async def competitor_analysis(self) -> str:
        """경쟁사 분석"""
        query = "스포츠 예측 앱 승부예측 서비스 시장 동향 2026"
        prompt = f"""
{self.SCOUT_SEARCH_PROMPT}

스포츠 예측 서비스 시장 경쟁사 분석을 해줘.

분석 항목:
1. 국내 주요 경쟁 서비스
2. 차별화 포인트 비교
3. 시장 트렌드
4. P!CKTO가 참고할 만한 전략

객관적 데이터 기반으로 분석해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)
