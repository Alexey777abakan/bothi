import aiohttp
import json
import logging
import asyncio
import re
import traceback
from config import MAX_POST_LENGTH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('content_generator.log')
    ]
)

# Шаблоны остаются такими же
TITLE_PROMPT = {
    "en": """Generate exactly {post_count} short, unique, and engaging titles for Telegram posts, focusing on key events, aspects, or examples of the theme '{theme}'. Distribute the titles evenly across significant moments, figures, or impacts related to the theme. Do not use quotation marks, numbers, or any prefixes/suffixes in the titles. Provide only titles, one per line, without extra text or numbering.""",
    "ru": """Сгенерируй ровно {post_count} коротких, уникальных и цепляющих заголовков для Telegram-постов, фокусируясь на ключевых событиях, аспектах или примерах темы '{theme}'. Распредели заголовки равномерно по значимым моментам, фигурам или воздействиям, связанным с темой. Не используй кавычки, цифры, префиксы или суффиксы в заголовках. Предоставь только заголовки, по одному на строку, без дополнительного текста, нумерации или форматирования.""",
}

POST_PROMPT = {
    "en": """Write an SEO-optimized post in {style} style for Telegram with the title '{title}'. Explore the event, aspect, or example from the title, related to the theme '{theme}', without literally repeating the title or theme. Use vivid, emotional language, specific examples, and compelling arguments to engage the reader. Structure the content into 2 concise, energetic paragraphs for readability. Length: strictly up to {max_length} characters, including exactly 3 SEO-friendly hashtags (short, trending, relevant) on a new line. Format:

[paragraph 1]

[paragraph 2]

#hashtag1 #hashtag2 #hashtag3

IMPORTANT: Do not repeat the title and its parts in the post text. Start directly with exploring the topic.""",
    "ru": """Напиши SEO-оптимизированный пост в стиле {style} для Telegram с заголовком '{title}'. Раскрой событие, аспект или пример из заголовка, связанный с темой '{theme}', не повторяя дословно заголовок или тему. Используй яркий, эмоциональный язык, конкретные примеры и убедительные аргументы, чтобы зацепить читателя. Структурируй контент в 2 сжатых, энергичных абзаца для удобства чтения. Длина: строго до {max_length} символов, включая ровно 3 SEO-дружественных хэштега (коротких, трендовых, релевантных) на новой строке. Формат:

[абзац 1]

[абзац 2]

#хэштег1 #хэштег2 #хэштег3

ВАЖНО: Не повторяй заголовок и его части в тексте поста. Начни сразу с раскрытия темы.""",
}

IMAGE_PROMPT = {
    "en": """Create a concise prompt (under 500 characters) for FLUX image generation API to create a photorealistic image for a post titled '{title}' in the theme '{theme}'. Describe a key scene with main action, characters, setting, mood, and objects. Use photorealistic style, high resolution. Do not use any forbidden content like violence, adult content, or copyright material.""",
    "ru": """Создай краткий промпт (до 500 символов) для FLUX API, чтобы сгенерировать фотореалистичное изображение для поста с заголовком '{title}' в теме '{theme}'. Опиши ключевую сцену с действием, персонажами, местом, настроением и объектами. Стиль — фотореализм, высокое разрешение. Не используй запрещенный контент: насилие, контент для взрослых или материалы с авторскими правами."""
}

class OpenRouterAPI:
    """Класс для взаимодействия с OpenRouter API (Google Gemini)."""
    def __init__(self):
        self.API_KEY = "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"
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
        
        # Дополнительные инструкции для обеспечения правильного формата
        prompt += "\n\nФормат ответа должен быть строго:\n[параграф 1]\n\n[параграф 2]\n\n#хэштег1 #хэштег2 #хэштег3"
        
        post_content = await self.generate_text(prompt, max_tokens=2000, session=session)
        if not post_content:
            logging.error(f"Не удалось сгенерировать контент для '{title}'")
            return None, None

        # Попытаемся разобрать сгенерированный текст
        try:
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
    
            return content, hashtags
        except Exception as e:
            logging.error(f"Ошибка обработки контента для '{title}': {e}")
            return None, None

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