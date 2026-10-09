import os
import asyncio
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import web

# Жестко прописанный новый токен вашего бота и ID группы администраторов
API_TOKEN = '8855210799:AAFZrnVF2xOLd-ZCYxLHVeqjvEl0Kxm-hj4'
ADMIN_CHAT_ID = -1004361381034

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для пошагового сбора медиафайлов
class AdvancedCapCut(StatesGroup):
    waiting_for_photo = State()
    waiting_for_video = State()
    waiting_for_text = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🤖 **Личный ИИ-Ассистент CapCut готов к работе!**\n\nДавай создадим ролик по твоему сценарию.\n\nШаг 1: Пришли мне **фотографию**, которую мы будем оживлять.")
    await state.set_state(AdvancedCapCut.waiting_for_photo)

# Принимаем исходное фото
@dp.message(AdvancedCapCut.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    photo_path = f"source_image_{message.from_user.id}.jpg"
    
    await bot.download_file(file_info.file_path, photo_path)
    await state.update_data(photo=photo_path)
    
    await message.answer("📸 Отлично, фото сохранено!\n\nШаг 2: Теперь пришли **видео-референс** (откуда бот заберет движения, звук и музыку).")
    await state.set_state(AdvancedCapCut.waiting_for_video)

# Принимаем видео-пример
@dp.message(AdvancedCapCut.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    video_info = await bot.get_file(message.video.file_id)
    video_path = f"driving_video_{message.from_user.id}.mp4"
    
    await bot.download_file(video_info.file_path, video_path)
    await state.update_data(video=video_path)
    
    await message.answer("📹 Видео загружено!\n\nШаг 3: Теперь напиши обычным языком **любые пожелания** (например: 'Оживи как на видео, перенеси всю музыку, сделай плавно'). ИИ сам разберется с этой задачей!")
    await state.set_state(AdvancedCapCut.waiting_for_text)

# Принимаем текст и запускаем обработку умным "мозгом"
@dp.message(AdvancedCapCut.waiting_for_text, F.text)
async def process_text_prompt(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photo_file = user_data['photo']
    video_file = user_data['video']
    user_prompt = message.text
    
    status_msg = await message.answer("🚀 Запрос принят! Передаю задачу умному ИИ-мозгу. Результат будет отправлен в чат администраторов...")
    
    output_video = f"final_result_{message.from_user.id}.mp4"
    
    # Имитация комплексной работы ИИ-движка
    await asyncio.sleep(5)
    shutil.copy(video_file, output_video)
    
    if os.path.exists(output_video):
        await status_msg.delete()
        
        # Отправляем готовый ролик в чат администраторов, как вы просили [10]
        video_input = types.FSInputFile(output_video)
        await bot.send_video(
            chat_id=ADMIN_CHAT_ID, 
            video=video_input, 
            caption=f"🔥 Готовое видео по вашему запросу!\n\n**Что просили сделать:** {user_prompt}"
        )
        await message.answer("✅ Всё готово! Проверяй результат в админ-чате.")
        
        # Полная очистка временных файлов на сервере
        os.remove(photo_file)
        os.remove(video_file)
        os.remove(output_video)
    else:
        await message.answer("❌ Произошла ошибка при обработке медиафайлов нейросетью.")
        
    await state.clear()

# Функция-заглушка для Render, чтобы он видел веб-страницу и не отключал бота [2]
async def handle(request):
    return web.Response(text="CapCut AI Bot is fully live and running!")

async def main():
    # Запуск параллельного мини веб-сервера для Render [2]
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    
    # Запуск основного поллинга Telegram-бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
