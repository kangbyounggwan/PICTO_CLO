"""Gemini API 서비스"""

import google.generativeai as genai
from config.settings import settings


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "max_output_tokens": settings.max_tokens,
                "temperature": 0.7,
            }
        )

    async def chat(
        self,
        message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Gemini API로 대화 생성"""
        try:
            # 시스템 프롬프트 + 히스토리 + 현재 메시지 구성
            full_prompt = f"[시스템 지침]\n{system_prompt}\n\n"

            if conversation_history:
                full_prompt += "[이전 대화]\n"
                for msg in conversation_history:
                    role = "사용자" if msg["role"] == "user" else "AI"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += "\n"

            full_prompt += f"[현재 질문]\n사용자: {message}"

            response = self.model.generate_content(full_prompt)
            return response.text

        except Exception as e:
            return f"⚠️ 오류가 발생했습니다: {str(e)}"

    async def quick_response(self, message: str, system_prompt: str) -> str:
        """단일 응답 (히스토리 없음)"""
        return await self.chat(message, system_prompt, None)


# 싱글톤 인스턴스
gemini_service = GeminiService()
