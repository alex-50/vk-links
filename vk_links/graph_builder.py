"""
Построение графа связей и экспорт в формат GEXF.

Строит граф networkx по данным, собранным DataLoader'ом, фильтрует узлы
по минимальной степени и сохраняет результат в GEXF для Gephi.
"""

import copy
import logging

import networkx as nx

from .config import VisualisationSetting
from .paths import ensure_data_dir, user_gexf_path

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Строит граф друзей и сохраняет его в GEXF.

    Attributes:
        config: настройки визуализации.
        users_data: {user_id: {поле: значение}} — данные пользователей.
        users_connections: {user_id: [friend_id, ...]} — списки друзей.
    """

    def __init__(self, config: VisualisationSetting) -> None:
        """
        Инициализирует построитель.

        Args:
            config: настройки визуализации.
        """
        self.config = config
        self.users_data: dict[int, dict] = {}
        self.users_connections: dict[int, list[int]] = {}

    def set_data(self, users_data: dict, users_connections: dict) -> None:
        """
        Загружает данные из JSON, приводя ключи к int.

        Args:
            users_data: {str(user_id): {поле: значение}}.
            users_connections: {str(user_id): [friend_id, ...]}.
        """
        self.users_data = {int(uid): users_data[uid] for uid in users_data}
        self.users_connections = {
            int(uid): users_connections[uid] for uid in users_connections
        }

    def export_gexf(self, path: str = "") -> None:
        """
        Строит граф и сохраняет его в GEXF.

        Алгоритм:
        1. Определяет «концевые» узлы — те, что есть в users_data, но не в
           users_connections. Для них достаточно входящих связей от узлов графа.
        2. Перебирает узлы из users_connections, пропуская те, у которых
           степень меньше min_degree или которые находятся в ignore_users_id.
        3. Для каждого валидного ребра добавляет оба узла и ребро в граф.
        4. Сохраняет граф через networkx.write_gexf.

        Args:
            path: путь к файлу без расширения. Если пусто — используется
                путь vk-links-data/<root_user_id>.gexf.
        """
        graph = nx.Graph()

        all_users_from_ends = set(self.users_data.keys()) - set(
            self.users_connections.keys()
        )
        valid_users_from_ends = self._find_valid_users_from_ends(all_users_from_ends)

        ready_nodes: set[int] = set()

        for user_id in self.users_connections:
            if (
                self._count_degree(user_id, valid_users_from_ends)
                < self.config.min_degree
                or user_id in self.config.ignore_users_id
            ):
                continue

            for friend_id in self.users_connections[user_id]:
                if friend_id in self.config.ignore_users_id:
                    continue

                if not self._is_edge_valid(
                    user_id, friend_id, valid_users_from_ends
                ):
                    continue

                self._add_node_to_graph(graph, user_id, ready_nodes)
                self._add_node_to_graph(graph, friend_id, ready_nodes)
                graph.add_edge(user_id, friend_id)

        ensure_data_dir()
        output_path = path or user_gexf_path(self.config.root_user_id).replace(
            ".gexf", ""
        )
        nx.write_gexf(graph, f"{output_path}.gexf")
        logger.info(f"GEXF сохранён: {output_path}.gexf")

    @staticmethod
    def merge_graphs(
        graph_a: "GraphBuilder",
        graph_b: "GraphBuilder",
        name1: str,
        name2: str,
    ) -> None:
        """
        Объединяет два графа и сохраняет результат в GEXF.

        За основу берётся graph_a. Из graph_b добавляются узлы, у которых
        число общих связей с graph_a строго больше min_degree_common_connection.
        Исходные графы не изменяются — данные копируются через deepcopy.

        Args:
            graph_a: граф-основа.
            graph_b: граф-источник дополнительных узлов.
            name1: имя первого графа (для имени файла).
            name2: имя второго графа.
        """
        new_graph = GraphBuilder(graph_a.config)

        users_data = copy.deepcopy(graph_a.users_data)
        users_connections = copy.deepcopy(graph_a.users_connections)

        for user_id in graph_b.users_data:
            common = GraphBuilder._count_common_connections(graph_a, graph_b, user_id)
            if common > graph_a.config.min_degree_common_connection:
                if user_id not in graph_a.users_connections:
                    users_connections[user_id] = graph_b.users_connections[user_id]
                    for friend_id in users_connections[user_id]:
                        users_data[friend_id] = graph_b.users_data[friend_id]

        new_graph.set_data(users_data, users_connections)

        ensure_data_dir()
        output_path = str(
            user_gexf_path(f"{name1} + {name2}(merged)").replace(".gexf", "")
        )
        new_graph.export_gexf(path=output_path)

    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================

    def _find_valid_users_from_ends(
        self, all_users_from_ends: set[int]
    ) -> set[int]:
        """
        Находит «концевые» узлы, которые должны попасть в граф.

        Узел считается валидным, если у него не меньше min_degree входящих
        связей от узлов из users_connections и он не находится в ignore_users_id.

        Args:
            all_users_from_ends: множество концевых ID.

        Returns:
            Множество ID, прошедших фильтр.
        """
        valid: set[int] = set()

        for user_id in all_users_from_ends:
            edges_to = {
                uid
                for uid in self.users_connections
                if user_id in self.users_connections[uid]
                and uid not in self.config.ignore_users_id
            }
            if len(edges_to) >= self.config.min_degree:
                valid.add(user_id)

        valid -= set(self.config.ignore_users_id)
        return valid

    def _count_degree(self, user_id: int, valid_users_from_ends: set[int]) -> int:
        """
        Считает степень узла с учётом концевых узлов.

        К степени добавляются только те друзья, что есть в users_connections,
        и те, что вошли в valid_users_from_ends.

        Args:
            user_id: ID узла.
            valid_users_from_ends: концевые узлы, прошедшие фильтр.

        Returns:
            Число учтённых связей.
        """
        friends = self.users_connections[user_id]
        friends_in_graph = {f for f in friends if f in self.users_connections}
        friends_at_ends = {f for f in friends if f in valid_users_from_ends}
        return len(friends_in_graph | friends_at_ends)

    def _is_edge_valid(
        self, user_id: int, friend_id: int, valid_users_from_ends: set[int]
    ) -> bool:
        """
        Проверяет, должно ли ребро попасть в граф.

        Ребро валидно, если друг присутствует в users_connections и его степень
        не меньше min_degree, либо если он входит в valid_users_from_ends.

        Args:
            user_id: ID узла-источника.
            friend_id: ID узла-цели.
            valid_users_from_ends: концевые узлы, прошедшие фильтр.

        Returns:
            True, если ребро нужно добавить.
        """
        if friend_id in self.users_connections:
            return (
                self._count_degree(friend_id, valid_users_from_ends)
                >= self.config.min_degree
            )
        return friend_id in valid_users_from_ends

    def _add_node_to_graph(
        self, graph: nx.Graph, user_id: int, ready_nodes: set[int]
    ) -> None:
        """
        Добавляет узел в граф, если он ещё не добавлен.

        Атрибут label устанавливается в полное имя пользователя, остальные
        поля из users_data попадают как атрибуты узла.

        Args:
            graph: граф networkx.
            user_id: ID узла.
            ready_nodes: множество уже добавленных узлов (изменяется на месте).
        """
        if user_id in ready_nodes:
            return

        user = self.users_data[user_id]
        graph.add_node(
            user_id,
            label=user["fullname"],
            **{k: v for k, v in user.items() if k != "fullname"},
        )
        ready_nodes.add(user_id)

    @staticmethod
    def _count_common_connections(
        graph_a: "GraphBuilder", graph_b: "GraphBuilder", user_id: int
    ) -> int:
        """
        Считает число общих связей пользователя из graph_b с graph_a.

        Если пользователь есть в users_connections графа B — считает, сколько
        его друзей есть в users_connections графа A. Если пользователя нет
        в users_connections графа B — проверяет, встречается ли он как друг
        в графе A.

        Args:
            graph_a: первый граф.
            graph_b: второй граф.
            user_id: ID пользователя из graph_b.

        Returns:
            Число общих связей.
        """
        count = 0

        if user_id in graph_b.users_connections:
            for friend_id in graph_b.users_connections[user_id]:
                if friend_id in graph_a.users_connections:
                    count += 1
        else:
            for a_friend_id in graph_a.users_connections:
                if user_id == a_friend_id:
                    count += 1

        return count