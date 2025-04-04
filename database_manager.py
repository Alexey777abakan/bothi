import sqlite3
import logging
from datetime import datetime, timezone, timedelta  # Убедимся, что timedelta импортирован
import asyncio
import aiosqlite

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

DB_PATH = "telegram_bot_data.db"

async def setup_database():
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                chat_id INTEGER PRIMARY KEY,
                theme TEXT,
                post_count INTEGER,
                style TEXT,
                channel_id TEXT,
                subscription_end TEXT,
                subscription_plan TEXT,
                language TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                chat_id INTEGER,
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                hashtags TEXT,
                file_id TEXT,
                image_prompt TEXT,
                message_id INTEGER,
                created_at TEXT,
                FOREIGN KEY (chat_id) REFERENCES clients(chat_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                chat_id INTEGER,
                post_id INTEGER,
                channel_id TEXT,
                publish_datetime TEXT,
                FOREIGN KEY (chat_id) REFERENCES clients(chat_id),
                FOREIGN KEY (post_id) REFERENCES posts(post_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                chat_id INTEGER,
                action TEXT,
                timestamp TEXT,
                FOREIGN KEY (chat_id) REFERENCES clients(chat_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_chat_created ON posts(chat_id, created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_usage_stats_chat ON usage_stats(chat_id)")
        await db.commit()
        logging.info(f"Database initialized at {DB_PATH} with all tables")

async def save_client_settings(chat_id, **kwargs):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        fields = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?' for _ in kwargs])
        values = list(kwargs.values())
        await db.execute(f"""
            INSERT OR REPLACE INTO clients (chat_id, {fields})
            VALUES (?, {placeholders})
        """, [chat_id] + values)
        await db.commit()

async def get_client_settings(chat_id):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        async with db.execute("SELECT * FROM clients WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(zip(['chat_id', 'theme', 'post_count', 'style', 'channel_id', 'subscription_end', 'subscription_plan', 'language'], row))
            return None

async def save_post_result(chat_id, title, content, hashtags, file_id, image_prompt, message_id):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        await db.execute("""
            INSERT INTO posts (chat_id, title, content, hashtags, file_id, image_prompt, message_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, title, content, hashtags, file_id, image_prompt, message_id, datetime.now(timezone.utc).isoformat()))
        await db.commit()

async def get_pending_posts():
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        async with db.execute("""
            SELECT c.chat_id, s.post_id, s.channel_id, s.publish_datetime, p.message_id
            FROM schedule s
            JOIN clients c ON s.chat_id = c.chat_id
            JOIN posts p ON s.post_id = p.post_id
            WHERE s.publish_datetime <= ?
        """, (datetime.now(timezone.utc).isoformat(),)) as cursor:
            return await cursor.fetchall()

async def delete_schedule_entry(chat_id, post_id):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        await db.execute("DELETE FROM schedule WHERE chat_id = ? AND post_id = ?", (chat_id, post_id))
        await db.commit()

async def get_post_count_this_month(chat_id):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        first_day = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        async with db.execute("""
            SELECT COUNT(*) FROM posts
            WHERE chat_id = ? AND created_at >= ?
        """, (chat_id, first_day.isoformat())) as cursor:
            count = await cursor.fetchone()
            return count[0] if count else 0

async def save_schedule(chat_id, channel_id, post_id, publish_datetime):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        await db.execute("""
            INSERT INTO schedule (chat_id, post_id, channel_id, publish_datetime)
            VALUES (?, ?, ?, ?)
        """, (chat_id, post_id, channel_id, publish_datetime.isoformat()))
        await db.commit()

async def clean_old_posts(days=7):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        await db.execute("""
            DELETE FROM posts WHERE created_at < ?
        """, (cutoff.isoformat(),))
        await db.commit()
    logging.info(f"Cleaned posts older than {days} days")

async def save_usage_stat(chat_id, action, timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        await db.execute("""
            INSERT INTO usage_stats (chat_id, action, timestamp)
            VALUES (?, ?, ?)
        """, (chat_id, action, timestamp))
        await db.commit()

async def get_usage_stats(chat_id, days=30):
    async with aiosqlite.connect(DB_PATH, timeout=30.0) as db:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with db.execute("""
            SELECT action, COUNT(*), MAX(timestamp) FROM usage_stats
            WHERE chat_id = ? AND timestamp >= ?
            GROUP BY action
        """, (chat_id, cutoff.isoformat())) as cursor:
            return await cursor.fetchall()