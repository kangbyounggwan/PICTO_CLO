"""뉴스 및 웹 크롤링 서비스"""

import httpx
import feedparser
from bs4 import BeautifulSoup
from dataclasses import dataclass
from config.settings import settings


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    source: str


class CrawlerService:
    # 한국 주요 뉴스 RSS 피드
    NEWS_FEEDS = {
        "연합뉴스": "https://www.yonhapnewstv.co.kr/browse/feed/",
        "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml",
        "한겨레": "https://www.hani.co.kr/rss/",
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._search_service = None

    @property
    def search_service(self):
        """SerpAPI 서비스 lazy loading"""
        if self._search_service is None and settings.serpapi_key:
            from services.search_service import search_service
            self._search_service = search_service
        return self._search_service

    async def fetch_news(self, keyword: str | None = None, limit: int = 5) -> list[NewsItem]:
        """뉴스 피드에서 기사 가져오기"""
        all_news = []

        for source, feed_url in self.NEWS_FEEDS.items():
            try:
                response = await self.client.get(feed_url)
                feed = feedparser.parse(response.text)

                for entry in feed.entries[:limit]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))

                    # 키워드 필터링
                    if keyword:
                        if keyword.lower() not in title.lower() and keyword.lower() not in summary.lower():
                            continue

                    all_news.append(NewsItem(
                        title=title,
                        link=entry.get("link", ""),
                        summary=summary[:200] + "..." if len(summary) > 200 else summary,
                        source=source,
                    ))
            except Exception:
                continue

        return all_news[:limit]

    async def scrape_page(self, url: str) -> str:
        """웹 페이지 내용 스크래핑"""
        try:
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # 스크립트, 스타일 제거
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            return text[:3000]  # 최대 3000자

        except Exception as e:
            return f"스크래핑 실패: {str(e)}"

    async def search_news(self, query: str) -> str:
        """뉴스 검색 결과를 포맷팅된 문자열로 반환 (SerpAPI 우선)"""
        # SerpAPI가 설정되어 있으면 실시간 검색 사용
        if self.search_service:
            results = await self.search_service.search_news(query, num_results=5)
            if results:
                return await self.search_service.format_results(query, results, "뉴스")

        # Fallback: RSS 피드 기반 검색
        news_items = await self.fetch_news(keyword=query, limit=5)

        if not news_items:
            return f"'{query}' 관련 뉴스를 찾지 못했습니다."

        result = f"📰 '{query}' 관련 뉴스 ({len(news_items)}건)\n\n"
        for i, item in enumerate(news_items, 1):
            result += f"{i}. [{item.source}] {item.title}\n"
            result += f"   {item.summary}\n"
            result += f"   🔗 {item.link}\n\n"

        return result

    async def web_search(self, query: str) -> str:
        """웹 검색 (SerpAPI 사용)"""
        if not self.search_service:
            return "⚠️ 웹 검색 기능을 사용하려면 SERPAPI_KEY를 설정해주세요."

        results = await self.search_service.search(query, num_results=5)
        return await self.search_service.format_results(query, results, "검색")

    async def close(self):
        await self.client.aclose()


# 싱글톤 인스턴스
crawler_service = CrawlerService()
