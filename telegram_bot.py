import aiohttp
import re
import json
import logging
import asyncio
import io
from config import TELEGRAM_BOT_TOKEN, TEST_CHANNEL_ID, MAX_CAPTION_LENGTH, IMGUR_CLIENT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class TelegramBot:
    """Класс для отправки сообщений в Telegram."""
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.session = None
    
    async def create_session(self):
        """Создает сессию aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def send_telegram_post(self, text, image=None, session=None):
        """Отправляет пост с изображением в Telegram."""
        logging.info(f"Отправка поста: длина текста={len(text)}, есть изображение={image is not None}")
        
        use_existing_session = session is not None
        if not use_existing_session:
            session = await self.create_session()
        
        try:
            # Проверяем, что текст содержит заголовок и основной текст
            parts = text.split("\n\n", 1)
            if len(parts) != 2:
                logging.warning("Неправильный формат текста поста, добавляем разделители")
                title, content = text.split("\n", 1) if "\n" in text else (text, "")
                text = f"{title}\n\n{content}"
            
            # Если есть изображение, загружаем его на Imgur
            image_url = None
            if image:
                image_url = await upload_to_imgur(image, session)
            
            # Отправляем пост в Telegram
            message_id, file_id = await send_telegram_post(
                self.chat_id, text, image_url, image, session, token=self.token
            )
            
            return message_id is not None
            
        except Exception as e:
            logging.error(f"Ошибка отправки поста: {e}")
            return False
        finally:
            if not use_existing_session and session:
                await session.close()
    
    async def send_message(self, text, reply_markup=None, session=None):
        """Отправляет текстовое сообщение в Telegram."""
        use_existing_session = session is not None
        if not use_existing_session:
            session = await self.create_session()
        
        try:
            message_id = await send_telegram_message(
                self.chat_id, text, reply_markup, session, token=self.token
            )
            return message_id
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения: {e}")
            return None
        finally:
            if not use_existing_session and session:
                await session.close()
    
    async def edit_message(self, message_id, text, reply_markup=None, session=None):
        """Редактирует существующее сообщение в Telegram."""
        use_existing_session = session is not None
        if not use_existing_session:
            session = await self.create_session()
        
        try:
            result = await edit_telegram_message(
                self.chat_id, message_id, text, reply_markup, session, token=self.token
            )
            return result is not None
        except Exception as e:
            logging.error(f"Ошибка редактирования сообщения: {e}")
            return False
        finally:
            if not use_existing_session and session:
                await session.close()
    
    async def delete_messages(self, message_ids, session=None):
        """Удаляет сообщения из чата."""
        use_existing_session = session is not None
        if not use_existing_session:
            session = await self.create_session()
        
        try:
            result = await delete_telegram_messages(
                self.chat_id, message_ids, session, token=self.token
            )
            return result
        except Exception as e:
            logging.error(f"Ошибка удаления сообщений: {e}")
            return False
        finally:
            if not use_existing_session and session:
                await session.close()
    
    async def forward_post(self, from_chat_id, message_id, session=None):
        """Пересылает сообщение из одного чата в этот чат."""
        use_existing_session = session is not None
        if not use_existing_session:
            session = await self.create_session()
        
        try:
            result = await forward_telegram_post(
                from_chat_id, message_id, self.chat_id, session, token=self.token
            )
            return result is not None
        except Exception as e:
            logging.error(f"Ошибка пересылки сообщения: {e}")
            return False
        finally:
            if not use_existing_session and session:
                await session.close()

def escape_markdown(text):
    """Экранирует специальные символы для MarkdownV2, корректно обрабатывая точки и восклицательные знаки."""
    escape_chars = r"\_*[]()~`>#+-=|{}"  # Убрали . и ! отсюда
    text = re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)
    # Экранируем . и !, только если они НЕ являются частью уже экранированной последовательности
    text = re.sub(r"(?<!\\)\.", r"\\.", text)  # Экранируем ., только если перед ней нет \
    text = re.sub(r"(?<!\\)!", r"\\!", text)  # Экранируем !, только если перед ней нет \
    return text

def truncate_post(text, max_length=MAX_CAPTION_LENGTH):
    """Обрезает текст, если он превышает максимальную длину."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_punctuation = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    return (truncated[:last_punctuation + 1] + "...") if last_punctuation > -1 else (truncated + "...")


