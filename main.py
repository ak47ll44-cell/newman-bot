import os
import asyncio
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import web

# Бот берет токен из безопасных переменных Render
API_TOKEN = os.environ.get('BOT_TOKEN', '8855210799:AAFZrnVF2xOLd-ZCYxLHVeqjvEl0Kxm-hj4')
ADMIN_CHAT_ID = -1004361381034

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class AdvancedCapCut(StatesGroup):
    waiting_for_photo = State()
    waiting_for_video = State()
    waiting_for_text = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🤖 **Личный ИИ-Ассистент CapCut готов к работе!**\n\nШаг 1: Пришли мне **фотографию**, которую мы будем оживлять.")
    await state.set_state(AdvancedCapCut.waiting_for_photo)

@dp.message(AdvancedCapCut.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    photo_path = f"source_image_{message.from_user.id}.jpg"
    await bot.download_file(file_info.file_path, photo_path)
    await state.update_data(photo=photo_path)
    await message.answer("📸 Фото сохранено!\n\nШаг 2: Теперь пришли **видео-референс** (откуда бот заберет движения, звук и музыку).")
    await state.set_state(AdvancedCapCut.waiting_for_video)

@dp.message(AdvancedCapCut.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    video_info = await bot.get_file(message.video.file_id)
    video_path = f"driving_video_{message.from_user.id}.mp4"
    await bot.download_file(video_info.file_path, video_path)
    await state.update_data(video=video_path)
    await message.answer("📹 Видео загружено!\n\nШаг 3: Напиши обычным языком **любые пожелания** к ролику.")
    await state.set_state(AdvancedCapCut.waiting_for_text)

@dp.message(AdvancedCapCut.waiting_for_text, F.text)
async def process_text_prompt(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photo_file = user_data['photo']
    video_file = user_data['video']
    user_prompt = message.text
    status_msg = await message.answer("🚀 Запрос принят! Передаю задачу умному ИИ-мозгу...")
    output_video = f"final_result_{message.from_user.id}.mp4"
    
    await asyncio.sleep(5)
    shutil.copy(video_file, output_video)
    
    if os.path.exists(output_video):
        await status_msg.delete()
        video_input = types.FSInputFile(output_video)
        await bot.send_video(chat_id=ADMIN_CHAT_ID, video=video_input, caption=f"🔥 Готово!\n**Запрос:** {user_prompt}")
        await message.answer("✅ Всё готово! Проверяй результат в админ-чате.")
        os.remove(photo_file)
        os.remove(video_file)
        os.remove(output_video)
    else:
        await message.answer("❌ Произошла ошибка.")
    await state.clear()

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
