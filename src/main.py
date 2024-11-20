import os
import json
import pathlib
import argparse
import platform

from utils.SearchSetting import SearchSetting
from utils.VKDataLoader import DataLoader
from utils.GraphVisualisation import GraphVisualisation


class ErrorNotFoundNecessaryDependenciesOfApp(Exception):
    pass


def load_config_file() -> dict:
    try:
        config_data = json.loads(
            open("config.json", mode="r", encoding="utf-8").read()
        )
    except:
        raise ErrorNotFoundNecessaryDependenciesOfApp(
            "config.json not found - use script with param: m=config (config generation)")

    return config_data


def load_token() -> str:
    if os_env_vk_api_token := os.getenv('VK_API_TOKEN'):
        return os_env_vk_api_token
    else:
        raise ErrorNotFoundNecessaryDependenciesOfApp("<VK_API_TOKEN> not be found in system variables")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--mode", required=True)
    parser.add_argument("-u", "--userids")
    parser.add_argument("-u2", "--userids2")

    args = parser.parse_args()

    if args.mode == "config":

        sep = "\\" if platform.system() == "Windows" else "/"
        save_path = str(pathlib.Path.home()) + sep + "vk-links-data" + sep

        if not os.path.exists(save_path):
            os.mkdir(save_path)

        with open("config.json", mode="w", encoding="utf-8") as config_file:
            json.dump(
                {
                    "depth": 2,
                    "min_degree": 2,
                    "crawler_depth_conditions": 2,
                    "request_fields": [
                        "city",
                        "school",
                        "university",
                        "work",
                        "home_town",
                    ],
                    "crawler_conditions": {"ok": [], "ignore": []},
                    "ignore_users_id": [],
                    "min_degree_common_connection": 1,
                    "save_path": save_path
                },
                config_file
            )

    elif args.mode in {"visual", "mining", "merge"}:

        config_data = load_config_file()

        config = SearchSetting(
            root_user_ids=args.userids,
            depth=config_data["depth"],
            min_degree=config_data["min_degree"],
            crawler_depth_conditions=config_data["crawler_depth_conditions"],
            request_fields=config_data["request_fields"],
            crawler_conditions=config_data["crawler_conditions"],
            ignore_users_id=config_data["ignore_users_id"],
            min_degree_common_connection=config_data["min_degree_common_connection"],
            save_path=config_data["save_path"]
        )

        match args.mode:

            case "mining":

                TOKEN = load_token()
                loader = DataLoader(config, TOKEN)
                loader.save_data()

            case "visual":
                try:
                    js_users_data = json.loads(
                        open(f"{config.save_path}{args.userids}.json", mode="r", encoding="utf-8").read()
                    )
                    visualisation = GraphVisualisation(config)
                    visualisation.set_data(js_users_data["data"], js_users_data["connections"])
                    visualisation.generate_gexf()

                except FileNotFoundError:
                    print(f"{config.root_user_ids}.json not be found {config.save_path}")

            case "merge":

                try:
                    js_users_data_1 = json.loads(
                        open(f"{config.save_path}{args.userids}.json", mode="r", encoding="utf-8").read()
                    )
                    js_users_data_2 = json.loads(
                        open(f"{config.save_path}{args.userids2}.json", mode="r", encoding="utf-8").read()
                    )

                    visualisation1 = GraphVisualisation(config)
                    visualisation2 = GraphVisualisation(config)

                    visualisation1.set_data(js_users_data_1["data"], js_users_data_1["connections"])
                    visualisation2.set_data(js_users_data_2["data"], js_users_data_2["connections"])

                    GraphVisualisation.merge_graphs(visualisation1, visualisation2, args.userids, args.userids2)

                except FileNotFoundError:
                    print(f"{args.userids}.json or {args.userids2}.json not be found in {config.save_path}")


if __name__ == "__main__":
    main()
