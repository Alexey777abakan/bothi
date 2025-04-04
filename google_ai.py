import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv()

class GoogleAI:
    def __init__(self, api_key=None):
        """
        Инициализация клиента Google Generative AI (Gemini)
        
        Параметры:
            api_key (str): API ключ Google AI. Если не указан, будет использован из переменных окружения.
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_KEY")
        
        if not self.api_key:
            logging.warning("API ключ для Google AI не найден. Генерация контента будет недоступна.")
            return
            
        # Инициализация API
        genai.configure(api_key=self.api_key)
        
        # Получение доступных моделей
        try:
            self.models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Используем Gemini 2.0 Flash для более быстрого ответа
            # Если эта модель недоступна, автоматически вернемся к gemini-pro
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logging.info("Используется модель Gemini 2.0 Flash")
            except Exception as e:
                logging.warning(f"Модель gemini-2.0-flash недоступна: {e}. Используем gemini-pro")
                self.model = genai.GenerativeModel('gemini-pro')
            
            logging.info(f"Google AI клиент инициализирован. Доступные модели: {[m.name for m in self.models]}")
        except Exception as e:
            logging.error(f"Ошибка при инициализации Google AI: {e}")
            self.models = []
    
    async def generate_content(self, prompt, max_tokens=4000, temperature=0.7):
        """
        Генерация контента с помощью Google Generative AI
        
        Параметры:
            prompt (str): Запрос для генерации
            max_tokens (int): Максимальное количество токенов в ответе
            temperature (float): Температура генерации (0.0-1.0)
            
        Возвращает:
            str: Сгенерированный текст
        """
        if not self.api_key or not hasattr(self, 'model'):
            return "API ключ для Google AI не настроен или модель не инициализирована."
            
        try:
            # Настройка параметров генерации
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            # Генерация ответа
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Извлечение текста из ответа
            result = response.text
            
            return result
        
        except Exception as e:
            logging.error(f"Ошибка при генерации контента через Google AI: {e}")
            return f"Ошибка генерации через Google AI: {str(e)}"
    
    async def generate_image_prompt(self, theme, style):
        """
        Генерация промпта для изображения на основе темы и стиля
        
        Параметры:
            theme (str): Тема для изображения
            style (str): Стиль изображения
            
        Возвращает:
            str: Промпт для генерации изображения
        """
        prompt = f"""
        Создай детальный промпт для генерации изображения в стиле {style} на историческую тему: {theme}.
        
        Промпт должен включать:
        1. Детальное описание сцены, объектов и персонажей
        2. Указание на исторический период и его особенности
        3. Атмосферу и настроение изображения
        4. Цветовую палитру и освещение
        5. Стилистические особенности изображения
        
        Формат должен быть компактным, но информативным, подходящим для систем генерации изображений.
        """
        
        try:
            image_prompt = await self.generate_content(prompt, max_tokens=300, temperature=0.8)
            return image_prompt
        
        except Exception as e:
            logging.error(f"Ошибка при генерации промпта для изображения: {e}")
            return f"Не удалось создать промпт для изображения: {str(e)}"
    
    async def generate_historical_content(self, theme, style, format_type="post"):
        """
        Генерация исторического контента на заданную тему и в определенном стиле
        
        Параметры:
            theme (str): Историческая тема
            style (str): Стиль контента
            format_type (str): Тип формата (post, article, story)
            
        Возвращает:
            dict: Словарь с заголовком и контентом
        """
        prompt = f"""
        Создай увлекательный исторический {format_type} на тему: {theme}.
        
        Стиль написания: {style}
        
        Текст должен быть:
        1. Исторически достоверным, с упоминанием реальных фактов, дат и личностей
        2. Написан увлекательно и захватывающе
        3. Структурирован с заголовком и основным содержанием
        4. Объем основного содержания: 300-500 слов
        
        Формат вывода должен быть такой:
        ЗАГОЛОВОК: [Интересный заголовок]
        
        [Основное содержание поста]
        """
        
        try:
            generated_text = await self.generate_content(prompt, max_tokens=2000, temperature=0.7)
            
            # Разделение на заголовок и содержание
            if "ЗАГОЛОВОК:" in generated_text:
                parts = generated_text.split("ЗАГОЛОВОК:", 1)
                if len(parts) > 1:
                    title_content = parts[1].strip().split("\n", 1)
                    title = title_content[0].strip()
                    content = title_content[1].strip() if len(title_content) > 1 else ""
                else:
                    title = "История"
                    content = generated_text
            else:
                lines = generated_text.strip().split("\n")
                title = lines[0].strip()
                content = "\n".join(lines[1:]).strip()
            
            return {
                "title": title,
                "content": content
            }
        
        except Exception as e:
            logging.error(f"Ошибка при генерации исторического контента: {e}")
            return {
                "title": "Ошибка генерации",
                "content": f"Не удалось создать контент: {str(e)}"
            }


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def test_google_ai():
        ai = GoogleAI()
        result = await ai.generate_historical_content(
            theme="Древний Египет и пирамиды",
            style="Научно-популярный"
        )
        print(f"Заголовок: {result['title']}")
        print(f"Содержание: {result['content'][:200]}...")
    
    asyncio.run(test_google_ai()) 