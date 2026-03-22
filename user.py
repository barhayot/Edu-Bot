# handlers/user.py - Foydalanuvchi handlerlari

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

import database as db
from keyboards import main_menu_kb, categories_kb, lessons_kb, lesson_nav_kb
from config import BOT_NAME, ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    
    # Foydalanuvchini ro'yxatdan o'tkazish
    await db.register_user(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name
    )
    
    # Bloklangan foydalanuvchini tekshirish
    if await db.is_user_blocked(user.id):
        await message.answer("❌ Siz bloklangansiz. Admin bilan bog'laning.")
        return
    
    # Admin uchun admin menyusiga yo'naltirish
    if user.id in ADMIN_IDS:
        from keyboards import admin_main_kb
        await message.answer(
            f"👨‍💼 Xush kelibsiz, Admin!\n\n"
            f"🏫 <b>{BOT_NAME}</b> boshqaruv paneliga xush kelibsiz.",
            reply_markup=admin_main_kb(),
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        f"🎓 <b>{BOT_NAME}</b> ga xush kelibsiz!\n\n"
        f"Bu yerda siz quyidagi imkoniyatlardan foydalanishingiz mumkin:\n"
        f"📚 Video darslar\n"
        f"📁 Turli xil kurslar\n\n"
        f"Boshlash uchun <b>📚 Darslar</b> tugmasini bosing!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📚 Darslar")
async def show_categories(message: Message):
    if await db.is_user_blocked(message.from_user.id):
        return
    
    categories = await db.get_all_categories()
    
    if not categories:
        await message.answer("📭 Hozircha darslar mavjud emas. Tez orada qo'shiladi!")
        return
    
    await message.answer(
        "📁 <b>Kurslar ro'yxati</b>\n\nQaysi kursni ko'rmoqchisiz?",
        reply_markup=categories_kb(categories),
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ Ma'lumot")
async def info(message: Message):
    await message.answer(
        f"🏫 <b>{BOT_NAME}</b>\n\n"
        f"📌 Bu bot orqali siz:\n"
        f"• Video darslarni ko'rishingiz\n"
        f"• Turli kurslarga kirish olishingiz\n"
        f"• O'z bilimingizni oshirishingiz mumkin\n\n"
        f"📞 Muammo bo'lsa admin bilan bog'laning.",
        parse_mode="HTML"
    )


# ============ KATEGORIYA CALLBACK ============

@router.callback_query(F.data.startswith("cat_"))
async def show_lessons(callback: CallbackQuery):
    if await db.is_user_blocked(callback.from_user.id):
        await callback.answer("❌ Siz bloklangansiz!", show_alert=True)
        return
    
    cat_id = int(callback.data.split("_")[1])
    lessons = await db.get_lessons_by_category(cat_id)
    
    if not lessons:
        await callback.answer("📭 Bu kursda hali darslar yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📋 <b>Darslar ro'yxati</b> ({len(lessons)} ta)\n\nDarsni tanlang:",
        reply_markup=lessons_kb(lessons, cat_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = await db.get_all_categories()
    await callback.message.edit_text(
        "📁 <b>Kurslar ro'yxati</b>\n\nQaysi kursni ko'rmoqchisiz?",
        reply_markup=categories_kb(categories),
        parse_mode="HTML"
    )


# ============ DARS CALLBACK ============

@router.callback_query(F.data.startswith("lesson_"))
async def show_lesson(callback: CallbackQuery):
    if await db.is_user_blocked(callback.from_user.id):
        await callback.answer("❌ Siz bloklangansiz!", show_alert=True)
        return
    
    lesson_id = int(callback.data.split("_")[1])
    lesson = await db.get_lesson(lesson_id)
    
    if not lesson:
        await callback.answer("❌ Dars topilmadi!", show_alert=True)
        return
    
    # Navbatdagi va oldingi darslarni topish
    all_lessons = await db.get_lessons_by_category(lesson["category_id"])
    lesson_ids = [l["id"] for l in all_lessons]
    current_idx = lesson_ids.index(lesson_id)
    
    prev_id = lesson_ids[current_idx - 1] if current_idx > 0 else None
    next_id = lesson_ids[current_idx + 1] if current_idx < len(lesson_ids) - 1 else None
    
    caption = (
        f"🎬 <b>{lesson['title']}</b>\n"
        f"📁 Kurs: {lesson['category_name']}\n"
        f"📌 Dars {current_idx + 1}/{len(lesson_ids)}\n"
    )
    if lesson['description']:
        caption += f"\n📝 {lesson['description']}"
    
    nav_kb = lesson_nav_kb(lesson_id, lesson["category_id"], prev_id, next_id)
    
    # Kirishni loglash
    await db.log_access(callback.from_user.id, lesson_id)
    
    # Avvalgi xabarni o'chirish
    await callback.message.delete()
    
    # Videoni protect_content=True bilan yuborish (forward taqiqi)
    if lesson['file_type'] == 'video':
        await callback.message.answer_video(
            video=lesson['file_id'],
            caption=caption,
            reply_markup=nav_kb,
            parse_mode="HTML",
            protect_content=True  # 🔒 Forward va saqlash taqiqi
        )
    elif lesson['file_type'] == 'document':
        await callback.message.answer_document(
            document=lesson['file_id'],
            caption=caption,
            reply_markup=nav_kb,
            parse_mode="HTML",
            protect_content=True
        )
    elif lesson['file_type'] == 'photo':
        await callback.message.answer_photo(
            photo=lesson['file_id'],
            caption=caption,
            reply_markup=nav_kb,
            parse_mode="HTML",
            protect_content=True
        )
    
    await callback.answer()
