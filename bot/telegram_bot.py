"""텔레그램 봇 메인 클래스"""

from telegram.ext import Application
from config.settings import settings
from .handlers import setup_handlers


class TelegramBot:
    """텔레그램 봇 관리 클래스"""

    def __init__(self):
        self.token = settings.telegram_bot_token
        self.app: Application | None = None

    async def initialize(self):
        """봇 초기화"""
        self.app = Application.builder().token(self.token).build()
        setup_handlers(self.app)
        print("✅ 텔레그램 봇 초기화 완료")

    async def start(self):
        """봇 시작 (polling 모드)"""
        if not self.app:
            await self.initialize()

        print("🚀 봇 시작...")
        print("📱 텔레그램에서 봇과 대화를 시작하세요!")

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

    async def stop(self):
        """봇 중지"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            print("🛑 봇 중지됨")

    def run(self):
        """봇 실행 (블로킹)"""
        import asyncio

        async def main():
            await self.start()
            # 무한 대기
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await self.stop()

        asyncio.run(main())
