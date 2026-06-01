import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

# =============== НАСТРОЙКА БОТА ===============
BOT_TOKEN = 8754167937:AAH_x6JJAT6KALu5KwntnTtKD_htXprb8zA
ACCOUNTS_FILE = "accounts.txt
# ==============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Функция для чтения токенов гостевых аккаунтов из файла
def load_guest_tokens():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        # Убираем лишние пробелы и пустые строки
        return [line.strip() for line in f if line.strip()]

# Функция отправки лайка на сервер Garena Free Fire
async def send_freefire_like(session, target_uid, account_token):
    # Официальный эндпоинт игрового сервера для отправки лайков (взаимодействий)
    url = "https://client.ggame.garena.com/account/like" 
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {account_token}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; Garena Free Fire)"
    }
    
    payload = {
        "target_uid": int(target_uid),
        "source": 1 # Тип лайка (после матча или из профиля)
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                # Проверяем ответ сервера (структура зависит от текущей версии протокола Garena)
                if data.get("status") == 0 or data.get("message") == "SUCCESS":
                    return True
            return False
    except Exception:
        return False

@dp.message(CommandStart())
async def cmd_start(message: Message):
    tokens = load_guest_tokens()
    await message.answer(
        f"👋 **Привет! Я автономный бот для лайков Free Fire.**\n\n"
        f"В моей базе сейчас аккаунтов для накрутки: `{len(tokens)}` шт.\n\n"
        f" Чтобы накрутить лайки, введи команду:\n"
        f"`/like [ваш_UID]`",
        parse_mode="Markdown"
    )

@dp.message(Command("like"))
async def process_like(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи UID! Пример: `/like 123456789`")
        return
        
    target_uid = args[1]
    if not target_uid.isdigit():
        await message.answer("❌ UID должен состоять только из цифр!")
        return

    tokens = load_guest_tokens()
    if not tokens:
        await message.answer("❌ Ошибка: Файл `accounts.txt` пуст! Админ не загрузил токены аккаунтов.")
        return

    status_msg = await message.answer(f"⏳ Начинаю накрутку на UID `{target_uid}`...\nИспользую {len(tokens)} аккаунтов.", parse_mode="Markdown")
    
    success_count = 0
    
    # Открываем одну сессию для быстрой отправки пакетов
    async with aiohttp.ClientSession() as session:
        for i, token in enumerate(tokens):
            # Отправляем лайк
            is_success = await send_freefire_like(session, target_uid, token)
            if is_success:
                success_count += 1
            
            # Делаем микро-паузу 0.2 сек, чтобы сервера игры не заблокировали запросы за спам
            await asyncio.sleep(0.2)
            
            # Обновляем статус в чате каждые 10 аккаунтов, чтобы пользователь видел прогресс
            if i % 10 == 0 and i > 0:
                await status_msg.edit_text(f"⏳ Прогресс: обработано {i}/{len(tokens)} аккаунтов...")

    await status_msg.edit_text(
        f"✅ **Накрутка завершена!**\n\n"
        f"🎯 Цель: `{target_uid}`\n"
        f"🚀 Успешно отправлено лайков: `{success_count}` из `{len(tokens)}`", 
        parse_mode="Markdown"
    )

async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
      
