import os
import sqlite3
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

# --- 1. KEEP ALIVE (Защита от сна) ---
app = Flask('')
@app.route('/')
def home(): return "Бот NEWMAN$ активен!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()

# --- 2. НАСТРОЙКИ ---
BOT_TOKEN = "8817735126:AAFoJYpehYcoy4mYtLYvJXQsqtgInlNEIGA"
ADMIN_CHAT_ID = -1004361381034  # Твой чат админов

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- 3. БАЗА ДАННЫХ (Защита от обмана) ---
DB_PATH = "reports_db.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_photos (
            file_unique_id TEXT PRIMARY KEY,
            user_id INTEGER,
            nickname TEXT
        )
    """)
    conn.commit()
    conn.close()

def check_duplicate(file_unique_id, user_id, nickname):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, nickname FROM used_photos WHERE file_unique_id = ?", (file_unique_id,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return {"status": "exists", "user_id": result[0], "nickname": result[1]}
    
    cursor.execute("INSERT INTO used_photos (file_unique_id, user_id, nickname) VALUES (?, ?, ?)", 
                   (file_unique_id, user_id, nickname))
    conn.commit()
    conn.close()
    return {"status": "new"}

init_db()

# --- 4. РАНГИ И ЦЕНЫ ---
RANKS_INFO = {
    "2": {"title": "2 ранг", "req": "5.000.000$ (5кк) на счет семьи", "btn": "На 2 ранг (5кк)"},
    "3": {"title": "3 ранг", "req": "15.000.000$ (15кк) на счет семьи", "btn": "На 3 ранг (15кк)"},
    "4": {"title": "4 ранг", "req": "25.000.000$ (25кк) на счет семьи", "btn": "На 4 ранг (25кк)"},
    "5": {"title": "5 ранг", "req": "35.000.000$ (35кк) на счет семьи", "btn": "На 5 ранг (35кк)"},
    "6": {"title": "6 ранг", "req": "45.000.000$ (45кк) на счет семьи", "btn": "На 6 ранг (45кк)"},
    "7": {"title": "7 ранг", "req": "55.000.000$ (55кк) на счет семьи", "btn": "На 7 ранг (55кк)"},
    "8": {"title": "8 ранг (Зам)", "req": "Доверие, вклад в семью, помощь в развитии", "btn": "На 8 ранг (Зам) (За заслуги)"},
    "9": {"title": "9 ранг (Гл. Зам)", "req": "Максимальное доверие лидера и руководство", "btn": "На 9 ранг (Гл. Зам) (За заслуги)"}
}

class ReportStates(StatesGroup):
    waiting_nickname = State()
    waiting_rank = State()
    waiting_screen = State()

# Кнопки для админ-чата (содержат ID игрока, чтобы бот знал кому писать)
def get_admin_keyboard(user_id):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_approve_{user_id}"),
                types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_deny_{user_id}")
            ]
        ]
    )

# --- 5. УВЕДОМЛЕНИЕ О ЗАПУСКЕ ---
async def on_startup(bot: Bot):
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text="🚀 <b>Бот NEWMAN$ успешно запущен!</b>", parse_mode="HTML")

# --- 6. ЛОГИКА БОТА ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Подать отчет на повышение")]], resize_keyboard=True)
    await message.answer(f"Привет! Это бот для отчетов семьи <b>NEWMAN$</b>.", reply_markup=kb, parse_mode="HTML")

@dp.message(F.text == "Подать отчет на повышение")
async def start_report(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш игровой ник (Nick_Name):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ReportStates.waiting_nickname)

@dp.message(ReportStates.waiting_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    
    warning_text = (
        "⚠️⚠️⚠️ <b>ВНИМАНИЕ: ОЧЕНЬ ВАЖНО!</b> ⚠️⚠️⚠️\n\n"
        "📈 Повышения проходят строго <u><b>ПО ПОРЯДКУ</b></u>.\n"
        "❌ <b>ЗАПРЕЩЕНО</b> перескакивать ранги (например, с 1 сразу на 7).\n"
    )
    await message.answer(warning_text, parse_mode="HTML")
    
    # Кнопки с ценами прямо на них
    buttons = [[types.InlineKeyboardButton(text=v['btn'], callback_data=f"rank_{k}")] for k, v in RANKS_INFO.items()]
    await message.answer("Теперь выберите ранг, на который вы повышаетесь:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(ReportStates.waiting_rank)

@dp.callback_query(ReportStates.waiting_rank, F.data.startswith("rank_"))
async def process_rank(callback: types.CallbackQuery, state: FSMContext):
    rank_id = callback.data.split("_")[1]
    info = RANKS_INFO[rank_id]
    await state.update_data(rank_title=info['title'], rank_req=info['req'])
    await callback.message.delete()
    await callback.message.answer(
        f"Выбрано: <b>{info['title']}</b>\n💰 Стоимость: {info['req']}\n\n"
        "📸 Отправьте скриншот пополнения счета семьи с <b>/time</b>.", 
        parse_mode="HTML"
    )
    await state.set_state(ReportStates.waiting_screen)

@dp.message(ReportStates.waiting_screen, F.photo)
async def process_screen(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    data = await state.get_data()
    await state.clear()

    check = check_duplicate(photo.file_unique_id, message.from_user.id, data['nickname'])
    
    admin_warning = ""
    if check["status"] == "exists":
        admin_warning = f"🛑 <b>ОБМАН!</b> Скрин уже был у: {check['nickname']} (ID: {check['user_id']})\n\n"

    admin_text = (
        f"{admin_warning}📂 <b>ОТЧЕТ НА ПОВЫШЕНИЕ</b>\n\n"
        f"👤 Игрок: {data['nickname']}\n"
        f"🎖 Цель: {data['rank_title']}\n"
        f"💰 Оплата: {data['rank_req']}\n"
        f"🆔 TG ID: <code>{message.from_user.id}</code>"
    )
    
    # Отправляем админам С КНОПКАМИ одобрения/отклонения
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID, 
        photo=photo.file_id, 
        caption=admin_text, 
        reply_markup=get_admin_keyboard(message.from_user.id),
        parse_mode="HTML"
    )

    if check["status"] == "exists":
        await message.answer("⚠️ <b>У вас попытка обмана!</b> Вы скинули тот же скриншот, что кидали раньше. Отчет отклонен.", parse_mode="HTML")
    else:
        await message.answer("✅ <b>Ваш отчет успешно отправлен администрации!</b>", parse_mode="HTML")

# --- 7. ОБРАБОТКА РЕШЕНИЙ АДМИНИСТРАЦИИ ---
@dp.callback_query(F.data.startswith("adm_"))
async def handle_admin_choice(callback: types.CallbackQuery):
    # Разделяем данные кнопки
    data_parts = callback.data.split("_")
    action = data_parts[1]
    user_id = int(data_parts[2])
    
    if action == "approve":
        status_text = "🟢 ОДОБРЕН"
        user_msg = "🎉 <b>Отличные новости!</b> Ваш отчет на повышение был одобрен. Зайдите в игру для получения ранга!"
    else:
        status_text = "🔴 ОТКЛОНЕН"
        user_msg = "❌ <b>Ваш отчет на повышение был отклонен.</b> Проверьте условия или свяжитесь с руководством семьи."

    # Обновляем отчет в админ-чате: пишем результат и убираем кнопки
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n<b>[РЕШЕНИЕ АДМИНА]:</b> {status_text}",
        reply_markup=None,
        parse_mode="HTML"
    )
    
    # Отправляем уведомление игроку в личку
    try:
        await bot.send_message(chat_id=user_id, text=user_msg, parse_mode="HTML")
    except Exception:
        pass  # На случай если игрок заблокировал бота
        
    await callback.answer()

if __name__ == "__main__":
    import asyncio
    dp.startup.register(on_startup)
    keep_alive() 
    async def main():
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    asyncio.run(main())
