"""
Обёртка над VK API.

Инкапсулирует экземпляр vk.API и предоставляет методы для получения
данных пользователей и их друзей.
"""

import logging

from vk import API
from vk.exceptions import VkAPIError

from .constants import VK_API_VERSION, REQUEST_FIELDS

logger = logging.getLogger(__name__)


class VKClient:
    """
    Клиент для работы с VK API.

    Attributes:
        _api: экземпляр vk.API с настроенным токеном и версией.
    """

    def __init__(self, token: str, api_version: str = VK_API_VERSION) -> None:
        """
        Создаёт клиент VK API.

        Args:
            token: VK API токен.
            api_version: версия VK API.
        """
        self._api = API(access_token=token, v=api_version, timeout=30)

    def get_user(self, user_id: str) -> dict:
        """
        Возвращает данные пользователя по ID или нику.

        Args:
            user_id: ID (например, "id1") или ник (например, "durov").

        Returns:
            Словарь с данными пользователя.

        Raises:
            VkAPIError: если VK API вернул ошибку.
        """
        response = self._api.users.get(user_ids=user_id)[0]
        return response

    def get_friends(self, user_id: int) -> list[dict]:
        """
        Возвращает список друзей пользователя.

        Запрашиваемые поля задаются константой REQUEST_FIELDS.

        Args:
            user_id: ID пользователя.

        Returns:
            Список словарей с данными друзей.

        Raises:
            VkAPIError: если VK API вернул ошибку (например, профиль закрыт).
        """
        response = self._api.friends.get(
            user_id=user_id,
            fields=REQUEST_FIELDS,
        )
        return response["items"]

    def get_full_name(self, user_data: dict) -> str:
        """
        Формирует полное имя пользователя из имени и фамилии.

        Args:
            user_data: данные пользователя из VK API.

        Returns:
            Строка вида "Имя Фамилия".
        """
        return f'{user_data["first_name"]} {user_data["last_name"]}'