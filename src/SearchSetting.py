from dataclasses import dataclass


@dataclass
class Setting:
    root_user_ids: str  # the root user's page
    save_path: str  # the path to the folder where the data is saved
    ignore_users_id: list[int]  # ignored users


@dataclass
class ParseSetting(Setting):
    depth: int  # depth of entry
    crawler_depth_conditions: int  # the depth to which the condition should be checked
    request_fields: set[str]  # fields for the request
    crawler_conditions: list[dict]  # list of conditions

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
    min_degree: int  # the minimum degree of the vertex
    min_degree_common_connection: int  # minimum number of connections between graphs (for merging)
