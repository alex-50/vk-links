import networkx as nx
from .SearchSetting import VisualisationSetting

from typing import Dict, Set, List


class GraphVisualisation:
    def __init__(self, config: VisualisationSetting) -> None:
        self.config = config
        self.users_data: Dict[int, Dict] = None
        self.users_connections: Dict[int, List[int]] = None

    def set_data_from_json(
        self, users_data: Dict[str, Dict], users_connections: Dict[str, List[int]]
    ) -> None:
        self.users_data = {int(user_id): users_data[user_id] for user_id in users_data}
        self.users_connections = {
            int(user_id): users_connections[user_id] for user_id in users_connections
        }

    @staticmethod
    def _count_connections_from_b_to_a(
        graph_a: "GraphVisualisation", graph_b: "GraphVisualisation", user_id: int
    ) -> int:

        connections_count = 0

        if user_id in graph_b.users_connections:
            for friend_id in graph_b.users_connections[user_id]:
                if friend_id in graph_a.users_connections:
                    connections_count += 1

        else:
            for a_friend_id in graph_a.users_connections:
                if user_id == a_friend_id:
                    connections_count += 1

        return connections_count

    @staticmethod
    def merge_graphs(
        graph_a: "GraphVisualisation",
        graph_b: "GraphVisualisation",
        name1: str,
        name2: str,
    ) -> None:

        new_graph = GraphVisualisation(graph_a.config)

        users_data = graph_a.users_data
        users_connections = graph_a.users_connections

        for user_id in graph_b.users_data:
            if (
                GraphVisualisation._count_connections_from_b_to_a(
                    graph_a, graph_b, user_id
                )
                > graph_a.config.min_degree_common_connection
            ):
                if user_id not in graph_a.users_connections:
                    users_connections[user_id] = graph_b.users_connections[user_id]
                    for friend_id in users_connections[user_id]:
                        users_data[friend_id] = graph_b.users_data[friend_id]

        new_graph.set_data_from_json(users_data, users_connections)
        new_graph.generate_gexf(
            path=f"{graph_a.config.save_path}{name1} + {name2}(merged)"
        )

    def _count_degree(self, user_id: int, valid_users_from_ends: Set[int]) -> int:
        return len(
            set(
                filter(
                    lambda id: id in self.users_connections,
                    self.users_connections[user_id],
                )
            )
            | set(self.users_connections[user_id]) & valid_users_from_ends
        )

    def generate_gexf(self, path: str = "") -> None:

        graph = nx.Graph()

        all_users_from_ends: Set[int] = set(self.users_data.keys()) - set(
            self.users_connections.keys()
        )
        valid_users_from_ends: Set[int] = set()

        for user_id in all_users_from_ends:
            edges_to = set(
                filter(
                    lambda id: user_id in self.users_connections[id]
                    and id not in self.config.ignore_users_id,
                    self.users_connections,
                )
            )
            if len(edges_to) >= self.config.min_degree:
                valid_users_from_ends.add(user_id)

        valid_users_from_ends -= set(self.config.ignore_users_id)

        ready_nodes: Set[int] = set()

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

                ok = False

                if friend_id in self.users_connections:

                    if (
                        self._count_degree(friend_id, valid_users_from_ends)
                        >= self.config.min_degree
                    ):
                        ok = True
                else:
                    if friend_id in valid_users_from_ends:
                        ok = True

                if ok:
                    if user_id not in ready_nodes:
                        graph.add_node(
                            user_id,
                            label=self.users_data[user_id]["fullname"],
                            **(self.users_data[user_id]),
                        )
                        ready_nodes.add(user_id)

                    if friend_id not in ready_nodes:
                        graph.add_node(
                            friend_id,
                            label=self.users_data[friend_id]["fullname"],
                            **(self.users_data[friend_id]),
                        )
                        ready_nodes.add(friend_id)

                    graph.add_edge(user_id, friend_id)

        nx.write_gexf(
            graph,
            f"{self.config.save_path}{self.config.root_user_ids}.gexf"
            if not path
            else f"{path}.gexf",
        )
        print(f".gexf-file was be saved at {self.config.save_path}")
