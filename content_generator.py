import aiohttp
import json
import logging
import asyncio
import re
import traceback
import os
from dotenv import load_dotenv
from config import MAX_POST_LENGTH, OPENROUTER_API_KEY
from prompts import TITLE_PROMPT, POST_PROMPT, IMAGE_PROMPT
from mistral_ai import MistralAPI  # Добавляем импорт нового класса
from google_ai import GoogleAI  # Импорт Google AI

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('content_generator.log')
    ]
)

class ContentGenerator:
    """Класс для генерации контента для исторических постов."""
    def __init__(self):
        self.api = OpenRouterAPI()
        self.google_ai = GoogleAI()  # Инициализируем Google AI
        self.mistral_ai = MistralAPI()  # Инициализируем Mistral AI
        self.language = "ru"  # Установим русский как язык по умолчанию
        self.post_style = "информативно-развлекательный"  # Стиль постов по умолчанию
        self.use_google_ai = False  # По умолчанию не используем Google AI
        self.use_mistral_ai = True  # По умолчанию используем Mistral AI
        
    async def generate_title(self, theme):
        """Генерирует заголовок для поста на историческую тему."""
        if self.use_mistral_ai:
            try:
                logging.info(f"Генерация заголовка через Mistral AI для темы: {theme}")
                title = await self.mistral_ai.generate_historical_title(theme, self.language)
                logging.info(f"Mistral AI сгенерировал заголовок: {title}")
                return title
            except Exception as e:
                logging.error(f"Ошибка генерации заголовка через Mistral AI: {e}")
                # Если не удалось, переходим к следующему варианту
                self.use_mistral_ai = False
                
        if self.use_google_ai:
            try:
                logging.info(f"Генерация заголовка через Google AI для темы: {theme}")
                prompt = f"""
                Создай интересный и привлекательный заголовок для исторического поста на тему: {theme}.
                Заголовок должен быть на русском языке, коротким (до 50 символов) и вызывать интерес к чтению.
                Не используй кавычки вокруг заголовка. Верни только сам заголовок, без вводных слов.
                """
                title = await self.google_ai.generate_content(prompt, max_tokens=50, temperature=0.8)
                # Очистка от кавычек и лишних символов
                title = title.strip('"\'„"').strip()
                logging.info(f"Google AI сгенерировал заголовок: {title}")
                return title
            except Exception as e:
                logging.error(f"Ошибка генерации заголовка через Google AI: {e}")
                # Если не удалось, используем запасной вариант
                self.use_google_ai = False
        
        # Запасной вариант через OpenRouter API
        async with aiohttp.ClientSession() as session:
            titles_text = await self.api.generate_titles(theme, 1, self.language, session)
            if not titles_text:
                return None
                
            # Берем первый заголовок из списка
            titles = [line.strip() for line in titles_text.split('\n') if line.strip()]
            if not titles:
                return None
                
            return titles[0]
    
    async def generate_post_content(self, title, theme):
        """Генерирует содержимое поста на основе заголовка и темы."""
        if self.use_mistral_ai:
            try:
                logging.info(f"Генерация содержания через Mistral AI для заголовка: {title}")
                result = await self.mistral_ai.generate_historical_content(
                    title=title,
                    theme=theme,
                    style=self.post_style,
                    language=self.language
                )
                content = result["content"]
                hashtags = result["hashtags"]
                logging.info(f"Mistral AI сгенерировал контент длиной {len(content)} символов и хэштеги: {hashtags}")
                return f"{content}\n\n{hashtags}"
            except Exception as e:
                logging.error(f"Ошибка генерации контента через Mistral AI: {e}")
                # Если не удалось, переходим к следующему варианту
                self.use_mistral_ai = False
                
        if self.use_google_ai:
            try:
                logging.info(f"Генерация содержания через Google AI для заголовка: {title}")
                result = await self.google_ai.generate_historical_content(
                    theme=theme,
                    style=self.post_style,
                    format_type="post"
                )
                content = result["content"]
                logging.info(f"Google AI сгенерировал контент длиной {len(content)} символов")
                return content
            except Exception as e:
                logging.error(f"Ошибка генерации контента через Google AI: {e}")
                # Если не удалось, используем запасной вариант
                self.use_google_ai = False
        
        # Запасной вариант через OpenRouter API
        async with aiohttp.ClientSession() as session:
            content = await self.api.generate_post_content(
                title, theme, self.post_style, MAX_POST_LENGTH, self.language, session
            )
            return content
    
    async def generate_image_prompt(self, title, theme, language="en", session=None):
        """Генерирует промпт для создания изображения."""
        if self.use_mistral_ai:
            try:
                logging.info(f"Генерация промпта для изображения через Mistral AI: {title}")
                image_prompt = await self.mistral_ai.generate_image_prompt(title, theme, language)
                logging.info(f"Mistral AI сгенерировал промпт для изображения длиной {len(image_prompt)} символов")
                return image_prompt
            except Exception as e:
                logging.error(f"Ошибка генерации промпта для изображения через Mistral AI: {e}")
                # Если не удалось, переходим к следующему варианту
                self.use_mistral_ai = False
                
        if self.use_google_ai:
            try:
                logging.info(f"Генерация промпта для изображения через Google AI: {title}")
                image_prompt = await self.google_ai.generate_image_prompt(theme, "фотореалистичный")
                logging.info(f"Google AI сгенерировал промпт для изображения длиной {len(image_prompt)} символов")
                return image_prompt
            except Exception as e:
                logging.error(f"Ошибка генерации промпта для изображения через Google AI: {e}")
                # Если не удалось, используем запасной вариант
                self.use_google_ai = False
        
        # Оригинальный метод остается без изменений для резервного использования
        logging.info(f"Генерация описания изображения для '{title}' на языке: {language}")
        if language not in IMAGE_PROMPT:
            language = "en"
        
        # Создаем резервный промпт заранее
        if language == "ru":
            backup_prompt = f"Фотореалистичное изображение средневекового замка на фоне европейского пейзажа, связанное с темой '{title}'. Высокое качество, детализация, дневное освещение."
        else:
            backup_prompt = f"Photorealistic image of a medieval castle against a European landscape, related to '{title}'. High quality, detailed, daylight."
        
        try:
            prompt = IMAGE_PROMPT[language].format(title=title, theme=theme)
            
            # Дополнительные инструкции для создания качественного промпта (делаем их короче)
            prompt += "\n\nВажно: создай краткий, четкий промпт для изображения."
            
            image_prompt = await self.api.generate_text(prompt, max_tokens=100, session=session)
            
            # Проверяем, не пустой ли ответ
            if not image_prompt or len(image_prompt.strip()) < 10:
                logging.warning(f"Получен пустой или слишком короткий промпт для изображения, использую резервный")
                return backup_prompt
            
            # Ограничение длины промпта
            if len(image_prompt) > 300:
                image_prompt = image_prompt[:300].rsplit(' ', 1)[0] + '.'
                
            return image_prompt.strip()
            
        except Exception as e:
            logging.error(f"Ошибка при генерации промпта для изображения: {e}")
            return backup_prompt

