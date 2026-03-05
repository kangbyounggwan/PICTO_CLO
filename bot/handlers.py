"""텔레그램 봇 메시지 핸들러"""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config.settings import settings
from agents import MarketingAgent, ServerAgent, CrawlerAgent
from database.models import Database


# 에이전트 인스턴스
marketing_agent = MarketingAgent()
server_agent = ServerAgent()
crawler_agent = CrawlerAgent()

# 데이터베이스
db = Database()


def is_authorized(user_id: int) -> bool:
    """권한 확인"""
    if not settings.authorized_users:
        return True  # 권한 설정이 없으면 모두 허용
    return user_id in settings.authorized_users


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    user = update.effective_user
    welcome_message = f"""
👋 안녕하세요, {user.first_name}님!

**OpenClo 팀 AI 어시스턴트**입니다.

🤖 **사용 가능한 AI 에이전트:**
• `@marketing` - 마케팅 AI (콘텐츠, 전략)
• `@server` - 서버관리 AI (인프라, 배포)
• `@crawler` - 크롤러 AI (뉴스, 트렌드)

📝 **명령어:**
• /help - 도움말
• /status - 상태 확인
• /news [키워드] - 뉴스 검색

메시지를 보내시면 적절한 AI가 응답합니다!
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어"""
    help_text = """
📚 **사용 가이드**

**AI 에이전트 호출:**
• `@marketing 인스타 광고 문구 작성해줘`
• `@server 배포 체크리스트 만들어줘`
• `@crawler AI 스타트업 뉴스 찾아줘`

**특수 명령어:**
• `/news 키워드` - 뉴스 검색
• `/trend 주제` - 트렌드 리포트
• `/status` - 봇 상태

**팁:**
• 에이전트 없이 메시지를 보내면 자동으로 적합한 AI가 응답
• 대화 맥락이 유지되므로 자연스럽게 대화 가능
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """상태 확인 명령어"""
    user_id = update.effective_user.id
    usage = await db.get_user_usage(user_id)

    status_text = f"""
📊 **봇 상태**

✅ 정상 운영 중

👤 **사용자 통계:**
• 오늘 사용: {usage.get('today', 0)}건
• 총 사용: {usage.get('total', 0)}건

🤖 **에이전트 상태:**
• 마케팅AI: ✅ 활성
• 서버AI: ✅ 활성
• 크롤러AI: ✅ 활성
"""
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """뉴스 검색 명령어"""
    if not context.args:
        await update.message.reply_text("❓ 검색할 키워드를 입력해주세요.\n예: `/news AI 스타트업`", parse_mode="Markdown")
        return

    keyword = " ".join(context.args)
    await update.message.reply_text(f"🔍 '{keyword}' 뉴스를 검색 중...")

    response = await crawler_agent.fetch_and_summarize(keyword)
    await update.message.reply_text(response, parse_mode="Markdown")


async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """트렌드 리포트 명령어"""
    if not context.args:
        await update.message.reply_text("❓ 주제를 입력해주세요.\n예: `/trend 핀테크`", parse_mode="Markdown")
        return

    topic = " ".join(context.args)
    await update.message.reply_text(f"📊 '{topic}' 트렌드 리포트 생성 중...")

    response = await crawler_agent.trend_report(topic)
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 메시지 처리"""
    user_id = update.effective_user.id
    message = update.message.text

    # 권한 확인
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ 권한이 없습니다. 관리자에게 문의하세요.")
        return

    # 대화 히스토리 가져오기
    history = await db.get_conversation_history(user_id, limit=10)

    # 적절한 에이전트 선택
    if marketing_agent.matches_trigger(message):
        agent = marketing_agent
    elif server_agent.matches_trigger(message):
        agent = server_agent
    elif crawler_agent.matches_trigger(message):
        agent = crawler_agent
    else:
        # 내용 기반 자동 라우팅
        message_lower = message.lower()
        if any(kw in message_lower for kw in ["마케팅", "광고", "콘텐츠", "sns", "홍보"]):
            agent = marketing_agent
        elif any(kw in message_lower for kw in ["서버", "배포", "에러", "장애", "인프라"]):
            agent = server_agent
        elif any(kw in message_lower for kw in ["뉴스", "트렌드", "검색", "정보", "기사"]):
            agent = crawler_agent
        else:
            # 기본: 마케팅 에이전트 (또는 일반 응답)
            agent = marketing_agent

    # 응답 생성
    await update.message.reply_text("💭 생각 중...")

    response = await agent.process(message, history=history)

    # 대화 저장
    await db.save_message(user_id, "user", message)
    await db.save_message(user_id, "assistant", response)

    # 응답 전송
    await update.message.reply_text(response, parse_mode="Markdown")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """에러 핸들러"""
    print(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")


def setup_handlers(app: Application):
    """핸들러 등록"""
    # 명령어 핸들러
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("trend", trend_command))

    # 메시지 핸들러
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 에러 핸들러
    app.add_error_handler(error_handler)
