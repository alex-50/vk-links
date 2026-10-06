"""
Чтение и запись JSON-файлов.

Все операции выполняются через контекстный менеджер `with`, поэтому
файлы закрываются даже при возникновении исключений.
"""

import json
import os


def load_json(path: str) -> dict:
    """
    Загружает JSON-файл.

    Args:
        path: абсолютный путь к файлу.

    Returns:
        Содержимое файла в виде словаря.

    Raises:
        FileNotFoundError: если файл не существует.
        json.JSONDecodeError: если содержимое файла — не валидный JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")

    with open(path, mode="r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: str) -> None:
    """
    Сохраняет словарь в JSON-файл.

    Кириллица сохраняется как есть (ensure_ascii=False), отступы — 2 пробела
    для читаемости.

    Args:
        data: словарь для сохранения.
        path: абсолютный путь к файлу.
    """
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)