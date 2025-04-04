#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
import random
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import traceback
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp
from langdetect import detect
from config import TELEGRAM_BOT_TOKEN, TEST_CHANNEL_ID, MAX_POST_LENGTH
from telegram_bot import send_telegram_post, send_telegram_message, edit_telegram_message, forward_telegram_post
from content_generator import OpenRouterAPI  # Используем OpenRouter вместо YandexGPTAPI
from image_processor import FLUX_API   # Используем FLUX_API для изображений
from database_manager import setup_database, save_client_settings, get_client_settings, save_post_result, get_pending_posts, delete_schedule_entry, get_post_count_this_month, save_schedule, clean_old_posts, save_usage_stat
from menus import translations, language_menu, get_main_menu, get_more_menu, get_style_menu, get_subscription_menu
from instructions import instructions
import aiosqlite

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

logger = logging.getLogger(__name__)

# Глобальные словари для отслеживания состояния пользователей
current_language = {}  # Текущий язык пользователя
awaiting_theme = {}    # Ожидаем ли ввода темы
awaiting_channel = {}  # Ожидаем ли ввода канала
awaiting_payment = {}  # Ожидаем ли оплаты
current_style = {}     # Текущий стиль постов
awaiting_generate = {} # Ожидаем ли команду /generate или ввода темы после неё
awaiting_feedback = {} # Ожидаем ли обратной связи
generate_image_flag = {} # Флаг генерации изображений (True/False)