async def upload_to_imgur(image_data, session=None):
    """Загружает изображение на Imgur и возвращает URL."""
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    image_bytes = image_data.getvalue() if isinstance(image_data, io.BytesIO) else image_data

    for attempt in range(5):
        try:
            form_data = aiohttp.FormData()
            form_data.add_field("image", io.BytesIO(image_bytes), filename="image.jpg", content_type="image/jpeg")

            async with session.post(url, headers=headers, data=form_data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 503:
                    logging.warning(f"Imgur временно недоступен (503), повторяем через {10 * (attempt + 1)} секунд...")
                    await asyncio.sleep(10 * (attempt + 1))
                    continue
                if response.status != 200:
                    logging.error(f"Ошибка Imgur: {response.status}, сообщение='{await response.text()}'")
                    raise Exception(f"Загрузка на Imgur не удалась")

                result = await response.json()
                logging.info(f"Изображение загружено на Imgur: {result['data']['link']}")
                return result["data"]["link"]

        except Exception as e:
            logging.error(f"Ошибка загрузки на Imgur (попытка {attempt + 1}): {e}")
            if attempt < 4:
                await asyncio.sleep(10 * (attempt + 1))

    logging.error("Не удалось загрузить изображение на Imgur после всех попыток")
    return None

async def send_telegram_post(chat_id, formatted_post, image_url=None, image_data=None, session=None, token=None):
    """
    Отправляет пост в Telegram.
    Форматирует заголовок *перед* отправкой.
    """
    token = token or TELEGRAM_BOT_TOKEN
    logging.info(f"Отправка поста в Telegram: chat_id={chat_id}, есть изображение={image_data is not None}")
    
    # Разделяем пост на части *перед* форматированием
    parts = formatted_post.split("\n\n", 2)
    if len(parts) != 3:
        logging.error(f"Неверный формат поста: {formatted_post}")
        return None, None
    title, content, hashtags = parts[0], parts[1], parts[2]

    # *Форматируем заголовок*, добавляя звёздочки
    formatted_title = f"*{escape_markdown(title)}*"
    formatted_content = escape_markdown(content)
    formatted_hashtags = escape_markdown(hashtags)

    # Собираем *финальный* пост
    final_post = f"{formatted_title}\n\n{formatted_content}\n\n{formatted_hashtags}"
    final_post = truncate_post(final_post)  # Обрезаем *после* форматирования

    if image_data:  # Если у нас есть бинарные данные изображения
        logging.info(f"Отправка изображения напрямую через multipart/form-data")
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        # Создаем форму с multipart/form-data
        form_data = aiohttp.FormData()
        form_data.add_field("chat_id", str(chat_id))
        form_data.add_field("caption", final_post)
        form_data.add_field("parse_mode", "MarkdownV2")
        
        # Добавляем изображение
        if hasattr(image_data, 'read'):  # Это файл-подобный объект (BytesIO)
            # Устанавливаем указатель в начало файла
            image_data.seek(0)
            form_data.add_field("photo", image_data, filename="image.jpg", content_type="image/jpeg")
        else:  # Это уже бинарные данные
            form_data.add_field("photo", io.BytesIO(image_data), filename="image.jpg", content_type="image/jpeg")
        
        payload = form_data
    elif image_url:  # Если у нас есть URL изображения
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": final_post,
            "parse_mode": "MarkdownV2"
        }
    else:  # Если нет изображения
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": final_post,
            "parse_mode": "MarkdownV2"
        }

    for attempt in range(5):
        try:
            if isinstance(payload, aiohttp.FormData):
                async with session.post(url, data=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        logging.error(f"Ошибка Telegram при отправке изображения (попытка {attempt + 1}): {response.status}, сообщение='{response_text}'")
                        if attempt < 4:
                            await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    result = await response.json()
                    message_id = result["result"]["message_id"]
                    file_id = result["result"].get("photo", [{}])[-1].get("file_id") if "photo" in result["result"] else None
                    logging.info(f"Пост с изображением отправлен в Telegram: message_id={message_id}, file_id={file_id}")
                    return message_id, file_id
            else:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        logging.error(f"Ошибка Telegram (попытка {attempt + 1}): {response.status}, сообщение='{response_text}'")
                        if response.status == 400 and "can't parse entities" in response_text:
                            logging.error("  -> Ошибка форматирования Markdown. Проверьте escape_markdown().")
                        elif response.status == 429:
                            logging.warning("  -> Слишком много запросов к Telegram. Попробуйте увеличить задержки.")
                        if attempt < 4:
                            await asyncio.sleep(5 * (attempt + 1))
                        continue
                    
                    result = await response.json()
                    message_id = result["result"]["message_id"]
                    file_id = result["result"].get("photo", [{}])[-1].get("file_id") if "photo" in result["result"] else None
                    logging.info(f"Пост отправлен в Telegram: message_id={message_id}, file_id={file_id}")
                    return message_id, file_id
        except Exception as e:
            logging.error(f"Ошибка отправки поста в Telegram (попытка {attempt + 1}): {e}")
            if attempt < 4:
                await asyncio.sleep(5 * (attempt + 1))

    logging.error("Не удалось отправить пост после всех попыток")
    # Если не удалось отправить с изображением, попробуем без него
    if image_data or image_url:
        logging.info("Попытка отправить пост без изображения")
        return await send_telegram_post(chat_id, formatted_post, None, None, session)
    return None, None


async def send_telegram_message(chat_id, text, reply_markup=None, session=None, token=None):
    """Отправляет текстовое сообщение в Telegram."""
    token = token or TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": escape_markdown(text), "parse_mode": "MarkdownV2"}  # Экранируем текст *перед* отправкой
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)  # Добавляем клавиатуру, если есть

    for attempt in range(3):
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response_text = await response.text()
                if response.status != 200:
                    logging.error(f"Ошибка отправки сообщения в Telegram (попытка {attempt + 1}): {response.status}, message='{response_text}', url='{url}'")
                    if response.status == 400 and "can't parse entities" in response_text:
                        logging.error("  -> Probable Markdown formatting error. Check escape_markdown().")
                    if attempt < 2:
                        await asyncio.sleep(5 * (attempt+1))
                    continue

                result = await response.json()
                message_id = result["result"]["message_id"]
                logging.info(f"Сообщение отправлено: chat_id={chat_id}, message_id={message_id}")
                return message_id
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения в Telegram (попытка {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(5 * (attempt + 1))

    logging.error("Не удалось отправить сообщение после всех попыток")
    return None

async def edit_telegram_message(chat_id, message_id, text, reply_markup=None, session=None, token=None):
    """Редактирует существующее сообщение в Telegram."""
    token = token or TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": escape_markdown(text),
        "parse_mode": "MarkdownV2"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    for attempt in range(3):
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    response_text = await response.text()
                    logging.error(f"Ошибка редактирования сообщения (попытка {attempt + 1}): {response.status}, message='{response_text}'")
                    if "message is not modified" in response_text:
                        logging.warning("Сообщение не было изменено, так как текст идентичен")
                        return message_id  # Считаем успехом, если сообщение уже содержит этот текст
                    if attempt < 2:
                        await asyncio.sleep(5 * (attempt+1))
                    continue

                result = await response.json()
                logging.info(f"Сообщение отредактировано: chat_id={chat_id}, message_id={message_id}")
                return message_id
        except Exception as e:
            logging.error(f"Ошибка редактирования сообщения (попытка {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(5 * (attempt + 1))

    logging.error("Не удалось отредактировать сообщение после всех попыток")
    return None

async def delete_telegram_messages(chat_id, message_ids, session=None, token=None):
    """Удаляет сообщения из чата."""
    token = token or TELEGRAM_BOT_TOKEN
    if not isinstance(message_ids, list):
        message_ids = [message_ids]
    
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    results = []
    
    for message_id in message_ids:
        payload = {"chat_id": chat_id, "message_id": message_id}
        
        for attempt in range(3):
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logging.error(f"Ошибка удаления сообщения {message_id} (попытка {attempt + 1}): {response.status}")
                        if attempt < 2:
                            await asyncio.sleep(2 * (attempt+1))
                        continue
                    
                    results.append(message_id)
                    logging.info(f"Сообщение {message_id} удалено из чата {chat_id}")
                    break
            except Exception as e:
                logging.error(f"Ошибка удаления сообщения {message_id} (попытка {attempt + 1}): {e}")
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
    
    return len(results) == len(message_ids)  # True если все сообщения удалены

async def forward_telegram_post(from_chat_id, message_id, to_chat_id, session=None, token=None):
    """Пересылает сообщение из одного чата в другой."""
    token = token or TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/forwardMessage"
    payload = {
        "chat_id": to_chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    }
    
    for attempt in range(3):
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logging.error(f"Ошибка пересылки сообщения (попытка {attempt + 1}): {response.status}")
                    if attempt < 2:
                        await asyncio.sleep(5 * (attempt+1))
                    continue
                
                result = await response.json()
                new_message_id = result["result"]["message_id"]
                logging.info(f"Сообщение {message_id} переслано из {from_chat_id} в {to_chat_id}, новый ID: {new_message_id}")
                return new_message_id
        except Exception as e:
            logging.error(f"Ошибка пересылки сообщения (попытка {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(5 * (attempt + 1))
    
    logging.error("Не удалось переслать сообщение после всех попыток")
    return None