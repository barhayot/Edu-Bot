# handlers/admin.py - Admin handlerlari

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import (
    admin_main_kb, admin_categories_kb, admin_category_actions_kb,
    admin_lessons_kb, admin_lesson_actions_kb, confirm_delete_kb, cancel_kb, main_menu_kb
)
from config import ADMIN_IDS, BOT_NAME

router = Router()


# Admin filteri
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============ FSM STATES ============

class AddCategory(StatesGroup):
    name = State()
    description = State()


class AddLesson(StatesGroup):
    category_id = State()
    title = State()
    description = State()
    file = State()


class BroadcastState(StatesGroup):
    message = State()


# ============ ADMIN ASOSIY MENYU ============

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\nNimani qilmoqchisiz?",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "🏠 Asosiy menyu")
async def to_main_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    from keyboards import main_menu_kb
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_kb())


# ============ KATEGORIYALAR ============

@router.message(F.text == "📁 Kategoriyalar")
async def list_categories(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    categories = await db.get_all_categories()
    if not categories:
        await message.answer(
            "📭 Kategoriyalar yo'q.\n➕ Kategoriya qo'shing!",
            reply_markup=admin_main_kb()
        )
        return
    
    await message.answer(
        f"📁 <b>Kategoriyalar</b> ({len(categories)} ta)\n\nKategoriyani tanlang:",
        reply_markup=admin_categories_kb(categories),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_category_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    cat_id = int(callback.data.split("_")[2])
    lessons_count = await db.count_lessons(cat_id)
    
    cats = await db.get_all_categories()
    cat = next((c for c in cats if c['id'] == cat_id), None)
    if not cat:
        await callback.answer("Kategoriya topilmadi!")
        return
    
    await callback.message.edit_text(
        f"📁 <b>{cat['name']}</b>\n"
        f"📝 {cat['description'] or 'Tavsif yo\\'q'}\n"
        f"🎬 Darslar soni: {lessons_count}\n\n"
        f"Nima qilmoqchisiz?",
        reply_markup=admin_category_actions_kb(cat_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_cats_back")
async def admin_cats_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    categories = await db.get_all_categories()
    await callback.message.edit_text(
        "📁 Kategoriyani tanlang:",
        reply_markup=admin_categories_kb(categories)
    )


# ============ KATEGORIYA QO'SHISH ============

@router.message(F.text == "➕ Kategoriya qo'sh")
async def start_add_category(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCategory.name)
    await message.answer(
        "📁 Yangi kategoriya nomi:\n(Masalan: Python kursi, Ingliz tili)",
        reply_markup=cancel_kb()
    )


@router.message(AddCategory.name)
async def get_category_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddCategory.description)
    await message.answer("📝 Kategoriya tavsifi (yoki /skip):")


@router.message(AddCategory.description)
async def get_category_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    data = await state.get_data()
    desc = "" if message.text == "/skip" else message.text
    
    result = await db.add_category(data['name'], desc)
    await state.clear()
    
    if result:
        await message.answer(
            f"✅ <b>{data['name']}</b> kategoriyasi qo'shildi!",
            reply_markup=admin_main_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Xatolik! Bunday nom allaqachon mavjud.",
            reply_markup=admin_main_kb()
        )


# ============ KATEGORIYANI O'CHIRISH ============

@router.callback_query(F.data.startswith("del_cat_"))
async def confirm_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        "⚠️ Kategoriyani o'chirsangiz, undagi <b>barcha darslar ham o'chadi</b>!\n\nDavom etasizmi?",
        reply_markup=confirm_delete_kb("cat", cat_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_del_cat_"))
async def do_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    cat_id = int(parts[3])
    await db.delete_category(cat_id)
    await callback.message.edit_text("✅ Kategoriya o'chirildi!")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Bekor qilindi.")


# ============ DARSLAR ============

@router.callback_query(F.data.startswith("admin_lessons_"))
async def admin_list_lessons(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    lessons = await db.get_lessons_by_category(cat_id)
    
    if not lessons:
        await callback.answer("📭 Bu kursda darslar yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🎬 <b>Darslar</b> ({len(lessons)} ta):",
        reply_markup=admin_lessons_kb(lessons, cat_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_lesson_"))
async def admin_lesson_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    lesson_id = int(callback.data.split("_")[2])
    lesson = await db.get_lesson(lesson_id)
    
    if not lesson:
        await callback.answer("Dars topilmadi!")
        return
    
    await callback.message.edit_text(
        f"🎬 <b>{lesson['title']}</b>\n"
        f"📝 {lesson['description'] or 'Tavsif yo\\'q'}\n"
        f"📁 Kurs: {lesson['category_name']}\n"
        f"📂 Tur: {lesson['file_type']}\n\n"
        f"Nima qilmoqchisiz?",
        reply_markup=admin_lesson_actions_kb(lesson_id, lesson['category_id']),
        parse_mode="HTML"
    )


# ============ DARS QO'SHISH ============

@router.callback_query(F.data.startswith("add_lesson_"))
async def start_add_lesson(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=cat_id)
    await state.set_state(AddLesson.title)
    await callback.message.answer(
        "🎬 Dars nomi:\n(Masalan: 1-dars: Python o'rnatish)",
        reply_markup=cancel_kb()
    )


@router.message(AddLesson.title)
async def get_lesson_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    await state.update_data(title=message.text)
    await state.set_state(AddLesson.description)
    await message.answer("📝 Dars tavsifi (yoki /skip yozing):")


@router.message(AddLesson.description)
async def get_lesson_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    desc = "" if message.text == "/skip" else message.text
    await state.update_data(description=desc)
    await state.set_state(AddLesson.file)
    await message.answer(
        "📹 Endi <b>video, hujjat yoki rasm</b> yuboring:\n\n"
        "⚠️ Video bo'lsa, to'g'ridan-to'g'ri yuklang (forward emas)!",
        parse_mode="HTML"
    )


@router.message(AddLesson.file)
async def get_lesson_file(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    file_id = None
    file_type = None
    
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    else:
        await message.answer("❌ Faqat video, hujjat yoki rasm yuboring!")
        return
    
    data = await state.get_data()
    await db.add_lesson(
        category_id=data['category_id'],
        title=data['title'],
        description=data.get('description', ''),
        file_id=file_id,
        file_type=file_type
    )
    await state.clear()
    
    await message.answer(
        f"✅ <b>{data['title']}</b> darsi qo'shildi!\n"
        f"📂 Tur: {file_type}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ============ DARSNI O'CHIRISH ============

@router.callback_query(F.data.startswith("del_lesson_"))
async def confirm_del_lesson(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    lesson_id = int(parts[2])
    cat_id = parts[3]
    await callback.message.edit_text(
        "⚠️ Bu darsni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_kb("lesson", lesson_id, cat_id)
    )


@router.callback_query(F.data.startswith("confirm_del_lesson_"))
async def do_del_lesson(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    lesson_id = int(parts[3])
    await db.delete_lesson(lesson_id)
    await callback.message.edit_text("✅ Dars o'chirildi!")


# ============ STATISTIKA ============

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_stats()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: {stats['users']}\n"
        f"📁 Kategoriyalar: {stats['categories']}\n"
        f"🎬 Darslar: {stats['lessons']}\n"
        f"👁 Jami ko'rishlar: {stats['views']}",
        parse_mode="HTML"
    )


# ============ FOYDALANUVCHILAR ============

@router.message(F.text == "👥 Foydalanuvchilar")
async def list_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    users = await db.get_all_users()
    if not users:
        await message.answer("👥 Foydalanuvchilar yo'q.")
        return
    
    text = f"👥 <b>Foydalanuvchilar</b> ({len(users)} ta):\n\n"
    for i, user in enumerate(users[:20], 1):
        status = "🚫" if user['is_blocked'] else "✅"
        name = user['full_name'] or "Noma'lum"
        username = f"@{user['username']}" if user['username'] else f"ID: {user['id']}"
        text += f"{i}. {status} {name} | {username}\n"
    
    if len(users) > 20:
        text += f"\n... va yana {len(users) - 20} ta"
    
    await message.answer(text, parse_mode="HTML")


# ============ XABAR YUBORISH (BROADCAST) ============

@router.message(F.text == "📢 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.message)
    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "(Matn, rasm yoki video bo'lishi mumkin)",
        reply_markup=cancel_kb()
    )


@router.message(BroadcastState.message)
async def do_broadcast(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_main_kb())
        return
    
    await state.clear()
    users = await db.get_all_users()
    
    sent = 0
    failed = 0
    
    for user in users:
        if user['is_blocked']:
            continue
        try:
            await message.copy_to(user['id'], protect_content=True)
            sent += 1
        except Exception:
            failed += 1
    
    await message.answer(
        f"📢 <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {sent}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )
