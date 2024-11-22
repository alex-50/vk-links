from dataclasses import dataclass


@dataclass
class Setting:
    root_user_ids: str  # страница корневого пользователя
    save_path: str  # путь до папки с сохранением данных


@dataclass
class ParseSetting(Setting):
    depth: int  # глубина захода
    crawler_depth_conditions: int  # глубина до которой надо проверять условие
    request_fields: list[str]  # поля для запроса
    crawler_conditions: list[dict]  # список условий
    ignore_users_id: list[int]  # игнорируемы пользователи

    def check_valid_user(self, vk_json_user) -> bool:

        if self.crawler_conditions["ok"]:
            for condition in self.crawler_conditions["ok"]:
                if set(condition.keys()) <= set(vk_json_user.keys()):
                    for key in condition:

                        if condition[key].lower() not in vk_json_user[key].lower():
                            print(f"Condition \"{vk_json_user['fullname']}\" - failed")
                            break
                    else:
                        print(f"Condition \"{vk_json_user['fullname']}\" - success")
                        return True
            return False

        if self.crawler_conditions["ignore"]:
            for condition in self.crawler_conditions["ignore"]:
                if set(condition.keys()) <= set(vk_json_user.keys()):
                    for key in condition:
                        if condition[key].lower() in vk_json_user[key].lower():
                            print(f"Condition \"{vk_json_user['fullname']}\" - failed")
                            return False
            print(f"Condition \"{vk_json_user['fullname']}\" - success")
            return True

        return True


@dataclass
class VisualisationSetting(Setting):
    min_degree: int  # минимальная степень вершины
    min_degree_common_connection: int  # минимальное количество связей между груфами (для слияния)
