"""스카우트(Scout) - P!CKTO 정보수집 AI 에이전트"""

from datetime import datetime
from zoneinfo import ZoneInfo

from .base_agent import BaseAgent
from services.gemini_service import gemini_service


class CrawlerAgent(BaseAgent):
    """뉴스 및 정보 수집 에이전트 (Google Search Grounding 사용)"""

    agent_type = "crawler"

    @staticmethod
    def get_today_kst() -> str:
        """현재 날짜를 KST 기준으로 반환"""
        kst = ZoneInfo("Asia/Seoul")
        return datetime.now(kst).strftime("%Y년 %m월 %d일")

    def get_scout_prompt(self) -> str:
        """현재 날짜가 포함된 스카우트 프롬프트 생성"""
        today = self.get_today_kst()
        return f"""
너는 P!CKTO(픽토) 팀의 정보 수집 AI "스카우트"야.
스포츠 예측 서비스 운영에 필요한 최신 정보를 수집하고 전달하는 역할이야.

[필수] 오늘 날짜: {today} (KST 기준)
모든 응답에서 이 날짜를 사용해. 다른 날짜 사용 금지!

[DOMAIN EXPERTISE]
- 야구: KBO, MLB, NPB, WBC, 프리미어12, 올림픽
- 축구: K리그, EPL, 라리가, 분데스리가, 세리에A, 월드컵, AFC
- 농구: KBL, NBA, FIBA
- 배구: V리그, 국제대회
- 기술: AI/ML 예측 모델, 스포츠 데이터 분석

모든 스포츠 정보를 수집해. 국내 리그만 한정하지 말 것!

[요청 유형별 응답]

1. "경기 일정/총정리/리스트" 요청 시:
   ⚾ {today} 경기 일정

   | 시간 | 홈팀 vs 원정팀 | 구장 | 비고 |
   |------|---------------|------|------|
   | 18:30 | 삼성 vs LG | 대구 | 선발: OOO vs OOO |

   - 실제 경기 일정, 시간, 구장, 선발투수 정보 제공
   - 경기가 없으면 "오늘 경기 없음" 명시

2. "뉴스/트렌드/동향" 요청 시:
   📰 {{카테고리}} | {today}
   ▶ 제목: {{핵심 한줄}}
   📌 요약: {{3줄 이내}}
   🎯 P!CKTO 영향도: {{상/중/하}}

출처 명시 필수.

[중요] 응답 규칙:
- 검색 결과를 바탕으로 상세하게 답변할 것
- "경기가 없다"고 판단하기 전에 충분히 검색할 것
- 최소 200자 이상 상세하게 응답할 것
- 검색된 출처/링크를 반드시 포함할 것
"""

    async def process(self, message: str, **kwargs) -> str:
        """크롤링 관련 메시지 처리 - 항상 Google Search로 실시간 정보 검색"""
        clean_message = message
        for trigger in self.triggers:
            clean_message = clean_message.replace(trigger, "").strip()

        if not clean_message:
            clean_message = "P!CKTO 스포츠 정보 수집 AI 스카우트 소개"

        # 경기 일정/총정리 요청인지 확인
        schedule_keywords = ["경기", "일정", "총정리", "리스트", "오늘", "내일", "스케줄"]
        is_schedule_request = any(kw in clean_message for kw in schedule_keywords)

        # 오늘 날짜를 쿼리에 명시적으로 포함
        today = self.get_today_kst()

        if is_schedule_request:
            # 경기 일정 검색 쿼리 생성 (국내 + 해외 리그 전체)
            sport_type = ""
            if "야구" in clean_message or "KBO" in clean_message.upper() or "MLB" in clean_message.upper() or "WBC" in clean_message.upper():
                sport_type = "KBO MLB NPB WBC 야구"
            elif "축구" in clean_message or "K리그" in clean_message or "EPL" in clean_message.upper() or "라리가" in clean_message:
                sport_type = "K리그 EPL 라리가 분데스리가 세리에A 챔피언스리그 축구"
            elif "농구" in clean_message or "KBL" in clean_message.upper() or "NBA" in clean_message.upper():
                sport_type = "KBL NBA 농구"
            elif "배구" in clean_message or "V리그" in clean_message:
                sport_type = "V리그 배구"
            else:
                # 전체 스포츠 검색 (국내 + 해외 모든 주요 리그)
                sport_type = "KBO MLB EPL 라리가 챔피언스리그 NBA KBL V리그 스포츠"

            # 날짜를 쿼리에 명시적으로 포함
            query = f"{today} {sport_type} 오늘 경기 일정"
        else:
            # 일반 쿼리에도 날짜 포함
            query = f"{today} {clean_message}"

        # 항상 Google Search 사용 - 실시간 날짜 인식
        prompt = self.get_scout_prompt()
        response = await gemini_service.chat_with_search(
            query,
            prompt,
            kwargs.get("history")
        )
        return f"{self.emoji} **{self.name}**\n\n{response}"

    async def fetch_sports_news(self, sport: str = "전체") -> str:
        """스포츠 뉴스 수집 (K리그, KBO, KBL, V리그)"""
        today = self.get_today_kst()
        sport_queries = {
            "축구": f"{today} K리그 축구 최신 뉴스 이적 부상",
            "야구": f"{today} KBO 야구 최신 뉴스 선발 로테이션",
            "농구": f"{today} KBL 농구 최신 뉴스 경기 결과",
            "배구": f"{today} V리그 배구 최신 뉴스 경기 일정",
            "전체": f"{today} K리그 KBO KBL V리그 오늘 경기 뉴스"
        }
        query = sport_queries.get(sport, sport_queries["전체"])

        prompt = f"""
{self.get_scout_prompt()}

다음 주제로 최신 스포츠 뉴스를 검색하고 P!CKTO 관점에서 분석해줘:
{query}

특히 예측 정확도에 영향을 줄 수 있는 정보(부상, 이적, 컨디션)에 집중해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)

    async def fetch_tech_news(self) -> str:
        """AI/기술 뉴스 수집"""
        today = self.get_today_kst()
        query = f"{today} AI 스포츠 예측 기술 LLM 에이전트 최신 동향"
        prompt = f"""
{self.get_scout_prompt()}

