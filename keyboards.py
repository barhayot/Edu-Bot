# keyboards.py - Barcha tugmalar

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ============ USER KLAVIATURALAR ============

def main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📚 Darslar"),
        KeyboardButton(text="ℹ️ Ma'lumot"),
    )
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"📁 {cat['name']}",
            callback_data=f"cat_{cat['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def lessons_kb(lessons, category_id):
    builder = InlineKeyboardBuilder()
    for i, lesson in enumerate(lessons, 1):
        builder.button(
            text=f"🎬 {i}. {lesson['title']}",
            callback_data=f"lesson_{lesson['id']}"
        )
    builder.button(text="◀️ Orqaga", callback_data="back_categories")
    builder.adjust(1)
    return builder.as_markup()


def lesson_nav_kb(lesson_id, category_id, prev_id=None, next_id=None):
    builder = InlineKeyboardBuilder()
    nav_row = []
    if prev_id:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"lesson_{prev_id}"))
    if next_id:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"lesson_{next_id}"))
    if nav_row:
        builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="📋 Darslar ro'yxati", callback_data=f"cat_{category_id}"))
    return builder.as_markup()


# ============ ADMIN KLAVIATURALAR ============

def admin_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📁 Kategoriyalar"),
        KeyboardButton(text="➕ Kategoriya qo'sh"),
    )
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="👥 Foydalanuvchilar"),
    )
    builder.row(
        KeyboardButton(text="📢 Xabar yuborish"),
        KeyboardButton(text="🏠 Asosiy menyu"),
    )
    return builder.as_markup(resize_keyboard=True)


def admin_categories_kb(categories):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"📁 {cat['name']}",
            callback_data=f"admin_cat_{cat['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def admin_category_actions_kb(cat_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Dars qo'sh", callback_data=f"add_lesson_{cat_id}")
    builder.button(text="📋 Darslar", callback_data=f"admin_lessons_{cat_id}")
    builder.button(text="🗑 Kategoriyani o'chir", callback_data=f"del_cat_{cat_id}")
    builder.button(text="◀️ Orqaga", callback_data="admin_cats_back")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def admin_lessons_kb(lessons, cat_id):
    builder = InlineKeyboardBuilder()
    for i, lesson in enumerate(lessons, 1):
        builder.button(
            text=f"🎬 {i}. {lesson['title']}",
            callback_data=f"admin_lesson_{lesson['id']}"
        )
    builder.button(text="◀️ Orqaga", callback_data=f"admin_cat_{cat_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_lesson_actions_kb(lesson_id, cat_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"del_lesson_{lesson_id}_{cat_id}")
    builder.button(text="◀️ Orqaga", callback_data=f"admin_lessons_{cat_id}")
    builder.adjust(2)
    return builder.as_markup()


def confirm_delete_kb(item_type, item_id, extra=""):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"confirm_del_{item_type}_{item_id}_{extra}")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_delete")
    builder.adjust(2)
    return builder.as_markup()


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)
