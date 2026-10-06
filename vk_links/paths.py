"""
Пути к файлам и папкам проекта.

Все пути строятся через os.path.join, поэтому работают на Windows,
Linux и macOS без дополнительных условий.
"""

import os

from .constants import (
    CONFIG_FILENAME,
    CONFIG_EXAMPLE_FILENAME,
    DATA_DIR_NAME,
)

# Корень проекта — папка, содержащая vk_links.py и vk_links/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Путь к конфигу, создаваемому пользователем
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILENAME)

# Путь к шаблону конфига в репозитории
CONFIG_EXAMPLE_PATH = os.path.join(BASE_DIR, CONFIG_EXAMPLE_FILENAME)

# Папка для собранных данных и GEXF-файлов
DATA_DIR = os.path.join(BASE_DIR, DATA_DIR_NAME)


def ensure_data_dir() -> None:
    """Создаёт папку для данных, если она ещё не существует."""
    os.makedirs(DATA_DIR, exist_ok=True)


def user_json_path(user_id: str) -> str:
    """
    Возвращает путь к JSON-файлу с данными пользователя.

    Args:
        user_id: ID или ник пользователя.

    Returns:
        Абсолютный путь к файлу.
    """
    return os.path.join(DATA_DIR, f"{user_id}.json")


def user_gexf_path(user_id: str) -> str:
    """
    Возвращает путь к GEXF-файлу с графом пользователя.

    Args:
        user_id: ID или ник пользователя.

    Returns:
        Абсолютный путь к файлу.
    """
    return os.path.join(DATA_DIR, f"{user_id}.gexf")