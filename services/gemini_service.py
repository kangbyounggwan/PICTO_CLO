"""Gemini API 서비스 (Google Search Grounding 지원)"""

from google import genai
from google.genai import types
from config.settings import settings


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.max_tokens = settings.max_tokens

    async def chat(
        self,
        message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None,
        use_search: bool = False,
    ) -> str:
        """Gemini API로 대화 생성 (선택적 Google Search Grounding)"""
        try:
            print(f"[Gemini] use_search={use_search}, model={self.model_name}")
            # 시스템 프롬프트 + 히스토리 + 현재 메시지 구성
            full_prompt = f"[시스템 지침]\n{system_prompt}\n\n"

            if conversation_history:
                full_prompt += "[이전 대화]\n"
                for msg in conversation_history:
                    role = "사용자" if msg["role"] == "user" else "AI"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += "\n"

            full_prompt += f"[현재 질문]\n사용자: {message}"

            # 설정 구성
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=0.7,
            )

            # Google Search Grounding 활성화
            if use_search:
                config.tools = [types.Tool(google_search=types.GoogleSearch())]
                print(f"[Gemini] Google Search Grounding 활성화됨")

            print(f"[Gemini] API 호출 시작...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config,
            )

            print(f"[Gemini] API 호출 성공, 응답 길이: {len(response.text)}")
            return response.text

        except Exception as e:
            print(f"[Gemini] ERROR: {str(e)}")
            return f"⚠️ 오류가 발생했습니다: {str(e)}"

    async def chat_with_search(
        self,
        message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Google Search Grounding을 사용한 대화 (실시간 정보 포함)"""
        return await self.chat(message, system_prompt, conversation_history, use_search=True)

    async def quick_response(self, message: str, system_prompt: str) -> str:
        """단일 응답 (히스토리 없음)"""
        return await self.chat(message, system_prompt, None)

    async def search_and_respond(self, query: str, system_prompt: str = "") -> str:
        """웹 검색 후 응답 생성 (실시간 정보 필요 시)"""
        search_prompt = system_prompt or "당신은 최신 정보를 검색하여 정확하게 답변하는 AI입니다."
        return await self.chat(query, search_prompt, None, use_search=True)


# 싱글톤 인스턴스
gemini_service = GeminiService()
