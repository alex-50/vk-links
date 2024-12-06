import os
import json
import argparse
import platform

from src.SearchSetting import ParseSetting, VisualisationSetting
from src.VKDataLoader import DataLoader
from src.GraphVisualisation import GraphVisualisation


class ErrorNotFoundNecessaryDependenciesOfApp(Exception):
    pass


DIR_SEP = "\\" if platform.system() == "Windows" else "/"
DIR_WITH_EXEC_SCRIPT = os.path.dirname(os.path.realpath(__file__))


def load_config_file() -> dict:
    try:
        config_data = json.loads(
            open(
                DIR_WITH_EXEC_SCRIPT + DIR_SEP + "config.json",
                mode="r",
                encoding="utf-8",
            ).read()
        )
    except Exception:
        raise ErrorNotFoundNecessaryDependenciesOfApp(
            f'config.json not found in "{DIR_WITH_EXEC_SCRIPT}" - use script with param: m=config (config generation)'
        )

    return config_data


def load_token() -> str:
    if os_env_vk_api_token := os.getenv("VK_API_TOKEN"):
        return os_env_vk_api_token
    else:
        raise ErrorNotFoundNecessaryDependenciesOfApp(
            "<VK_API_TOKEN> not be found in system variables"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--mode", required=True)
    parser.add_argument("-u", "--userids")
    parser.add_argument("-u2", "--userids2")

    args = parser.parse_args()

    if args.mode == "config":

        save_path = DIR_WITH_EXEC_SCRIPT + DIR_SEP + "vk-links-data" + DIR_SEP

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
                    "save_path": save_path,
                },
                config_file,
            )

    elif args.mode in {"visual", "parse", "merge"}:

        config_data = load_config_file()

        if args.mode == "parse":
            config = ParseSetting(
                root_user_ids=args.userids,
                save_path=config_data["save_path"],
                depth=config_data["depth"],
                crawler_depth_conditions=config_data["crawler_depth_conditions"],
                request_fields=config_data["request_fields"],
                crawler_conditions=config_data["crawler_conditions"],
                ignore_users_id=config_data["ignore_users_id"],
            )
        else:
            config = VisualisationSetting(
                root_user_ids=args.userids,
                save_path=config_data["save_path"],
                min_degree=config_data["min_degree"],
                min_degree_common_connection=config_data[
                    "min_degree_common_connection"
                ],
                ignore_users_id=config_data["ignore_users_id"],
            )

        match args.mode:

            case "parse":

                TOKEN = load_token()
                loader = DataLoader(config, TOKEN)
                loader.save_data()

            case "visual":
                try:
                    js_users_data = json.loads(
                        open(
                            f"{config.save_path}{args.userids}.json",
                            mode="r",
                            encoding="utf-8",
                        ).read()
                    )
                    visualisation = GraphVisualisation(config)
                    visualisation.set_data_from_json(
                        js_users_data["data"], js_users_data["connections"]
                    )
                    visualisation.generate_gexf()

                except FileNotFoundError:
                    print(
                        f"{config.root_user_ids}.json not be found {config.save_path}"
                    )

            case "merge":

                try:
                    js_users_data_1 = json.loads(
                        open(
                            f"{config.save_path}{args.userids}.json",
                            mode="r",
                            encoding="utf-8",
                        ).read()
                    )
                    js_users_data_2 = json.loads(
                        open(
                            f"{config.save_path}{args.userids2}.json",
                            mode="r",
                            encoding="utf-8",
                        ).read()
                    )

                    visualisation1 = GraphVisualisation(config)
                    visualisation2 = GraphVisualisation(config)

                    visualisation1.set_data_from_json(
                        js_users_data_1["data"], js_users_data_1["connections"]
                    )
                    visualisation2.set_data_from_json(
                        js_users_data_2["data"], js_users_data_2["connections"]
                    )

                    GraphVisualisation.merge_graphs(
                        visualisation1, visualisation2, args.userids, args.userids2
                    )

                except FileNotFoundError:
                    print(
                        f"{args.userids}.json or {args.userids2}.json not be found in {config.save_path}"
                    )


if __name__ == "__main__":
    main()
