"""
Рекурсивный сбор данных о пользователе и его связях.

Обходит граф друзей в глубину до заданного предела, применяет фильтры
и сохраняет результат в JSON-файл.
"""

import logging
import time

from vk.exceptions import VkAPIError

from .config import ParseSetting
from .constants import REQUEST_DELAY, REQUEST_FIELDS
from .file_io import save_json
from .paths import ensure_data_dir, user_json_path
from .vk_client import VKClient

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Собирает данные о пользователях и связях между ними.

    Attributes:
        client: клиент VK API.
        config: настройки сбора.
        users_data: {user_id: {поле: значение}} — данные пользователей.
        users_connections: {user_id: [friend_id, ...]} — списки друзей.
    """

    def __init__(self, client: VKClient, config: ParseSetting) -> None:
        """
        Инициализирует загрузчик.

        Args:
            client: клиент VK API.
            config: настройки сбора данных.
        """
        self.client = client
        self.config = config
        self.users_data: dict[int, dict] = {}
        self.users_connections: dict[int, list[int]] = {}

    def load(self) -> None:
        """
        Запускает сбор данных начиная с корневого пользователя.

        Сначала загружает данные корня, затем — его друзей и так далее
        до глубины, указанной в config.depth.
        """
        root = self.client.get_user(self.config.root_user_id)
        root_id = root["id"]

        self.users_data[root_id] = {
            "fullname": self.client.get_full_name(root),
        }

        self._load_user(root_id, current_depth=1)

        logger.info(f"Всего собрано аккаунтов: {len(self.users_data)}")

    def save(self) -> None:
        """
        Сохраняет собранные данные в JSON-файл.

        Файл: vk-links-data/<root_user_id>.json.
        В файл записываются два ключа: "data" и "connections".
        """
        ensure_data_dir()
        path = user_json_path(self.config.root_user_id)
        save_json(
            {"data": self.users_data, "connections": self.users_connections},
            path,
        )
        logger.info(f"Данные сохранены в {path}")

    def _load_user(self, user_id: int, current_depth: int = 1) -> None:
        """
        Рекурсивно загружает друзей пользователя.

        Для каждого друга:
        - пропускает, если его ID в ignore_users_id;
        - извлекает нужные поля через _extract_friend_data;
        - применяет фильтр, если глубина не превышает crawler_depth_conditions;
        - добавляет в граф и рекурсивно обходит его друзей, если профиль открыт.

        Args:
            user_id: ID текущего пользователя.
            current_depth: текущая глубина обхода (1 — корень).
        """
        if current_depth > self.config.depth:
            return

        fullname = self.users_data[user_id]["fullname"]
        indent = "  " * current_depth
        logger.info(f"{indent}→ {fullname} ({user_id}) [глубина {current_depth}]")

        time.sleep(REQUEST_DELAY)

        self.users_connections[user_id] = []

        try:
            friends = self.client.get_friends(user_id)
        except VkAPIError as e:
            logger.warning(f"VK API error для {user_id}: {e}")
            return

        for friend in friends:
            friend_id = friend["id"]

            if friend_id in self.config.ignore_users_id:
                continue

            friend_data = self._extract_friend_data(friend)

            friend_is_valid = True
            if self.config.crawler_depth_conditions >= current_depth:
                if not self.config.check_valid_user(friend_data):
                    friend_is_valid = False

            if not friend_is_valid:
                continue

            self.users_connections[user_id].append(friend_id)
            self.users_data[friend_id] = friend_data

            if (
                    friend.get("can_access_closed")
                    and "deactivated" not in friend
                    and friend_id not in self.config.ignore_users_id
            ):
                self._load_user(friend_id, current_depth + 1)

    def _extract_friend_data(self, friend: dict) -> dict:
        """
        Извлекает из данных VK API нужные поля в плоский словарь.

        Обрабатывает поля, требующие преобразования:
        city (объект → название), sex (число → строка),
        occupation (объект → название), schools и universities (списки → строки).

        Args:
            friend: данные друга из VK API.

        Returns:
            Словарь с полями, определёнными в REQUEST_FIELDS, и полем "fullname".
        """
        data = {
            "fullname": self.client.get_full_name(friend),
        }

        for param in ("status", "site", "about", "domain", "home_town"):
            if param in REQUEST_FIELDS and param in friend:
                data[param] = friend.get(param, "")

        if "city" in REQUEST_FIELDS and "city" in friend:
            data["city"] = friend["city"]["title"]

        if "sex" in REQUEST_FIELDS:
            sex = friend.get("sex", 0)
            if sex == 2:
                data["sex"] = "male"
            elif sex == 1:
                data["sex"] = "female"
            else:
                data["sex"] = "undef"

        if "occupation" in REQUEST_FIELDS and "occupation" in friend:
            occ = friend["occupation"]
            data[f'{occ["type"]}(occupation)'] = occ["name"]

        for param in ("schools", "universities"):
            if param in REQUEST_FIELDS and param in friend:
                data[param] = "; ".join(
                    edu["name"] for edu in friend[param]
                )

        return data