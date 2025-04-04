#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
import random
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from dotenv import load_dotenv
import traceback

from content_generator import ContentGenerator
from image_processor import FLUX_API
from telegram_bot import TelegramBot

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

class HistoricalBot:
    def __init__(self):
        self.content_generator = ContentGenerator()
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

async def main():
    # Проверяем наличие переменных окружения
    if not os.getenv("TELEGRAM_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logger.error("Не заданы переменные окружения TELEGRAM_TOKEN или TELEGRAM_CHAT_ID")
        logger.info("Вы можете создать файл .env с этими переменными или задать их напрямую в системе")
        return
    
    # Запускаем веб-сервер для Render.com в отдельном потоке
    threading.Thread(target=start_webserver, daemon=True).start()
    
    bot = HistoricalBot()
    
    # Проверяем режим запуска
    if os.getenv("RUN_MODE") == "test":
        # Тестовый режим - одна публикация
        await bot.run_test()
    else:
        # Стандартный режим - публикация по расписанию
        # Получаем интервал из переменной окружения или используем значение по умолчанию
        interval_hours = int(os.getenv("POST_INTERVAL_HOURS", "6"))
        await bot.run_schedule(interval_hours)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())