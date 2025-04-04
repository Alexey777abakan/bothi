# create_test_image.py
import os
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_image(text="Тестовое изображение", 
                     color=(73, 109, 137), 
                     width=1024, 
                     height=1024,
                     text_color=(255, 255, 255)):
    """Создает тестовое изображение с заданным текстом и цветом."""
    try:
        logging.info(f"Создание тестового изображения размером {width}x{height}")
        
        # Создаем изображение
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            # Если шрифт не найден, используем стандартный
            font = None
        
        d.text((width//2, height//2), text, 
               fill=text_color, font=font, anchor="mm", align="center")
        
        # Добавляем рамку
        for i in range(3):
            d.rectangle([i, i, width-i-1, height-i-1], outline=text_color)
        
        # Сохраняем
        filename = f"test_image_local_{int(time.time())}.jpg"
        img.save(filename)
        
        logging.info(f"Тестовое изображение сохранено в файл: {filename}")
        
        # Открываем изображение (только для Windows)
        if os.name == 'nt':
            try:
                os.startfile(filename)
                logging.info("Изображение открыто в просмотрщике")
            except Exception as e:
                logging.error(f"Не удалось открыть изображение: {e}")
        
        # Также возвращаем байтовый поток с изображением
        bytesio = BytesIO()
        img.save(bytesio, format='JPEG')
        bytesio.seek(0)
        
        return {
            'filename': filename,
            'bytes_io': bytesio,
            'width': width,
            'height': height
        }
    except Exception as e:
        logging.error(f"Ошибка создания тестового изображения: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Запрашиваем текст для изображения
    text = input("Введите текст для тестового изображения (или нажмите Enter для использования текста по умолчанию): ")
    if not text:
        text = "Тестовое изображение\nДля проверки бота"
    
    # Создаем изображение
    result = create_test_image(text)
    
    if result:
        print(f"\n✅ Изображение успешно создано и сохранено в файл: {result['filename']}")
        print(f"Размеры: {result['width']}x{result['height']} пикселей")
    else:
        print("\n❌ Не удалось создать изображение")
    
    print("\nПроверьте логи выше для подробной информации.") 