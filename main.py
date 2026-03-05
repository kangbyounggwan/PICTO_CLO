"""OpenClo 팀 AI 봇 - 3개 봇 동시 실행"""

import asyncio
import sys
import re
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config.settings import settings
from config.agents import AGENT_PROFILES
from services.gemini_service import GeminiService
from database.models import Database


# Gemini 서비스
gemini = GeminiService()
db = Database()


def escape_telegram(text: str) -> str:
    """텔레그램 특수문자 이스케이프"""
    # 마크다운 특수문자 제거/이스케이프
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("``", "")
    text = text.replace("*", "")
    text = text.replace("_", " ")
    text = text.replace("`", "'")
    text = text.replace("[", "(")
    text = text.replace("]", ")")
    return text


def create_bot_handlers(agent_type: str, bot_username: str):
    """에이전트 타입별 메시지 핸들러 생성"""
    profile = AGENT_PROFILES[agent_type]

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = profile["name"]
        emoji = profile["emoji"]
        await update.message.reply_text(
            f"{emoji} 안녕하세요! 저는 {name}입니다.\n\n무엇을 도와드릴까요?"
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
        chat_type = update.effective_chat.type

        # 그룹 채팅인 경우: 자기 봇이 멘션되었을 때만 응답
        if chat_type in ["group", "supergroup"]:
            # 대소문자 무시하고 봇 유저네임 체크
            if bot_username.lower() not in user_message.lower():
                return  # 내 멘션 아니면 무시

            # 멘션 제거 (대소문자 무시)
            pattern = re.compile(re.escape(f"@{bot_username}"), re.IGNORECASE)
            user_message = pattern.sub("", user_message).strip()

        if not user_message:
            user_message = "안녕하세요"

        user_id = update.effective_user.id

        # 생각 중 표시
        thinking_msg = await update.message.reply_text("생각 중...")

        try:
            # Gemini 응답 생성
            response = await gemini.chat(
                message=user_message,
                system_prompt=profile["system_prompt"],
                conversation_history=None
            )

            # 특수문자 이스케이프
            safe_response = escape_telegram(response)

            # 응답 전송
            emoji = profile["emoji"]
            name = profile["name"]
            final_text = f"{emoji} {name}\n\n{safe_response}"

            # 4096자 제한
            if len(final_text) > 4000:
                final_text = final_text[:4000] + "..."

            await thinking_msg.edit_text(final_text)

            # 대화 저장
            await db.save_message(user_id, "user", user_message, agent_type)
            await db.save_message(user_id, "assistant", response, agent_type)

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[ERROR] {agent_type}: {error_msg}")
            await thinking_msg.edit_text(f"죄송합니다. 오류가 발생했습니다.")

    return start, handle_message


async def run_bot(token: str, agent_type: str, name: str, bot_username: str):
    """개별 봇 실행"""
    print(f"[{name}] 시작... (@{bot_username})")

    app = Application.builder().token(token).build()

    start_handler, message_handler = create_bot_handlers(agent_type, bot_username)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print(f"[{name}] 실행 중!")
    return app


async def main():
    """메인 함수 - 3개 봇 동시 실행"""
    print("=" * 40)
    print("    PICTO AI Team Bots")
    print("=" * 40)

    # 설정 확인
    if not settings.gemini_api_key:
        print("[X] GEMINI_API_KEY 없음")
        return
    if not settings.marky_bot_token:
        print("[X] MARKY_BOT_TOKEN 없음")
        return
    if not settings.servo_bot_token:
        print("[X] SERVO_BOT_TOKEN 없음")
        return
    if not settings.scout_bot_token:
        print("[X] SCOUT_BOT_TOKEN 없음")
        return

    # 데이터베이스 초기화
    await db.initialize()

    # 3개 봇 동시 시작
    bots = []
    try:
        marky = await run_bot(
            settings.marky_bot_token,
            "marketing",
            "마키",
            "sport_Marky_bot"
        )
        bots.append(marky)

        servo = await run_bot(
            settings.servo_bot_token,
            "server",
            "서보",
            "servo_ai_bot"
        )
        bots.append(servo)

        scout = await run_bot(
            settings.scout_bot_token,
            "crawler",
            "스카우트",
            "PICKTO_scout_ai_bot"
        )
        bots.append(scout)

        print("\n[OK] 3개 봇 실행 중!\n")

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"오류: {e}")
    finally:
        for bot in bots:
            try:
                await bot.updater.stop()
                await bot.stop()
                await bot.shutdown()
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())
