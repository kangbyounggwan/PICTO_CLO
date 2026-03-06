"""SerpAPI를 사용한 실시간 웹 검색 서비스"""

import httpx
from dataclasses import dataclass
from config.settings import settings


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    source: str = "Google"


class SearchService:
    """SerpAPI를 사용한 Google 검색 서비스"""

    BASE_URL = "https://serpapi.com/search"

    def __init__(self):
        self.api_key = settings.serpapi_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "google"
    ) -> list[SearchResult]:
        """Google 검색 수행"""
        if not self.api_key:
            return []

        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": search_type,
            "num": num_results,
            "hl": "ko",  # 한국어 결과
            "gl": "kr",  # 한국 지역
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.json()

            results = []
            organic_results = data.get("organic_results", [])

            for item in organic_results[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("source", "Google")
                ))

            return results

        except Exception as e:
            print(f"SerpAPI 검색 오류: {e}")
            return []

    async def search_news(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Google 뉴스 검색"""
        if not self.api_key:
            return []

        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google_news",
            "gl": "kr",
            "hl": "ko",
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.json()

            results = []
            news_results = data.get("news_results", [])

            for item in news_results[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", item.get("date", "")),
                    source=item.get("source", {}).get("name", "뉴스")
                ))

            return results

        except Exception as e:
            print(f"SerpAPI 뉴스 검색 오류: {e}")
            return []

    async def format_results(self, query: str, results: list[SearchResult], result_type: str = "검색") -> str:
        """검색 결과를 포맷팅된 문자열로 반환"""
        if not results:
            return f"'{query}' 관련 {result_type} 결과를 찾지 못했습니다."

        formatted = f"🔍 '{query}' {result_type} 결과 ({len(results)}건)\n\n"

        for i, item in enumerate(results, 1):
            formatted += f"{i}. [{item.source}] {item.title}\n"
            formatted += f"   {item.snippet}\n"
            formatted += f"   🔗 {item.link}\n\n"

        return formatted

    async def close(self):
        await self.client.aclose()


# 싱글톤 인스턴스
search_service = SearchService()
