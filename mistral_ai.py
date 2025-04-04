import os
import logging
import json
import requests
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

class MistralAPI:
    """Класс для взаимодействия с Mistral AI API для генерации исторического контента."""
    
    def __init__(self, api_key=None):
        """
        Инициализация API клиента Mistral AI
        
        Параметры:
            api_key (str, optional): API ключ Mistral. Если не указан, используется из .env
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "FsUvt9ZM403XMhVtLDyRu3PeNXzwjiKT")
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        
        # Заголовки для запросов к API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logging.info(f"MistralAPI инициализирован с моделью {self.model}")
    
    async def generate_text(self, prompt, system_prompt="", max_tokens=4000, temperature=0.7):
        """
        Генерация текста с использованием Mistral AI
        
        Параметры:
            prompt (str): Текст запроса
            system_prompt (str, optional): Системный промпт для настройки поведения модели
            max_tokens (int, optional): Максимальное количество токенов в ответе
            temperature (float, optional): Температура (случайность) генерации 0.0-1.0
            
        Возвращает:
            str: Сгенерированный текст
        """
        try:
            messages = []
            
            # Добавляем системный промпт, если он указан
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            # Добавляем запрос пользователя
            messages.append({"role": "user", "content": prompt})
            
            # Создаем тело запроса
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9
            }
            
            # Делаем запрос к API с несколькими попытками в случае ошибок
            for attempt in range(3):
                try:
                    response = requests.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload,
                        timeout=60  # Таймаут 60 секунд
                    )
                    
                    # Проверяем статус ответа
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result["choices"][0]["message"]["content"]
                        logging.info(f"Успешно получен ответ от Mistral AI, длина текста: {len(generated_text)}")
                        return generated_text
                    else:
                        logging.error(f"Ошибка API Mistral: {response.status_code} - {response.text}")
                        if attempt < 2:  # Если еще не последняя попытка
                            wait_time = 5 * (attempt + 1)
                            logging.info(f"Повторяем запрос через {wait_time} секунд...")
                            time.sleep(wait_time)
                        else:
                            return f"Ошибка генерации текста: {response.status_code}"
                
                except requests.exceptions.Timeout:
                    logging.error(f"Таймаут при запросе к Mistral API (попытка {attempt+1}/3)")
                    if attempt < 2:
                        wait_time = 10 * (attempt + 1)
                        logging.info(f"Повторяем запрос через {wait_time} секунд...")
                        time.sleep(wait_time)
                    else:
                        return "Ошибка генерации текста: превышено время ожидания"
                        
                except Exception as e:
                    logging.error(f"Ошибка при запросе к Mistral API: {e}")
                    if attempt < 2:
                        wait_time = 10 * (attempt + 1)
                        logging.info(f"Повторяем запрос через {wait_time} секунд...")
                        time.sleep(wait_time)
                    else:
                        return f"Ошибка генерации текста: {str(e)}"
        
        except Exception as e:
            logging.error(f"Критическая ошибка при работе с Mistral AI: {e}")
            return f"Критическая ошибка генерации: {str(e)}"
    
    async def generate_historical_title(self, theme, language="ru"):
        """
        Генерирует заголовок для исторического поста
        
        Параметры:
            theme (str): Историческая тема
            language (str): Язык генерации ('ru' или 'en')
            
        Возвращает:
            str: Заголовок для исторического поста
        """
        system_prompt = """Ты - эксперт по истории, который пишет увлекательные заголовки для исторических постов.
        Твоя задача - придумать один цепляющий, интригующий заголовок для исторического поста по указанной теме.
        Заголовок должен быть коротким (до 100 символов), привлекательным и содержать исторические факты.
        Верни только сам заголовок без кавычек и дополнительных пояснений."""
        
        prompt = f"""Создай заголовок для исторического поста на тему: "{theme}".
        
        Заголовок должен быть:
        - На {'русском' if language == 'ru' else 'английском'} языке
        - Коротким (до 100 символов)
        - Интригующим, вызывающим желание прочитать пост
        - Основанным на исторических фактах
        - Без очевидных кликбейтов и излишних эмоций
        
        Пожалуйста, верни только сам заголовок без кавычек, номера, дополнительного форматирования или пояснений."""
        
        title = await self.generate_text(prompt, system_prompt, max_tokens=100, temperature=0.7)
        
        # Очистка от кавычек и переносов строк
        title = title.strip('"\'„"').strip().replace('\n', ' ')
        
        return title
    
    async def generate_historical_content(self, title, theme, style="научно-популярный", language="ru"):
        """
        Генерирует содержимое исторического поста
        
        Параметры:
            title (str): Заголовок поста
            theme (str): Тема поста
            style (str): Стиль поста 
            language (str): Язык генерации ('ru' или 'en')
            
        Возвращает:
            dict: Словарь с контентом и хэштегами
        """
        system_prompt = """Ты - профессиональный историк, пишущий увлекательные исторические посты.
        Твоя задача - создать информативный и захватывающий исторический пост для социальных сетей.
        Пост должен быть достоверным, основанным на фактах и соответствовать заданной теме и стилю.
        Текст должен быть структурированным, с логически связанными абзацами и подходящими хэштегами в конце."""
        
        lang_text = "русском" if language == "ru" else "английском"
        tag_examples = "#история #факты #прошлое" if language == "ru" else "#history #facts #past"
        
        prompt = f"""Создай исторический пост по заголовку "{title}" на тему "{theme}".
        
        Стиль: {style}
        Язык: {lang_text}
        
        Требования к посту:
        1. Объем: 300-500 слов (не более 2000 символов)
        2. Должен быть информативным, основанным на исторических фактах
        3. Текст разбей на 2-3 логичных абзаца
        4. Используй доступный язык, понятный широкой аудитории
        5. В конце добавь 3-5 релевантных хэштегов (например: {tag_examples})
        
        Структура ответа должна быть такой:
        [Основной текст поста из 2-3 абзацев]
        
        [Хэштеги]"""
        
        response = await self.generate_text(prompt, system_prompt, max_tokens=2000, temperature=0.7)
        
        # Разделяем контент и хэштеги
        parts = response.split("\n\n")
        
        # Ищем хэштеги в последней части текста
        if parts and '#' in parts[-1]:
            content = "\n\n".join(parts[:-1]).strip()
            hashtags = parts[-1].strip()
        else:
            # Если формат не соблюден, выделяем хэштеги самостоятельно
            content = response.strip()
            if "#" in content:
                # Ищем последний абзац с хэштегами
                paragraphs = content.split("\n\n")
                if '#' in paragraphs[-1]:
                    hashtags = paragraphs[-1]
                    content = "\n\n".join(paragraphs[:-1])
                else:
                    # Создаем базовые хэштеги
                    if language == "ru":
                        hashtags = "#история #факты #прошлое"
                    else:
                        hashtags = "#history #facts #past"
            else:
                # Создаем базовые хэштеги
                if language == "ru":
                    hashtags = "#история #факты #прошлое"
                else:
                    hashtags = "#history #facts #past"
        
        return {
            "content": content,
            "hashtags": hashtags
        }
    
    async def generate_image_prompt(self, title, theme, language="en"):
        """
        Генерирует промпт для создания изображения
        
        Параметры:
            title (str): Заголовок поста
            theme (str): Тема поста
            language (str): Язык для промпта (en рекомендуется для лучших результатов)
            
        Возвращает:
            str: Промпт для генерации изображения
        """
        system_prompt = """Ты - эксперт по созданию промптов для генерации исторических изображений.
        Твоя задача - создать детальный и информативный промпт на английском языке для системы генерации изображений.
        Промпт должен описывать историческую сцену, соответствующую заданной теме и заголовку."""
        
        prompt_lang = "английском" if language == "en" else "русском"
        
        prompt = f"""Создай детальный промпт для генерации исторического изображения на основе заголовка "{title}" и темы "{theme}".
        
        Промпт должен быть на {prompt_lang} языке и включать:
        1. Описание исторической сцены (место, время, персонажи)
        2. Детали окружения и атмосферы
        3. Стиль изображения (фотореалистичный, художественный и т.д.)
        4. Освещение и цветовую гамму
        
        Промпт должен быть конкретным, информативным и содержать 3-5 предложений общей длиной 100-200 символов.
        Не используй специальные символы, только обычный текст.
        
        Пример хорошего промпта:
        "Historical scene of Napoleon at Waterloo, 1815. Dramatic battlefield with soldiers in French imperial uniforms. Photorealistic style, cinematic lighting, stormy sky, detailed costumes."
        
        Верни только сам промпт без дополнительных пояснений."""
        
        image_prompt = await self.generate_text(prompt, system_prompt, max_tokens=200, temperature=0.7)
        
        # Очистка от лишних кавычек и переносов строк
        image_prompt = image_prompt.strip('"\'„"').strip().replace('\n', ' ')
        
        # Если язык должен быть английским, но промпт на русском, пытаемся исправить
        if language == "en" and any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in image_prompt.lower()):
            # Пытаемся перевести промпт на английский
            translate_prompt = f"Переведи этот промпт для генерации изображения на английский язык: {image_prompt}"
            try:
                image_prompt = await self.generate_text(translate_prompt, "", max_tokens=200, temperature=0.3)
                image_prompt = image_prompt.strip('"\'„"').strip().replace('\n', ' ')
            except Exception as e:
                logging.error(f"Ошибка при попытке перевода промпта: {e}")
        
        return image_prompt


# Тестирование класса
if __name__ == "__main__":
    import asyncio
    
    async def test_mistral():
        api = MistralAPI()
        
        # Тест генерации заголовка
        title = await api.generate_historical_title("Вторая мировая война", "ru")
        print(f"Заголовок: {title}")
        
        # Тест генерации контента
        result = await api.generate_historical_content(
            title, "Вторая мировая война", "информативный", "ru"
        )
        print(f"Контент: {result['content']}")
        print(f"Хэштеги: {result['hashtags']}")
        
        # Тест генерации промпта для изображения
        image_prompt = await api.generate_image_prompt(title, "Вторая мировая война", "en")
        print(f"Промпт для изображения: {image_prompt}")
        
    asyncio.run(test_mistral()) 