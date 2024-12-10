import time
import json

from vk import API
from .SearchSetting import ParseSetting


class DataLoader:
    def __init__(
        self, config: ParseSetting, token: str, api_version: str = "5.92"
    ) -> None:
        self._api = API(access_token=token, v=api_version)
        self.config = config

        self.users_data = {}
        self.users_connections = {}

        self._need_params = list(
            {
                "city",
                "home_town",
                "status",
                "sex",
                "site",
                "about",
                "domain",
                "occupation",
                "schools",
                "universities",
                "home_town",
            }
            & set(self.config.request_fields)
        )

        root = self._api.users.get(user_ids=config.root_user_ids)[0]

        root_id = root["id"]
        self.users_data[root_id] = {}
        self.users_data[root_id][
            "fullname"
        ] = f'{root["first_name"]} {root["last_name"]}'

        self._data_load(root_id)

        print("Accounts found: ", len(self.users_data.keys()))

    def save_data(self) -> None:

        print(
            f"Users data save in {self.config.root_user_ids}.json at {self.config.save_path}"
        )

        with open(
            f"{self.config.save_path}{self.config.root_user_ids}.json",
            mode="w",
            encoding="utf-8",
        ) as user_datafile:
            json.dump(
                {
                    "data": self.users_data,
                    "connections": self.users_connections,
                },
                user_datafile,
            )

    def _data_load(self, user_id: int, current_depth: int = 1) -> None:

        if current_depth > self.config.depth:
            return None

        print(
            f'{"-----------" * current_depth}>{self.users_data[user_id]["fullname"]} ({user_id})  x{current_depth}'
        )

        time.sleep(0.25)

        self.users_connections[user_id] = []

        friends = self._api.friends.get(user_id=user_id, fields=self._need_params)

        for friend in friends["items"]:
            if friend["id"] in self.config.ignore_users_id:
                continue

            current_user_js_data = {
                "fullname": f'{friend["first_name"]} {friend["last_name"]}',
            }

            for param in ("status", "site", "about", "domain", "home_town"):
                if param in self.config.request_fields and param in friend:
                    current_user_js_data[param] = friend.get(param, "")

            if "city" in self.config.request_fields and "city" in friend:
                current_user_js_data["city"] = friend["city"]["title"]

            if "sex" in self.config.request_fields:
                current_user_js_data["sex"] = (
                    ("male" if friend["sex"] == 2 else "female")
                    if friend["sex"]
                    else "undef"
                )

            if "occupation" in self.config.request_fields and "occupation" in friend:
                current_user_js_data[
                    f'{friend["occupation"]["type"]}(occupation)'
                ] = friend["occupation"]["name"]

            for param in ("schools", "universities"):
                if param in self.config.request_fields and param in friend:
                    current_user_js_data[param] = "; ".join(
                        edu_org["name"] for edu_org in friend[param]
                    )

            friend_is_valid = True

            if self.config.crawler_depth_conditions >= current_depth:
                if not self.config.check_valid_user(current_user_js_data):
                    friend_is_valid = False

            if friend_is_valid:

                self.users_connections[user_id].append(friend["id"])
                self.users_data[friend["id"]] = current_user_js_data

                if (
                    friend["can_access_closed"]
                    and "deactivated" not in friend
                    and friend["id"] not in self.config.ignore_users_id
                ):
                    self._data_load(friend["id"], current_depth + 1)
