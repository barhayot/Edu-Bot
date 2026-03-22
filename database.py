# database.py - SQLite ma'lumotlar bazasi

import aiosqlite
from config import DB_PATH


async def init_db():
    """Barcha jadvallarni yaratish"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Kategoriyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Darslar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_id TEXT NOT NULL,
                file_type TEXT DEFAULT 'video',
                order_num INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_blocked INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Kirish logi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                lesson_id INTEGER,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()


# ============ KATEGORIYALAR ============

async def get_all_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories ORDER BY id") as cursor:
            return await cursor.fetchall()


async def add_category(name: str, description: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                (name, description)
            )
            await db.commit()
            return True
        except Exception:
            return False


async def delete_category(cat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM lessons WHERE category_id = ?", (cat_id,))
        await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        await db.commit()


# ============ DARSLAR ============

async def get_lessons_by_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM lessons WHERE category_id = ? ORDER BY order_num, id",
            (category_id,)
        ) as cursor:
            return await cursor.fetchall()


async def get_lesson(lesson_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT l.*, c.name as category_name FROM lessons l "
            "JOIN categories c ON l.category_id = c.id WHERE l.id = ?",
            (lesson_id,)
        ) as cursor:
            return await cursor.fetchone()


async def add_lesson(category_id: int, title: str, description: str, file_id: str, file_type: str = "video"):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT MAX(order_num) FROM lessons WHERE category_id = ?",
            (category_id,)
        ) as cursor:
            row = await cursor.fetchone()
            order_num = (row[0] or 0) + 1
        
        await db.execute(
            "INSERT INTO lessons (category_id, title, description, file_id, file_type, order_num) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (category_id, title, description, file_id, file_type, order_num)
        )
        await db.commit()
        return True


async def delete_lesson(lesson_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        await db.commit()


async def count_lessons(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM lessons WHERE category_id = ?", (category_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]


# ============ FOYDALANUVCHILAR ============

async def register_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        await db.execute("""
            UPDATE users SET username = ?, full_name = ? WHERE id = ?
        """, (username, full_name, user_id))
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as cursor:
            return await cursor.fetchall()


async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def is_user_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_blocked FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] == 1 if row else False


async def block_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 1 WHERE id = ?", (user_id,))
        await db.commit()


async def unblock_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 0 WHERE id = ?", (user_id,))
        await db.commit()


async def log_access(user_id: int, lesson_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO access_log (user_id, lesson_id) VALUES (?, ?)",
            (user_id, lesson_id)
        )
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM categories") as c:
            cats = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM lessons") as c:
            lessons = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM access_log") as c:
            views = (await c.fetchone())[0]
    return {"users": users, "categories": cats, "lessons": lessons, "views": views}
