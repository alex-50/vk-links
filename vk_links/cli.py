"""
Командный интерфейс vk-links на typer.

Команды:
    config — создать config.json и папку для данных;
    parse  — собрать данные о пользователе;
    visual — экспортировать граф в GEXF;
    merge  — объединить два графа.
"""

import logging
import os

import typer
from vk.exceptions import VkAPIError

from .config import ParseSetting, VisualisationSetting
from .constants import (
    DEFAULT_LOG_LEVEL,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOG_LEVEL_ENV,
)
from .data_loader import DataLoader
from .file_io import load_json, save_json
from .graph_builder import GraphBuilder
from .paths import (
    CONFIG_EXAMPLE_PATH,
    CONFIG_PATH,
    ensure_data_dir,
    user_json_path,
)
from .vk_client import VKClient

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="vk-links",
    help="OSINT-инструмент для анализа графов друзей ВКонтакте.",
    no_args_is_help=True,
)


# ============================================================
# ВСПОМОГАТЕЛЬНОЕ
# ============================================================

def setup_logging(verbose: bool = False) -> None:
    """
    Настраивает корневой логгер.

    Уровень определяется в порядке приоритета:
    1. Флаг --verbose (DEBUG).
    2. Переменная окружения VK_LINKS_LOG_LEVEL.
    3. DEFAULT_LOG_LEVEL (INFO).

    Args:
        verbose: если True, включает уровень DEBUG.
    """
    if verbose:
        level = logging.DEBUG
    else:
        level_name = os.getenv(LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL).upper()
        level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


def load_config() -> dict:
    """
    Загружает config.json.

    Returns:
        Содержимое конфига.

    Raises:
        typer.Exit: если файл не найден, с подсказкой запустить `config`.
    """
    try:
        return load_json(CONFIG_PATH)
    except FileNotFoundError:
        typer.echo(
            f"Конфиг не найден: {CONFIG_PATH}\n"
            f"   Сначала выполните: python vk_links.py config",
            err=True,
        )
        raise typer.Exit(code=1)


def load_token() -> str:
    """
    Возвращает VK API токен из переменной окружения VK_API_TOKEN.

    Returns:
        Токен.

    Raises:
        typer.Exit: если переменная не установлена.
    """
    token = os.getenv("VK_API_TOKEN")
    if not token:
        typer.echo(
            "Переменная окружения VK_API_TOKEN не установлена.\n"
            "   Получите токен: https://vkhost.github.io/\n"
            "   Затем: set VK_API_TOKEN=<ваш_токен> (Windows)\n"
            "   или:   export VK_API_TOKEN=<ваш_токен> (Linux/macOS)",
            err=True,
        )
        raise typer.Exit(code=1)
    return token


def build_parse_setting(config_data: dict, user_id: str) -> ParseSetting:
    """Создаёт ParseSetting из содержимого config.json и user_id."""
    return ParseSetting(
        root_user_id=user_id,
        depth=config_data["depth"],
        crawler_depth_conditions=config_data["crawler_depth_conditions"],
        crawler_conditions=config_data["crawler_conditions"],
        ignore_users_id=config_data["ignore_users_id"],
    )


def build_visual_setting(config_data: dict, user_id: str) -> VisualisationSetting:
    """Создаёт VisualisationSetting из содержимого config.json и user_id."""
    return VisualisationSetting(
        root_user_id=user_id,
        min_degree=config_data["min_degree"],
        min_degree_common_connection=config_data["min_degree_common_connection"],
        ignore_users_id=config_data["ignore_users_id"],
    )


# ============================================================
# КОМАНДЫ
# ============================================================

@app.command()
def config(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """
    Создаёт config.json и папку для данных.

    Если файл config.json уже существует, он будет перезаписан шаблоном
    config.example.json.
    """
    setup_logging(verbose)

    ensure_data_dir()
    logger.info(f"Папка для данных: {os.path.dirname(user_json_path('dummy'))}")

    if os.path.exists(CONFIG_EXAMPLE_PATH):
        example = load_json(CONFIG_EXAMPLE_PATH)
        save_json(example, CONFIG_PATH)
        typer.echo(f" Создан конфиг: {CONFIG_PATH}")
    else:
        default_config = {
            "depth": 2,
            "min_degree": 2,
            "crawler_depth_conditions": 2,
            "crawler_conditions": {"ok": [], "ignore": []},
            "ignore_users_id": [],
            "min_degree_common_connection": 1,
        }
        save_json(default_config, CONFIG_PATH)
        typer.echo(f" Создан конфиг по умолчанию: {CONFIG_PATH}")


@app.command()
def parse(
    user_id: str = typer.Argument(..., help="ID или ник пользователя (durov или id1)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """
    Собирает данные о пользователе и его друзьях.

    Результат сохраняется в vk-links-data/<user_id>.json.
    """
    setup_logging(verbose)

    config_data = load_config()
    token = load_token()
    setting = build_parse_setting(config_data, user_id)

    try:
        client = VKClient(token)
        loader = DataLoader(client, setting)
        loader.load()
        loader.save()
    except VkAPIError as e:
        typer.echo(f" Ошибка VK API: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Неожиданная ошибка")
        typer.echo(f" Ошибка: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f" Данные собраны: vk-links-data/{user_id}.json")


@app.command()
def visual(
    user_id: str = typer.Argument(..., help="ID или ник пользователя"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """
    Строит граф и экспортирует его в GEXF.

    Требует, чтобы данные уже были собраны командой parse.
    Результат: vk-links-data/<user_id>.gexf.
    """
    setup_logging(verbose)

    config_data = load_config()
    setting = build_visual_setting(config_data, user_id)

    try:
        data = load_json(user_json_path(user_id))
    except FileNotFoundError:
        typer.echo(
            f" Данные не найдены: vk-links-data/{user_id}.json\n"
            f"   Сначала выполните: python vk_links.py parse {user_id}",
            err=True,
        )
        raise typer.Exit(code=1)

    builder = GraphBuilder(setting)
    builder.set_data(data["data"], data["connections"])
    builder.export_gexf()

    typer.echo(f" Граф сохранён: vk-links-data/{user_id}.gexf")


@app.command()
def merge(
    user_id1: str = typer.Argument(..., help="Первый пользователь (основа)"),
    user_id2: str = typer.Argument(..., help="Второй пользователь (добавляем)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """
    Объединяет два графа в один и сохраняет результат в GEXF.

    Требует, чтобы данные обоих пользователей были собраны командой parse.
    Результат: vk-links-data/<user_id1> + <user_id2>(merged).gexf.
    """
    setup_logging(verbose)

    config_data = load_config()

    try:
        data1 = load_json(user_json_path(user_id1))
        data2 = load_json(user_json_path(user_id2))
    except FileNotFoundError as e:
        typer.echo(
            f" Данные не найдены: {e}\n"
            f"   Сначала выполните parse для обоих пользователей.",
            err=True,
        )
        raise typer.Exit(code=1)

    setting = build_visual_setting(config_data, user_id1)

    builder1 = GraphBuilder(setting)
    builder1.set_data(data1["data"], data1["connections"])

    builder2 = GraphBuilder(setting)
    builder2.set_data(data2["data"], data2["connections"])

    GraphBuilder.merge_graphs(builder1, builder2, user_id1, user_id2)

    typer.echo(f" Объединённый граф сохранён.")


