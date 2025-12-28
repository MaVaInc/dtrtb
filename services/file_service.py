"""
Сервис для работы с файлами
"""
import hashlib
import uuid
from pathlib import Path
from typing import Optional
from PIL import Image
import aiofiles
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


async def save_uploaded_file(
    file_content: bytes,
    filename: str,
    file_type: str = "file"
) -> Optional[str]:
    """
    Сохраняет загруженный файл и возвращает путь к нему
    
    Args:
        file_content: Содержимое файла
        filename: Имя файла
        file_type: Тип файла ("image" или "file")
    
    Returns:
        Путь к сохраненному файлу или None в случае ошибки
    """
    try:
        # Определяем директорию для сохранения
        if file_type == "image":
            save_dir = config.IMAGES_DIR
            # Проверяем расширение
            ext = Path(filename).suffix.lower()
            if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
                return None
        else:
            save_dir = config.FILES_DIR
            ext = Path(filename).suffix.lower()
            if ext not in config.ALLOWED_FILE_EXTENSIONS:
                return None
        
        # Генерируем уникальное имя файла
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        unique_filename = f"{file_hash}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = save_dir / unique_filename
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Оптимизируем изображение, если это изображение
        if file_type == "image":
            await optimize_image(file_path)
        
        return str(file_path)
    
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


async def optimize_image(image_path: Path, max_size: tuple = (1920, 1920), quality: int = 85):
    """
    Оптимизирует изображение (сжатие и изменение размера)
    
    Args:
        image_path: Путь к изображению
        max_size: Максимальный размер (width, height)
        quality: Качество JPEG (1-100)
    """
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB, если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменяем размер, если нужно
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем с оптимизацией
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
    
    except Exception as e:
        print(f"Error optimizing image: {e}")


async def delete_file(file_path: str) -> bool:
    """
    Удаляет файл
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        True если файл удален, False в противном случае
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def get_file_url(file_path: str) -> str:
    """
    Преобразует локальный путь в URL для доступа через веб-сервер
    
    Args:
        file_path: Локальный путь к файлу
    
    Returns:
        URL файла
    """
    if not file_path:
        return ""
    
    path = Path(file_path)
    if path.is_absolute():
        # Относительный путь от корня uploads
        try:
            relative_path = path.relative_to(config.UPLOADS_DIR)
            return f"{config.WEB_APP_URL}/uploads/{relative_path}"
        except ValueError:
            return ""
    else:
        # Уже относительный путь
        return f"{config.WEB_APP_URL}/{file_path}"

