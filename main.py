"""OpenClo 팀 AI 봇 - 3개 봇 동시 실행"""

import asyncio
import sys
import io
from pathlib import Path

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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


async def create_bot_handler(agent_type: str):
    """에이전트 타입별 메시지 핸들러 생성"""
    profile = AGENT_PROFILES[agent_type]

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = profile["name"]
        emoji = profile["emoji"]
        await update.message.reply_text(
            f"{emoji} 안녕하세요! 저는 **{name}**입니다.\n\n"
            f"무엇을 도와드릴까요?",
            parse_mode="Markdown"
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user_id = update.effective_user.id

        # 생각 중 표시
        thinking_msg = await update.message.reply_text("...")

        try:
            # Gemini 응답 생성
            response = await gemini.chat(
                message=user_message,
                system_prompt=profile["system_prompt"],
                conversation_history=None
            )

            # 응답 전송
            emoji = profile["emoji"]
            name = profile["name"]
            await thinking_msg.edit_text(
                f"{emoji} **{name}**\n\n{response}",
                parse_mode="Markdown"
            )

            # 대화 저장
            await db.save_message(user_id, "user", user_message, agent_type)
            await db.save_message(user_id, "assistant", response, agent_type)

        except Exception as e:
            await thinking_msg.edit_text(f"오류가 발생했습니다: {str(e)}")

    return start, handle_message


async def run_bot(token: str, agent_type: str, name: str):
    """개별 봇 실행"""
    print(f"[{name}] 봇 시작 중...")

    app = Application.builder().token(token).build()

    start_handler, message_handler = await create_bot_handler(agent_type)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print(f"[{name}] 봇 실행 중!")

    return app


async def main():
    """메인 함수 - 3개 봇 동시 실행"""
    print("""
==========================================
       OpenClo Team AI Bots
==========================================
  팀원: CEO(임웅배), CTO(강병관)
------------------------------------------
  [1] 마키 (Marky) - 마케팅
  [2] 서보 (Servo) - 서버관리
  [3] 스카우트 (Scout) - 정보수집
==========================================
    """)

    # 설정 확인
    errors = []
    if not settings.gemini_api_key:
        errors.append("[X] GEMINI_API_KEY 없음")
    if not settings.marky_bot_token:
        errors.append("[X] MARKY_BOT_TOKEN 없음")
    if not settings.servo_bot_token:
        errors.append("[X] SERVO_BOT_TOKEN 없음")
    if not settings.scout_bot_token:
        errors.append("[X] SCOUT_BOT_TOKEN 없음")

    if errors:
        print("\n설정 오류:")
        for e in errors:
            print(f"  {e}")
        return

    # 데이터베이스 초기화
    await db.initialize()

    # 3개 봇 동시 시작
    bots = []
    try:
        marky = await run_bot(settings.marky_bot_token, "marketing", "마키")
        bots.append(marky)

        servo = await run_bot(settings.servo_bot_token, "server", "서보")
        bots.append(servo)

        scout = await run_bot(settings.scout_bot_token, "crawler", "스카우트")
        bots.append(scout)

        print("\n[OK] 3개 봇 모두 실행 중! Ctrl+C로 종료\n")

        # 무한 대기
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n봇 종료 중...")
    finally:
        for bot in bots:
            try:
                await bot.updater.stop()
                await bot.stop()
                await bot.shutdown()
            except:
                pass
        print("Bye!")


if __name__ == "__main__":
    asyncio.run(main())
