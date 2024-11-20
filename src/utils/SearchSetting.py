from dataclasses import dataclass


@dataclass
class SearchSetting:
    depth: int  # глубина захода
    root_user_ids: str  # корневой пользователь
    crawler_depth_conditions: int  # глубина до которой надо проверять условие
    min_degree: int  # минимальная степень вершины
    request_fields: list[str]  # поля для запроса
    crawler_conditions: list[dict]  # список условий
    ignore_users_id: list[int]  # игнорируемы пользователи
    min_degree_common_connection: int  # минимальное количество связей между груфами (для слияния)
    save_path: str  # путь к папке для сохранения данных

    def check_valid_user(self, vk_json_user) -> bool:

        if self.crawler_conditions["ok"]:
            for condition in self.crawler_conditions["ok"]:
                if set(condition.keys()) <= set(vk_json_user.keys()):
                    for key in condition:

                        if condition[key].lower() not in vk_json_user[key].lower():
                            break
                    else:
                        print(f"Condition f{vk_json_user['fullname']} - success")
                        return True
            return False

        if self.crawler_conditions["ignore"]:
            for condition in self.crawler_conditions["ignore"]:
                if set(condition.keys()) <= set(vk_json_user.keys()):
                    for key in condition:
                        if condition[key].lower() in vk_json_user[key].lower():
                            return False
            print(f"Condition f{vk_json_user['fullname']} - success")
            return True

        return True