다음 주제로 기술 뉴스를 검색해줘:
{query}

P!CKTO AI 예측 서비스 개선에 활용할 수 있는 기술 트렌드 위주로 분석해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)

    async def daily_briefing(self) -> str:
        """일간 브리핑 생성"""
        today = self.get_today_kst()
        prompt = f"""
{self.get_scout_prompt()}

{today} P!CKTO 일간 브리핑을 작성해줘.

포함 내용:
1. 오늘({today}) 예정된 K리그/KBO/KBL/V리그 경기 일정
2. 주요 스포츠 뉴스 (부상, 이적, 감독 교체 등)
3. 각 경기별 주목 포인트

시간대: KST 기준으로 작성해줘.
"""
        query = f"{today} K리그 KBO KBL V리그 경기 일정 스포츠 뉴스"
        return await gemini_service.chat_with_search(query, prompt)

    async def trend_report(self, topic: str) -> str:
        """트렌드 리포트 생성"""
        today = self.get_today_kst()
        prompt = f"""
{self.get_scout_prompt()}

'{topic}' 관련 트렌드 리포트를 작성해줘. (기준일: {today})

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
        today = self.get_today_kst()
        query = f"{today} 스포츠 예측 앱 승부예측 서비스 시장 동향 2026"
        prompt = f"""
{self.get_scout_prompt()}

스포츠 예측 서비스 시장 경쟁사 분석을 해줘. (기준일: {today})

분석 항목:
1. 국내 주요 경쟁 서비스
2. 차별화 포인트 비교
3. 시장 트렌드
4. P!CKTO가 참고할 만한 전략

객관적 데이터 기반으로 분석해줘.
"""
        return await gemini_service.chat_with_search(query, prompt)