class HistoricalBot:
    def __init__(self):
        self.content_generator = OpenRouterAPI()
        self.image_processor = FLUX_API()
        
        # Получаем токен и ID канала из переменных окружения
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not telegram_token or not telegram_chat_id:
            raise ValueError("Не заданы переменные окружения TELEGRAM_TOKEN или TELEGRAM_CHAT_ID")
        
        self.telegram_bot = TelegramBot(telegram_token, telegram_chat_id)
        
        # Темы для исторических постов
        self.topics = [
            "История России в 1990-х годах",
            "Средневековые цивилизации Европы",
            "Древний Египет и его правители",
            "История СССР",
            "Римская империя и ее расцвет",
            "Древняя Греция и ее наследие",
            "Викинги и их завоевания",
            "Первая мировая война",
            "Вторая мировая война",
            "Эпоха Возрождения",
            "Индустриальная революция",
            "Великие географические открытия",
            "Колонизация Америки",
            "Китайские династии",
            "Японский феодализм",
            "Монгольская империя",
            "Османская империя",
            "Ацтеки и майя",
            "Французская революция",
            "Наполеоновские войны",
            "Холодная война",
            "Гражданская война в России",
            "Русско-японская война",
            "Петр Великий и его реформы",
            "Екатерина Великая",
            "Иван Грозный и его эпоха"
        ]
    
    async def generate_and_post(self):
        """Генерирует и публикует исторический пост"""
        try:
            # Выбираем случайную тему
            topic = random.choice(self.topics)
            logger.info(f"Выбрана тема для поста: {topic}")
            
            # Генерируем контент
            title = await self.content_generator.generate_title(topic)
            if not title:
                logger.error("Не удалось сгенерировать заголовок")
                return False
            
            logger.info(f"Сгенерирован заголовок: {title}")
            
            content = await self.content_generator.generate_post_content(title, topic)
            if not content:
                logger.error("Не удалось сгенерировать содержание поста")
                return False
                
            logger.info(f"Сгенерирован текст поста длиной {len(content)} символов")
            
            # Генерируем промпт для изображения
            image_prompt = await self.content_generator.generate_image_prompt(title, content)
            if not image_prompt:
                logger.error("Не удалось сгенерировать промпт для изображения")
                # Используем заголовок как запасной вариант
                image_prompt = f"Historical scene: {title}, photorealistic style"
            
            logger.info(f"Сгенерирован промпт для изображения: {image_prompt}")
            
            # Создаем асинхронную сессию для запросов к API
            async with self.telegram_bot.create_session() as session:
                # Генерируем изображение
                image = await self.image_processor.generate_image(image_prompt, session)
                if not image:
                    logger.error("Не удалось сгенерировать изображение")
                    return False
                
                logger.info("Изображение успешно сгенерировано")
                
                # Формируем полный текст поста
                full_text = f"<b>{title}</b>\n\n{content}"
                
                # Отправляем пост в Telegram
                result = await self.telegram_bot.send_telegram_post(full_text, image, session)
                if result:
                    logger.info("Пост успешно отправлен в Telegram")
                    return True
                else:
                    logger.error("Не удалось отправить пост в Telegram")
                    return False
                
        except Exception as e:
            logger.error(f"Произошла ошибка при генерации и публикации поста: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def run_schedule(self, interval_hours=6):
        """Запускает бота по расписанию с заданным интервалом"""
        logger.info(f"Бот запущен. Интервал публикации: {interval_hours} часов")
        
        # Сначала публикуем пост сразу при запуске
        logger.info("Начинаем публикацию первого поста...")
        await self.generate_and_post()
        
        while True:
            # Вычисляем время следующей публикации
            next_post_time = datetime.now() + timedelta(hours=interval_hours)
            logger.info(f"Следующая публикация запланирована на: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Ждем до следующей публикации
            await asyncio.sleep(interval_hours * 3600)
            
            # Публикуем пост
            logger.info("Начинаем публикацию нового поста...")
            await self.generate_and_post()

    async def run_test(self):
        """Запускает тестовую публикацию один раз"""
        logger.info("Запускаем тестовую публикацию...")
        result = await self.generate_and_post()
        if result:
            logger.info("Тестовая публикация успешно выполнена")
        else:
            logger.error("Тестовая публикация не удалась")
        return result

    async def process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду от пользователя."""
        user_id = update.effective_user.id
        command = context.args[0] if context.args else update.message.text
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        logger.info(f"Получена команда: {command} от пользователя {user_id}")
        
        # Проверяем, что команда от авторизованного пользователя
        if telegram_chat_id and str(user_id) != telegram_chat_id:
            logger.warning(f"Попытка несанкционированного доступа от пользователя {user_id}")
            await update.message.reply_text("Вы не авторизованы для управления ботом.")
            return
        
        # Получаем имя команды
        command_name = update.message.text.split()[0]
            
        if command_name == "/start":
            await update.message.reply_text(
                "Привет! Я бот для генерации исторических постов. Используйте команды:\n"
                "/post - опубликовать один пост\n"
                "/status - проверить статус бота"
            )
        elif command_name == "/post":
            await update.message.reply_text("Начинаю генерацию и публикацию поста...")
            success = await self.generate_and_post()
            if success:
                await update.message.reply_text("Пост успешно опубликован!")
            else:
                await update.message.reply_text("Не удалось опубликовать пост. Проверьте логи.")
        elif command_name == "/status":
            await update.message.reply_text("Бот работает нормально и готов к генерации постов.")
        else:
            await update.message.reply_text("Неизвестная команда. Используйте /start для получения списка команд.")

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')
        
    def log_message(self, format, *args):
        # Отключаем логирование HTTP-запросов
        return

def start_webserver():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    logger.info(f"Запуск веб-сервера на порту {port}")
    server.serve_forever()

async def check_subscription(chat_id):
    """Проверяет статус подписки пользователя."""
    настройки = await get_client_settings(chat_id)
    количество_постов = await get_post_count_this_month(chat_id)
    if not настройки or not настройки.get("subscription_end"):
        return "бесплатно", количество_постов  # Нет подписки
    конец_подписки = datetime.fromisoformat(настройки["subscription_end"])
    if конец_подписки < datetime.now(timezone.utc):
        return "истекла", количество_постов  # Подписка истекла
    return настройки.get("subscription_plan", "бесплатно"), количество_постов  # Активная подписка

async def check_admin_rights(bot_token, channel_id, session):
    """Проверяет, является ли бот администратором в канале."""
    url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
    bot_info_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    async with session.get(bot_info_url) as bot_response:
        данные_бота = await bot_response.json()
        id_бота = данные_бота["result"]["id"]
    payload = {"chat_id": channel_id, "user_id": id_бота}
    async with session.post(url, json=payload) as response:
        данные = await response.json()
        return данные.get("ok") and данные["result"]["status"] in ["administrator", "creator"]

async def check_channel_exists(channel_id, session):
    """Проверяет, существует ли канал с указанным ID."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChat"
    payload = {"chat_id": channel_id}
    async with session.post(url, json=payload) as response:
        данные = await response.json()
        return данные.get("ok")

async def check_schedule(bot_token, session):
    """Проверяет расписание и отправляет запланированные посты."""
    try:
        ожидающие_посты = await get_pending_posts()
        for пост in ожидающие_посты:
            chat_id, post_id, channel_id, дата_публикации, message_id = пост
            if await forward_telegram_post(from_chat_id=TEST_CHANNEL_ID, message_id=message_id, to_chat_id=channel_id, session=session):
                await delete_schedule_entry(chat_id, post_id)
                await save_usage_stat(chat_id, "пост_опубликован")
                await asyncio.sleep(0.1)  # Небольшая задержка
    except Exception as e:
        logging.error(f"Ошибка проверки расписания: {e}")
        await asyncio.sleep(5)  # Задержка при ошибке

async def generate_post(open_router_api, flux_api, заголовок, тема, стиль, chat_id, план_подписки, язык, генерация_изображения, session=None):
    """Генерирует пост (текст и, при необходимости, изображение)."""
    try:
        logging.info(f"Генерация поста на языке: {язык}")
        контент, хэштеги = await open_router_api.generate_post_content(заголовок, тема, стиль, MAX_POST_LENGTH, language=язык, session=session)
        if not контент or not хэштеги:
            logging.error(f"Не удалось сгенерировать контент или хэштеги для '{заголовок}'")
            return None, None, None, None, None

        if генерация_изображения:  # Если нужно изображение
            промпт_изображения = await open_router_api.generate_image_prompt(заголовок, тема, language=язык, session=session)
            if промпт_изображения:
                данные_изображения = await flux_api.generate_image(промпт_изображения, session=session)
            else:
                данные_изображения = None
                промпт_изображения = None
            message_id, file_id = await send_telegram_post(TEST_CHANNEL_ID, f"{заголовок}\n\n{контент}\n\n{хэштеги}", image_data=данные_изображения, session=session)
        else:  # Без изображения
            промпт_изображения = None
            message_id, file_id = await send_telegram_post(TEST_CHANNEL_ID, f"{заголовок}\n\n{контент}\n\n{хэштеги}", session=session)

        if message_id:
            await save_post_result(chat_id, заголовок, контент, хэштеги, file_id, промпт_изображения, message_id)
            await save_usage_stat(chat_id, "пост_сгенерирован")
            await asyncio.sleep(0.1)
        return контент, хэштеги, file_id, промпт_изображения, message_id
    except Exception as e:
        logging.error(f"Ошибка генерации поста '{заголовок}': {e}")
        return None, None, None, None, None

async def handle_updates(open_router_api, flux_api):
    """Основной цикл обработки обновлений от Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    смещение = 0
    await setup_database()
    последнее_проверка = None

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                сейчас = datetime.now(timezone.utc)
                if not последнее_проверка or (сейчас - последнее_проверка > timedelta(minutes=5)):
                    await check_schedule(TELEGRAM_BOT_TOKEN, session)
                    последнее_проверка = сейчас

                async with session.get(url, params={"offset": смещение, "timeout": 30}) as response:
                    данные = await response.json()
                    if not данные.get("ok"):
                        logging.error(f"Ошибка API Telegram: {данные}")
                        await asyncio.sleep(5)
                        continue

                    обновления = данные.get("result", [])
                    if not обновления:
                        await asyncio.sleep(1)
                        continue

                    for обновление in обновления:
                        смещение = обновление["update_id"] + 1
                        chat_id = обновление.get("message", {}).get("chat", {}).get("id") or обновление.get("callback_query", {}).get("message", {}).get("chat", {}).get("id")
                        if not chat_id:
                            continue

                        текст = обновление.get("message", {}).get("text", "").strip()
                        данные_коллбэка = обновление.get("callback_query", {}).get("data")
                        язык = current_language.get(chat_id, "en")
                        главное_меню = get_main_menu(язык)
                        план_подписки, количество_постов = await check_subscription(chat_id)

                        logging.info(f"Получено обновление: chat_id={chat_id}, текст={текст}, коллбэк={данные_коллбэка}, язык={язык}")

                        if текст == "/start":
                            current_language[chat_id] = "en"  # Язык по умолчанию
                            awaiting_theme.pop(chat_id, None)
                            awaiting_generate.pop(chat_id, None)
                            awaiting_channel.pop(chat_id, None)
                            awaiting_payment.pop(chat_id, None)
                            generate_image_flag[chat_id] = True
                            await send_telegram_message(chat_id, translations["en"]["welcome"], get_main_menu("en"), session)
                            await asyncio.sleep(0.1)
                            continue

                        if текст == "/help":
                            await send_telegram_message(chat_id, instructions[язык]["full_instruction"], главное_меню, session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "more":
                            await send_telegram_message(chat_id, "Больше крутых функций! 👇", get_more_menu(язык), session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "back_to_main":
                            awaiting_theme.pop(chat_id, None)
                            awaiting_generate.pop(chat_id, None)
                            awaiting_channel.pop(chat_id, None)
                            await send_telegram_message(chat_id, translations[язык]["main_menu"], главное_меню, session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "language":
                            await send_telegram_message(chat_id, translations[язык]["language_prompt"], language_menu, session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка and данные_коллбэка.startswith("lang_"):
                            язык = данные_коллбэка.split("_")[1]
                            current_language[chat_id] = язык
                            awaiting_theme.pop(chat_id, None)
                            awaiting_generate.pop(chat_id, None)
                            awaiting_channel.pop(chat_id, None)
                            await send_telegram_message(chat_id, translations[язык]["welcome"], get_main_menu(язык), session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "about":
                            await send_telegram_message(chat_id, instructions[язык]["full_instruction"], главное_меню, session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "settheme" or текст == "/settheme":
                            awaiting_theme[chat_id] = True
                            logging.info(f"Установлено awaiting_theme[{chat_id}] = True")
                            await send_telegram_message(chat_id, translations[язык]["theme_prompt"], главное_меню, session)
                            await asyncio.sleep(0.1)
                            continue

                        if chat_id in awaiting_theme and текст and текст != "/settheme":
                            logging.info(f"Обработка темы: {текст} для chat_id={chat_id}")
                            try:
                                части = текст.split("#", 1)
                                if len(части) != 2:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                try:
                                    количество_постов = int(части[0].strip())
                                except ValueError:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                тема = части[1].strip()
                                if количество_постов <= 0 or not тема:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                
                                # Определяем язык темы с помощью langdetect
                                try:
                                    язык_темы = detect(тема)
                                    logging.info(f"Определен язык темы для генерации: {язык_темы}")
                                    # Используем язык темы, если он поддерживается, иначе текущий язык пользователя
                                    язык_поста = язык_темы if язык_темы in ["ru", "en"] else язык
                                except Exception as e:
                                    logging.error(f"Ошибка при определении языка: {e}")
                                    язык_поста = язык  # Используем текущий язык пользователя как запасной вариант
                                
                                стиль = current_style.get(chat_id, "expert")
                                await save_client_settings(chat_id, theme=тема, post_count=количество_постов, language=язык_поста)
                                await save_usage_stat(chat_id, "тема_установлена")
                                await send_telegram_message(chat_id, translations[язык]["theme_saved"].format(theme=тема, post_count=количество_постов), главное_меню, session)
                                del awaiting_theme[chat_id]
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                logging.error(f"Ошибка обработки темы: {e}")
                                await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "setstyle" or текст == "/setstyle":
                            if план_подписки == "standard":
                                current_style[chat_id] = "expert"
                                await send_telegram_message(chat_id, translations[язык]["style_limited"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            else:
                                await send_telegram_message(chat_id, translations[язык]["style_prompt"], get_style_menu(язык), session)
                                await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка and данные_коллбэка.startswith("style_"):
                            стиль = данные_коллбэка.split("_")[1]
                            if план_подписки == "standard" and стиль != "expert":
                                await send_telegram_message(chat_id, translations[язык]["style_limited"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            else:
                                current_style[chat_id] = стиль
                                await save_usage_stat(chat_id, f"стиль_установлен_{стиль}")
                                await send_telegram_message(chat_id, f"Стиль '{стиль}' установлен!", главное_меню, session)
                                await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "setchannel" or текст == "/setchannel":
                            awaiting_channel[chat_id] = True
                            await send_telegram_message(chat_id, translations[язык]["channel_prompt"].format(channel="ВашКанал"), главное_меню, session)
                            await asyncio.sleep(0.1)
                            continue

                        if chat_id in awaiting_channel and текст and текст != "/setchannel":
                            channel_id = текст.strip()
                            if not channel_id.startswith("@"):
                                await send_telegram_message(chat_id, translations[язык]["channel_error"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            else:
                                if not await check_channel_exists(channel_id, session):
                                    await send_telegram_message(chat_id, translations[язык]["channel_not_found"].format(channel=channel_id), главное_меню, session)
                                    await asyncio.sleep(0.1)
                                elif await check_admin_rights(TELEGRAM_BOT_TOKEN, channel_id, session):
                                    await save_client_settings(chat_id, channel_id=channel_id)
                                    await save_usage_stat(chat_id, "канал_установлен")
                                    await send_telegram_message(chat_id, translations[язык]["channel_saved"].format(channel=channel_id), главное_меню, session)
                                    del awaiting_channel[chat_id]
                                    await asyncio.sleep(0.1)
                                else:
                                    ссылка_канала = f"tg://resolve?domain={channel_id[1:]}"
                                    подсказка = (
                                        translations[язык]["channel_no_admin"].format(channel=channel_id) + "\n\n"
                                        f"Перейдите в [{channel_id}]({ссылка_канала}), выберите 'Администраторы' > 'Добавить', и добавьте меня!"
                                    )
                                    await send_telegram_message(chat_id, подсказка, главное_меню, session)
                                    await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "subscribe" or текст == "/subscribe":
                            await send_telegram_message(chat_id, translations[язык]["subscribe_prompt"], get_subscription_menu(язык), session)
                            await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "generate" or текст == "/generate":
                            generate_image_flag[chat_id] = True
                            настройки = await get_client_settings(chat_id)
                            if not настройки or not настройки["theme"] or not настройки["post_count"]:
                                awaiting_generate[chat_id] = True
                                await send_telegram_message(chat_id, translations[язык]["theme_prompt"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            else:
                                стиль = current_style.get(chat_id, "expert")
                                количество_постов = настройки["post_count"]
                                тема = настройки["theme"]
                                язык_поста = настройки.get("language", язык)
                                logging.info(f"Генерация постов на языке: {язык_поста}")
                                message_id = await send_telegram_message(chat_id, translations[язык]["generating"].format(i=1, post_count=количество_постов, progress=0), главное_меню, session)
                                заголовки = await open_router_api.generate_titles(тема, количество_постов, language=язык_поста, session=session)
                                if not заголовки:
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["titles_error"], главное_меню, session)
                                    awaiting_generate.pop(chat_id, None)
                                    await asyncio.sleep(0.1)
                                    continue
                                список_заголовков = заголовки.split("\n")
                                for i, заголовок in enumerate(список_заголовков, 1):
                                    прогресс = (i / количество_постов) * 100
                                    logging.info(f"Генерация поста {i}/{количество_постов} ({прогресс:.1f}%): '{заголовок}' на языке {язык_поста}")
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["generating"].format(i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    контент, хэштеги, file_id, промпт_изображения, post_message_id = await generate_post(open_router_api, flux_api, заголовок, тема, стиль, chat_id, план_подписки, язык_поста, True, session=session)
                                    if контент is None or хэштеги is None:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                        continue
                                    if post_message_id:
                                        await save_post_result(chat_id, заголовок, контент, хэштеги, file_id, промпт_изображения, post_message_id)
                                        await save_usage_stat(chat_id, "пост_сгенерирован")
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_done"].format(title=заголовок, i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    else:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                    await asyncio.sleep(0.1)
                                await edit_telegram_message(chat_id, message_id, translations[язык]["generation_complete"], главное_меню, session)
                                awaiting_generate.pop(chat_id, None)
                                awaiting_theme.pop(chat_id, None)
                                awaiting_channel.pop(chat_id, None)
                                await asyncio.sleep(0.1)
                            continue

                        if данные_коллбэка == "generate_text_only":
                            generate_image_flag[chat_id] = False
                            настройки = await get_client_settings(chat_id)
                            if not настройки or not настройки["theme"] or not настройки["post_count"]:
                                awaiting_generate[chat_id] = True
                                await send_telegram_message(chat_id, translations[язык]["theme_prompt"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            else:
                                стиль = current_style.get(chat_id, "expert")
                                количество_постов = настройки["post_count"]
                                тема = настройки["theme"]
                                язык_поста = настройки.get("language", язык)
                                logging.info(f"Генерация постов на языке: {язык_поста}")
                                message_id = await send_telegram_message(chat_id, translations[язык]["generating"].format(i=1, post_count=количество_постов, progress=0), главное_меню, session)
                                заголовки = await open_router_api.generate_titles(тема, количество_постов, language=язык_поста, session=session)
                                if not заголовки:
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["titles_error"], главное_меню, session)
                                    awaiting_generate.pop(chat_id, None)
                                    await asyncio.sleep(0.1)
                                    continue
                                список_заголовков = заголовки.split("\n")
                                for i, заголовок in enumerate(список_заголовков, 1):
                                    прогресс = (i / количество_постов) * 100
                                    logging.info(f"Генерация поста {i}/{количество_постов} ({прогресс:.1f}%): '{заголовок}' на языке {язык_поста}")
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["generating"].format(i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    контент, хэштеги, file_id, промпт_изображения, post_message_id = await generate_post(open_router_api, flux_api, заголовок, тема, стиль, chat_id, план_подписки, язык_поста, False, session=session)
                                    if контент is None or хэштеги is None:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                        continue
                                    if post_message_id:
                                        await save_post_result(chat_id, заголовок, контент, хэштеги, file_id, промпт_изображения, post_message_id)
                                        await save_usage_stat(chat_id, "пост_сгенерирован")
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_done"].format(title=заголовок, i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    else:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                    await asyncio.sleep(0.1)
                                await edit_telegram_message(chat_id, message_id, translations[язык]["generation_complete"], главное_меню, session)
                                awaiting_generate.pop(chat_id, None)
                                awaiting_theme.pop(chat_id, None)
                                awaiting_channel.pop(chat_id, None)
                                await asyncio.sleep(0.1)
                            continue

                        if chat_id in awaiting_generate and текст and текст != "/generate" and текст != "/generate_text_only":
                            try:
                                части = текст.split("#", 1)
                                if len(части) != 2:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                try:
                                    количество_постов = int(части[0].strip())
                                except ValueError:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                тема = части[1].strip()
                                if количество_постов <= 0 or not тема:
                                    await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                    await asyncio.sleep(0.1)
                                    continue
                                
                                # Определяем язык темы с помощью langdetect
                                try:
                                    язык_темы = detect(тема)
                                    logging.info(f"Определен язык темы для генерации: {язык_темы}")
                                    # Используем язык темы, если он поддерживается, иначе текущий язык пользователя
                                    язык_поста = язык_темы if язык_темы in ["ru", "en"] else язык
                                except Exception as e:
                                    logging.error(f"Ошибка при определении языка: {e}")
                                    язык_поста = язык  # Используем текущий язык пользователя как запасной вариант
                                
                                стиль = current_style.get(chat_id, "expert")
                                message_id = await send_telegram_message(chat_id, translations[язык]["generating"].format(i=1, post_count=количество_постов, progress=0), главное_меню, session)
                                заголовки = await open_router_api.generate_titles(тема, количество_постов, language=язык_поста, session=session)
                                if not заголовки:
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["titles_error"], главное_меню, session)
                                    awaiting_generate.pop(chat_id, None)
                                    await asyncio.sleep(0.1)
                                    continue
                                список_заголовков = заголовки.split("\n")
                                for i, заголовок in enumerate(список_заголовков, 1):
                                    прогресс = (i / количество_постов) * 100
                                    logging.info(f"Генерация поста {i}/{количество_постов} ({прогресс:.1f}%): '{заголовок}' на языке {язык_поста}")
                                    await edit_telegram_message(chat_id, message_id, translations[язык]["generating"].format(i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    контент, хэштеги, file_id, промпт_изображения, post_message_id = await generate_post(open_router_api, flux_api, заголовок, тема, стиль, chat_id, план_подписки, язык_поста, generate_image_flag.get(chat_id, True), session=session)
                                    if контент is None or хэштеги is None:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                        continue
                                    if post_message_id:
                                        await save_post_result(chat_id, заголовок, контент, хэштеги, file_id, промпт_изображения, post_message_id)
                                        await save_usage_stat(chat_id, "пост_сгенерирован")
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_done"].format(title=заголовок, i=i, post_count=количество_постов, progress=прогресс), главное_меню, session)
                                    else:
                                        await edit_telegram_message(chat_id, message_id, translations[язык]["post_error"].format(title=заголовок, progress=прогресс), главное_меню, session)
                                    await asyncio.sleep(0.1)
                                await edit_telegram_message(chat_id, message_id, translations[язык]["generation_complete"], главное_меню, session)
                                del awaiting_generate[chat_id]
                                awaiting_theme.pop(chat_id, None)
                                awaiting_channel.pop(chat_id, None)
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                logging.error(f"Ошибка обработки темы: {e}")
                                await send_telegram_message(chat_id, translations[язык]["theme_error"], главное_меню, session)
                                await asyncio.sleep(0.1)
                            continue

                        if текст.startswith("/setschedule"):
                            настройки = await get_client_settings(chat_id)
                            if not настройки or not настройки["channel_id"]:
                                await send_telegram_message(chat_id, translations[язык]["no_channel"], главное_меню, session)
                                await asyncio.sleep(0.1)
                                continue
                            if "\n" in текст:
                                части = текст.split("\n")
                                if len(части) != настройки["post_count"] + 2 or not части[1].startswith("@"):
                                    await send_telegram_message(chat_id, translations[язык]["schedule_format_error"].format(post_count=настройки["post_count"]), главное_меню, session)
                                    continue
                                channel_id = части[1].strip()
                                await save_client_settings(chat_id, channel_id=channel_id)
                                post_ids = []
                                try:
                                    async with aiosqlite.connect("telegram_bot_data.db", timeout=10) as db:
                                        async with db.execute("""
                                            SELECT post_id FROM posts
                                            WHERE chat_id = ?
                                            ORDER BY created_at DESC
                                            LIMIT ?
                                        """, (chat_id, настройки["post_count"])) as cursor:
                                            строки = await cursor.fetchall()
                                            post_ids = [строка[0] for строка in строки]
                                    for i, строка in enumerate(части[2:]):
                                        try:
                                            дата_публикации = datetime.strptime(строка.strip(), "%d.%m.%Y %H:%M").replace(tzinfo=timezone.utc)
                                            await save_schedule(chat_id, channel_id, post_ids[i], дата_публикации)
                                            await save_usage_stat(chat_id, "расписание_установлено")
                                            await asyncio.sleep(0.1)
                                        except ValueError:
                                            await send_telegram_message(chat_id, translations[язык]["schedule_date_error"].format(line=строка), главное_меню, session)
                                            await asyncio.sleep(0.1)
                                            break
                                    else:
                                        await send_telegram_message(chat_id, translations[язык]["schedule_saved"].format(channel_id=channel_id), главное_меню, session)
                                        await asyncio.sleep(0.1)
                                except Exception as e:
                                    logging.error(f"Ошибка в /setschedule: {e}")
                                    await send_telegram_message(chat_id, "Ошибка при сохранении расписания", главное_меню, session)
                                    await asyncio.sleep(0.1)
                            else:
                                await send_telegram_message(chat_id, translations[язык]["schedule_prompt"].format(post_count=настройки["post_count"]), главное_меню, session)
                                await asyncio.sleep(0.1)
                            continue

            except Exception as e:
                logging.error(f"Ошибка в обработке обновлений: {e}")
                await asyncio.sleep(5)

async def cleanup_task():
    """Задача для очистки старых записей из базы данных."""
    while True:
        try:
            await clean_old_posts(days=7)  # Удаляем посты старше 7 дней
            await asyncio.sleep(86400)  # 24 часа
        except Exception as e:
            logging.error(f"Ошибка в задаче очистки: {e}")
            await asyncio.sleep(3600)  # Задержка 1 час при ошибке

async def main():
    """Основная функция бота."""
    try:
        # Запускаем веб-сервер для Render.com в отдельном потоке
        threading.Thread(target=start_webserver, daemon=True).start()
        logger.info("Веб-сервер для Render.com запущен")
        
        await setup_database()  # Инициализация базы данных
        open_router_api = OpenRouterAPI()  # Создаем экземпляр OpenRouterAPI
        flux_api = FLUX_API()    # Создаем экземпляр FLUX_API
        задача_очистки = asyncio.create_task(cleanup_task())  # Запускаем очистку в фоне
        await handle_updates(open_router_api, flux_api)  # Основной цикл обновлений
    except Exception as e:
        logging.error(f"Критическая ошибка в main: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        logging.error(traceback.format_exc())