class OpenRouterAPI:
    """Класс для взаимодействия с OpenRouter API (Google Gemini)."""
    def __init__(self):
        self.API_KEY = OPENROUTER_API_KEY
        self.PRIMARY_MODEL = "google/gemini-2.5-pro-exp-03-25:free"
        self.BACKUP_MODEL = "deepseek/deepseek-chat-v3-0324:free"  # Резервная модель DeepSeek
        self.LAST_RESORT_MODEL = "openai/gpt-4o-mini:free"  # Третья модель на крайний случай
        self.MODEL = self.PRIMARY_MODEL  # Текущая модель по умолчанию
        self.URL = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/publikator_bot",  # Необходимо для OpenRouter
            "User-Agent": "Telegram Bot Publikator",  # Идентификация приложения
            "X-Title": "PublikatorBot"  # Название для панели управления OpenRouter
        }

    async def generate_text(self, prompt, max_tokens=2000, session=None):
        """Генерирует текст с помощью OpenRouter API."""
        # Попробуем с основной моделью
        result = await self._try_generate_with_model(self.PRIMARY_MODEL, prompt, max_tokens, session)
        
        # Специальная обработка ошибки квоты
        if result == "QUOTA_EXCEEDED":
            logging.warning(f"Квота для модели {self.PRIMARY_MODEL} превышена, переключаемся на {self.BACKUP_MODEL}")
            result = await self._try_generate_with_model(self.BACKUP_MODEL, prompt, max_tokens, session)
        # Если другая ошибка или null, тоже пробуем резервную модель
        elif result is None:
            logging.warning(f"Основная модель {self.PRIMARY_MODEL} не сработала, пробуем резервную {self.BACKUP_MODEL}")
            result = await self._try_generate_with_model(self.BACKUP_MODEL, prompt, max_tokens, session)
        
        # Если и резервная модель не сработала или также превысила квоту, попробуем третью модель
        if result is None or result == "QUOTA_EXCEEDED":
            logging.warning(f"Резервная модель {self.BACKUP_MODEL} не сработала, пробуем последний вариант {self.LAST_RESORT_MODEL}")
            result = await self._try_generate_with_model(self.LAST_RESORT_MODEL, prompt, max_tokens, session)
            
        # Если это был "QUOTA_EXCEEDED" и для последней модели, заменим на None
        if result == "QUOTA_EXCEEDED":
            logging.error(f"Квота превышена для всех моделей")
            return None
            
        return result
            
    async def _try_generate_with_model(self, model_name, prompt, max_tokens=2000, session=None):
        """Пытается сгенерировать текст с указанной моделью."""
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": False,
            "response_format": {"type": "text"}
        }
        for attempt in range(3):  # Уменьшаем количество попыток для каждой модели
            try:
                logging.info(f"Отправка запроса к OpenRouter API с моделью {model_name} (попытка {attempt + 1})")
                async with session.post(self.URL, headers=self.headers, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response_text = await response.text()
                    
                    # Если получили ошибку квоты (429), сразу прекращаем попытки с этой моделью
                    if response.status == 429 or ("error" in response_text and "429" in response_text):
                        logging.error(f"Ошибка превышения квоты (429) для модели {model_name}: {response_text[:200]}...")
                        # Возвращаем особый статус для обработки в вызывающем методе
                        return "QUOTA_EXCEEDED"
                        
                    if response.status != 200:
                        logging.error(f"Ошибка OpenRouter API (попытка {attempt + 1}): {response.status} - {response_text}")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    try:
                        result = json.loads(response_text)
                        logging.info(f"Ответ от OpenRouter API получен, структура: {list(result.keys())}")
                    except json.JSONDecodeError as e:
                        logging.error(f"Не удалось разобрать JSON-ответ: {e}. Полный ответ: {response_text[:200]}...")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    # Проверка на ошибку 429 внутри JSON-ответа
                    if "error" in result and ("code" in result["error"] and result["error"]["code"] == 429):
                        logging.error(f"Ошибка превышения квоты (429) в ответе JSON для модели {model_name}")
                        return "QUOTA_EXCEEDED"
                    
                    # Проверяем корректную структуру ответа
                    if "choices" not in result:
                        logging.error(f"Неожиданная структура ответа от OpenRouter API: {result}")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    if not result["choices"] or "message" not in result["choices"][0]:
                        logging.error(f"Пустой список choices или отсутствует message: {result}")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    generated_text = result["choices"][0]["message"]["content"].strip()
                    logging.info(f"Сгенерирован текст, длина={len(generated_text)} символов")
                    
                    # Если текст пустой, повторим попытку
                    if not generated_text:
                        logging.error("Получен пустой ответ от модели")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                        
                    return generated_text
            except Exception as e:
                error_traceback = traceback.format_exc()
                logging.error(f"Ошибка генерации текста с моделью {model_name} (попытка {attempt + 1}): {e}\n{error_traceback}")
                await asyncio.sleep(5 * (attempt + 1))
        
        logging.error(f"Не удалось сгенерировать текст с моделью {model_name} после всех попыток")
        return None

    async def generate_titles(self, theme, post_count, language="en", session=None):
        """Генерирует заголовки постов."""
        logging.info(f"Генерация заголовков на языке: {language}")
        if language not in TITLE_PROMPT:
            language = "en"
        prompt = TITLE_PROMPT[language].format(post_count=post_count, theme=theme)
        
        # Добавляем инструкции для модели по формату и количеству
        prompt += f"\n\nВажно: генерируй ровно {post_count} заголовков, по одному в строке. Не нумеруй их."
        
        titles = await self.generate_text(prompt, max_tokens=1000, session=session)
        if not titles:
            logging.error("Получен пустой ответ при генерации заголовков")
            return None
            
        # Обработка и очистка заголовков
        titles = re.sub(r'["\'""]', '', titles, flags=re.MULTILINE)
        titles = re.sub(r'^\d+\.\s*', '', titles, flags=re.MULTILINE)
        titles = titles.strip()
        
        # Проверка, что получены заголовки
        lines = [line.strip() for line in titles.split('\n') if line.strip()]
        if not lines:
            logging.error("После обработки не осталось заголовков")
            return None
            
        logging.info(f"Сгенерировано заголовков: {len(lines)}")
        return titles

    async def generate_post_content(self, title, theme, style, max_length=MAX_POST_LENGTH, language="en", session=None):
        """Генерирует контент поста и хэштеги."""
        logging.info(f"Генерация контента для '{title}' на языке: {language}")
        if language not in POST_PROMPT:
            language = "en"
        prompt = POST_PROMPT[language].format(title=title, theme=theme, style=style, max_length=max_length)
        
        # Добавляем инструкции
        prompt += f"\n\nВажно: придерживайся длины {max_length} символов и структуры с 2 абзацами и 3 хэштегами. Не используй заголовок в тексте."
        
        post_content = await self.generate_text(prompt, max_tokens=2000, session=session)
        if not post_content:
            logging.error("Получен пустой ответ при генерации контента поста")
            return None
            
        try:
            # Обработка контента поста
            post_content = post_content.strip()
            
            # Разделяем контент и хэштеги
            parts = post_content.split('\n\n')
            if len(parts) >= 3 and '#' in parts[-1]:
                content = '\n\n'.join(parts[:-1]).strip()
                hashtags = parts[-1].strip()
            else:
                # Если формат некорректный, но есть текст, попытаемся разделить его самостоятельно
                content = post_content.strip()
                content_parts = content.split('\n\n')
                
                # Проверяем, есть ли хэштеги в последней части
                if content_parts and any(part.startswith('#') for part in content_parts[-1].split()):
                    hashtags = content_parts[-1]
                    content = '\n\n'.join(content_parts[:-1])
                else:
                    # Если хэштегов нет, добавляем стандартные
                    if language == "ru":
                        hashtags = "#история #события #девяностые"
                    else:
                        hashtags = "#history #events #nineties"
                    logging.warning(f"Неправильный формат для '{title}', добавлены стандартные хэштеги")
            
            # Ограничение длины контента
            if len(content) > max_length - len(hashtags) - 2:
                content = content[:max_length - len(hashtags) - 2]
                last_period = content.rfind('.')
                if last_period != -1:
                    content = content[:last_period + 1]
    
            # Форматирование на параграфы
            sentences = content.split('. ')
            if len(sentences) > 1:
                mid = len(sentences) // 2
                paragraph1 = '. '.join(sentences[:mid]).strip()
                paragraph2 = '. '.join(sentences[mid:]).strip()
                content = f"{paragraph1}\n\n{paragraph2}"
            else:
                if language == "ru":
                    content = f"{content}\n\nПодробности скоро"
                else:
                    content = f"{content}\n\nMore details coming soon"
    
            # Формируем финальный результат
            formatted_post = f"{content}\n\n{hashtags}"
            logging.info(f"Сгенерирован контент поста, длина={len(formatted_post)} символов")
            return formatted_post
            
        except Exception as e:
            logging.error(f"Ошибка обработки контента для '{title}': {e}")
            return None

    async def generate_image_prompt(self, title, theme, language="en", session=None):
        """Генерирует промпт для изображения."""
        logging.info(f"Генерация описания изображения для '{title}' на языке: {language}")
        if language not in IMAGE_PROMPT:
            language = "en"
        prompt = IMAGE_PROMPT[language].format(title=title, theme=theme)
        
        # Дополнительные инструкции для создания качественного промпта
        prompt += "\n\nВажно: создай четкий, фотореалистичный промпт. Не включай запрещенный контент."
        
        image_prompt = await self.generate_text(prompt, max_tokens=200, session=session)
        if not image_prompt:
            logging.error(f"Не удалось сгенерировать промпт для изображения '{title}'")
            if language == "ru":
                return f"Фотореалистичное изображение, иллюстрирующее {title} в контексте {theme}. Высокое качество, детализация."
            else:
                return f"Photorealistic image illustrating {title} in the context of {theme}. High quality, detailed."
        
        # Ограничение длины промпта
        if len(image_prompt) > 500:
            image_prompt = image_prompt[:500].rsplit(' ', 1)[0] + '.'
            
        return image_prompt.strip()