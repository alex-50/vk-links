"""
Пакет vk-links — инструменты для анализа графа друзей ВКонтакте.

Модули пакета:
- vk_client     — обёртка над VK API;
- data_loader   — рекурсивный сбор данных о пользователях и связях;
- graph_builder — построение графа и экспорт в GEXF;
- config        — dataclasses настроек;
- cli           — командный интерфейс на typer;
- paths         — пути к файлам проекта;
- file_io       — чтение и запись JSON;
- constants     — общие константы.
"""

__author__ = "Alexander Baranov"
