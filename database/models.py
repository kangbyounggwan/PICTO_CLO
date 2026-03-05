"""데이터베이스 모델 및 관리"""

import aiosqlite
from datetime import datetime, date
from pathlib import Path
from config.settings import settings


class Database:
    """SQLite 데이터베이스 관리"""

    def __init__(self):
        self.db_path = settings.database_path
        self._ensure_directory()

    def _ensure_directory(self):
        """데이터베이스 디렉토리 생성"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """데이터베이스 테이블 초기화"""
        async with aiosqlite.connect(self.db_path) as db:
            # 대화 히스토리 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    agent_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 사용량 통계 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    count INTEGER DEFAULT 1,
                    UNIQUE(user_id, date)
                )
            """)

            # 인덱스 생성
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user
                ON conversations(user_id, created_at DESC)
            """)

            await db.commit()
            print("✅ 데이터베이스 초기화 완료")

    async def save_message(
        self,
        user_id: int,
        role: str,
        content: str,
        agent_type: str | None = None,
    ):
        """메시지 저장"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversations (user_id, role, content, agent_type)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, role, content, agent_type),
            )

            # 사용량 업데이트 (user 메시지만)
            if role == "user":
                today = date.today().isoformat()
                await db.execute(
                    """
                    INSERT INTO usage_stats (user_id, date, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(user_id, date) DO UPDATE SET count = count + 1
                    """,
                    (user_id, today),
                )

            await db.commit()

    async def get_conversation_history(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """대화 히스토리 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT role, content FROM conversations
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()

            # Claude API 형식으로 변환 (역순으로)
            history = []
            for row in reversed(rows):
                history.append({
                    "role": row["role"],
                    "content": row["content"],
                })
            return history

    async def get_user_usage(self, user_id: int) -> dict:
        """사용자 사용량 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            # 오늘 사용량
            today = date.today().isoformat()
            cursor = await db.execute(
                "SELECT count FROM usage_stats WHERE user_id = ? AND date = ?",
                (user_id, today),
            )
            row = await cursor.fetchone()
            today_count = row[0] if row else 0

            # 총 사용량
            cursor = await db.execute(
                "SELECT SUM(count) FROM usage_stats WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            total_count = row[0] if row and row[0] else 0

            return {
                "today": today_count,
                "total": total_count,
            }

    async def clear_old_conversations(self, days: int = 30):
        """오래된 대화 삭제"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM conversations
                WHERE created_at < datetime('now', ?)
                """,
                (f"-{days} days",),
            )
            await db.commit()
