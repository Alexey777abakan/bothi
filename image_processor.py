# image_processor.py
import aiohttp
import asyncio
import logging
import base64
import io
import time
import json
import socket
import os
from random import randint
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def check_internet_connection():
    """Проверяет подключение к интернету, пытаясь подключиться к Google."""
    try:
        # Проверяем соединение с Google
        socket.create_connection(("www.google.com", 80), 3)
        return True
    except OSError:
        logging.error("Проблема с интернет-подключением. Проверьте ваше соединение.")
        return False

async def create_local_test_image(prompt, session=None):
    """Создает локальное тестовое изображение, если API недоступно."""
    try:
        logging.info(f"Создание локального тестового изображения для промпта: {prompt[:50]}...")
        
        # Создаем изображение
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            # Если шрифт не найден, используем стандартный
            font = None
        
        # Показываем часть промпта и поясняющий текст
        prompt_short = prompt[:150] + "..." if len(prompt) > 150 else prompt
        text = f"Тестовое изображение\n\nПромпт:\n{prompt_short}\n\nAPI fal.ai недоступно"
        
        d.text((width//2, height//2), text, 
               fill=(255, 255, 255), font=font, anchor="mm", align="center")
        
        # Добавляем рамку
        for i in range(3):
            d.rectangle([i, i, width-i-1, height-i-1], outline=(255, 255, 255))
        
        # Сохраняем
        filename = f"test_image_local_{int(time.time())}.jpg"
        img.save(filename)
        
        logging.info(f"Локальное тестовое изображение сохранено в файл: {filename}")
        
        # Возвращаем байтовый поток с изображением
        bytesio = io.BytesIO()
        img.save(bytesio, format='JPEG')
        bytesio.seek(0)
        
        return bytesio
    except Exception as e:
        logging.error(f"Ошибка создания локального тестового изображения: {e}")
        import traceback
        logging.error(f"Трассировка: {traceback.format_exc()}")
        return None

class FLUX_API:
    def __init__(self):
        # Получаем API ключ из переменных окружения
        self.API_KEY = os.getenv("FLUX_API_KEY", "")
        if not self.API_KEY:
            logging.warning("FLUX_API_KEY не найден в переменных окружения. API может не работать.")
            
        # Основной URL
        self.URL = "https://api.fal.ai/v1/models/fal-ai/flux-pro/v1.1-ultra/images"
        # Альтернативный URL, если основной не работает
        self.ALT_URL = "https://110011.fal.ai/v1/models/fal-ai/flux-pro/v1.1-ultra/images"
        self.headers = {
            "Authorization": f"Key {self.API_KEY}",
            "Content-Type": "application/json"
        }
        # Флаг, указывающий, что API недоступно
        self.api_unavailable = False

    async def generate_image(self, prompt, session=None):
        """Генерирует изображение через fal.ai FLUX API."""
        # Если мы уже знаем, что API недоступно, сразу создаем локальное изображение
        if self.api_unavailable:
            logging.warning("Предыдущие попытки показали, что API недоступно. Создаем локальное изображение.")
            return await create_local_test_image(prompt, session)
            
        # Проверяем интернет
        if not check_internet_connection():
            logging.error("Отсутствует подключение к интернету. Генерация изображения невозможна.")
            return await create_local_test_image(prompt, session)
            
        logging.info(f"Генерация изображения FLUX, длина промпта={len(prompt)}")
        data = {
            "prompt": prompt,
            "num_images": 1,
            "enable_safety_checker": True, 
            "safety_tolerance": "2",
            "output_format": "jpeg",
            "aspect_ratio": "1:1"
        }
        
        # Создаем сессию, если нужно
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            for attempt in range(3):  # Делаем 3 попытки
                try:
                    logging.info(f"Отправка запроса на генерацию FLUX изображения (попытка {attempt + 1})")
                    
                    # Основной URL
                    result = await self._try_request(session, self.URL, data, attempt)
                    if result:
                        return result
                    
                    # Альтернативный URL, если основной не сработал
                    result = await self._try_request(session, self.ALT_URL, data, attempt)
                    if result:
                        return result
                    
                    await asyncio.sleep(2 * (attempt + 1))
                    
                except Exception as e:
                    logging.error(f"Ошибка генерации FLUX изображения (попытка {attempt + 1}): {e}")
                    import traceback
                    logging.error(f"Трассировка: {traceback.format_exc()}")
                    await asyncio.sleep(2 * (attempt + 1))
            
            logging.error("Не удалось сгенерировать FLUX изображение после нескольких попыток")
            # Помечаем API как недоступное, чтобы не пытаться снова использовать его в ближайшее время
            self.api_unavailable = True
            # Используем локальное тестовое изображение
            logging.info("Создаем локальное тестовое изображение вместо использования API")
            return await create_local_test_image(prompt, session)
            
        finally:
            # Закрываем сессию, если мы её создали
            if close_session:
                await session.close()
        
    async def _try_request(self, session, url, data, attempt):
        """Выполняет запрос к API и обрабатывает результат."""
        try:
            async with session.post(url, headers=self.headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"FLUX API error (URL: {url}, попытка {attempt + 1}): {response.status} - {error_text}")
                    return None
                
                result = await response.json()
                logging.info(f"Получен ответ от FLUX API: {list(result.keys())}")
                
                # Проверяем структуру ответа
                if "images" not in result:
                    logging.error(f"Необычный формат ответа FLUX API: {result}")
                    return None
                
                image_url = result["images"][0].get("url", "")
                
                if not image_url:
                    logging.error(f"FLUX API не вернул URL изображения (попытка {attempt + 1})")
                    return None
                
                logging.info(f"Получен URL изображения: {image_url}")
                
                # Загружаем изображение по ссылке
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as img_response:
                    if img_response.status != 200:
                        logging.error(f"Ошибка загрузки изображения: {img_response.status}")
                        return None
                    
                    image_data = await img_response.read()
                    logging.info(f"Изображение FLUX загружено, размер={len(image_data)} байт")
                    
                    if image_data:
                        return io.BytesIO(image_data)
                        
        except Exception as e:
            logging.error(f"Ошибка при запросе к {url}: {e}")
            return None
        
        return None