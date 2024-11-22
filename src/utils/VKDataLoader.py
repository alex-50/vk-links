import time
import json

from vk import API, exceptions
from utils.SearchSetting import ParseSetting


class DataLoader:
    def __init__(
            self, config: ParseSetting, token: str, api_version="5.92"
    ) -> None:
        self._api = API(access_token=token, v=api_version)
        self.config = config

        self.users_data = {}
        self.users_connections = {}

        self._need_params = []

        if (
                "school" in config.request_fields
                or "university" in config.request_fields
                or "work" in config.request_fields
        ):
            self._need_params.append("occupation")

        for param in ("city", "home_town", "status"):
            if param in config.request_fields:
                self._need_params.append(param)

        root = self._api.users.get(user_ids=config.root_user_ids)[0]
        self.root_id = root["id"]

        self.users_data[self.root_id] = {}
        self.users_data[self.root_id]["fullname"] = f'{root["first_name"]} {root["last_name"]}'

        self._data_load(self.root_id)

        print("Find accounts: ", len(self.users_data.keys()))

    def save_data(self):

        print(f"Users data save in {self.config.root_user_ids}.json")

        with open(
                f"{self.config.save_path}{self.config.root_user_ids}.json", mode="w", encoding="utf-8"
        ) as user_datafile:
            json.dump(
                {
                    "data": self.users_data,
                    "connections": self.users_connections,
                },
                user_datafile
            )

    def _data_load(self, user_id, current_depth=1) -> None:

        if current_depth > self.config.depth:
            return None

        print(f'{"-----------" * current_depth}>{self.users_data[user_id]["fullname"]} ({user_id})  x{current_depth}')

        time.sleep(0.25)

        self.users_connections[user_id] = []

        friends = self._api.friends.get(
            user_id=user_id, fields=self._need_params
        )

        for friend in friends["items"]:
            if friend["id"] in self.config.ignore_users_id:
                continue

            current_user_js_data = {
                "fullname": f'{friend["first_name"]} {friend["last_name"]}',
            }

            if (
                    "city" in self.config.request_fields
                    and "city" in friend.keys()
            ):
                current_user_js_data["city"] = friend["city"]["title"]

            if "status" in self.config.request_fields:
                current_user_js_data["status"] = friend.get("status", "")

            if (
                    "school" in self.config.request_fields
                    or "university" in self.config.request_fields
                    or "work" in self.config.request_fields
            ) and "occupation" in friend.keys():
                current_user_js_data[friend["occupation"]["type"]] = friend[
                    "occupation"
                ]["name"]

            friend_is_valid = True

            if self.config.crawler_depth_conditions >= current_depth:
                if not self.config.check_valid_user(current_user_js_data):
                    friend_is_valid = False

            if friend_is_valid:
                current_user_js_data["fullname"] = f'{friend["first_name"]} {friend["last_name"]}'

                self.users_connections[user_id].append(friend["id"])
                self.users_data[friend["id"]] = current_user_js_data

                if (friend["can_access_closed"] and "deactivated" not in friend and
                        friend["id"] not in self.config.ignore_users_id):
                    self._data_load(friend["id"], current_depth + 1)
