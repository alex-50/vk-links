"""
Dataclasses с настройками для разных режимов работы.

- Setting — общие поля;
- ParseSetting — настройки сбора данных;
- VisualisationSetting — настройки визуализации и объединения графов.
"""

from dataclasses import dataclass, field


@dataclass
class Setting:
    """
    Общие настройки, используемые во всех режимах.

    Attributes:
        root_user_id: ID или ник корневого пользователя.
        ignore_users_id: список ID пользователей, которых нужно пропускать.
    """

    root_user_id: str
    ignore_users_id: list[int] = field(default_factory=list)


@dataclass
class ParseSetting(Setting):
    """
    Настройки режима сбора данных.

    Attributes:
        depth: максимальная глубина обхода (1 — только друзья, 2 — друзья друзей).
        crawler_depth_conditions: глубина, до которой применяются условия фильтрации.
        crawler_conditions: словарь с условиями фильтрации.
            Ключ "ok" — оставить пользователя, если он подходит хотя бы под одно условие.
            Ключ "ignore" — исключить пользователя, если он подходит хотя бы под одно условие.
            Если оба ключа пусты, фильтрация не применяется.
    """

    depth: int = 2
    crawler_depth_conditions: int = 2
    crawler_conditions: dict = field(default_factory=lambda: {"ok": [], "ignore": []})

    def check_valid_user(self, vk_user: dict) -> bool:
        """
        Проверяет, проходит ли пользователь условия фильтрации.

        Если заданы условия "ok" — возвращает True только для тех, кто подходит
        хотя бы под одно из них. Иначе, если заданы условия "ignore", отсеивает
        тех, кто подходит хотя бы под одно. Если условий нет — пропускает всех.

        Args:
            vk_user: данные пользователя из VK API.

        Returns:
            True, если пользователь должен быть добавлен в граф.
        """
        ok_conditions = self.crawler_conditions.get("ok", [])
        ignore_conditions = self.crawler_conditions.get("ignore", [])

        if ok_conditions:
            for condition in ok_conditions:
                if self._matches_condition(vk_user, condition):
                    return True
            return False

        if ignore_conditions:
            for condition in ignore_conditions:
                if self._matches_condition(vk_user, condition):
                    return False
            return True

        return True

    @staticmethod
    def _matches_condition(vk_user: dict, condition: dict) -> bool:
        """
        Проверяет соответствие пользователя одному условию.

        Условие — словарь вида {"city": "москва", "schools": "123"}.
        Пользователь подходит, если у него есть все поля из условия
        и значение каждого поля содержит подстроку из условия
        (без учёта регистра).

        Args:
            vk_user: данные пользователя.
            condition: одно условие фильтрации.

        Returns:
            True, если пользователь удовлетворяет условию.
        """
        if not set(condition.keys()) <= set(vk_user.keys()):
            return False

        for key, expected in condition.items():
            actual = str(vk_user.get(key, "")).lower()
            if str(expected).lower() not in actual:
                return False

        return True


@dataclass
class VisualisationSetting(Setting):
    """
    Настройки визуализации и объединения графов.

    Attributes:
        min_degree: минимальная степень узла для попадания в граф.
        min_degree_common_connection: минимальное число общих связей
            для добавления узла при объединении графов.
    """

    min_degree: int = 2
    min_degree_common_connection: int = 1
