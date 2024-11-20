import networkx as nx


class GraphVisualisation:
    def __init__(self, config=None) -> None:
        self.config = config

    def set_data(self, users_data, users_connections):
        self.users_data = {}
        self.users_connections = {}

        for user_id in users_data:
            self.users_data[int(user_id)] = users_data[user_id]

        for user_id in users_connections:
            self.users_connections[int(user_id)] = users_connections[user_id]

    @staticmethod
    def _count_connections_from_b_to_a(graph_a, graph_b, user_id) -> int:

        connections_count = 0

        # собираем кол-во связей родительских узлов графа Б с исходным графом А
        if user_id in graph_b.users_connections:
            for friend_id in graph_b.users_connections[user_id]:
                if friend_id in graph_a.users_connections:
                    connections_count += 1

        else:
            # собираем кол-во ссылок на рассматриваемый узел Б из родительских узлов исходного графа А
            for a_user_id in graph_a.users_connections:
                for a_friend_id in graph_a.users_connections:
                    if user_id == a_friend_id:
                        connections_count += 1

        return connections_count

    @staticmethod
    def merge_graphs(graph_a, graph_b, name1, name2):

        new_graph = GraphVisualisation(graph_a.config)

        users_data = graph_a.users_data
        users_connections = graph_a.users_connections

        for user_id in graph_b.users_data:
            if GraphVisualisation._count_connections_from_b_to_a(graph_a, graph_b,
                                                                 user_id) > graph_a.config.min_degree_common_connection:
                if user_id not in graph_a.users_connections:
                    users_connections[user_id] = graph_b.users_connections[user_id]
                    for friend_id in users_connections[user_id]:
                        users_data[friend_id] = graph_b.users_data[friend_id]

        new_graph.set_data(users_data, users_connections)
        new_graph.generate_gexf(
            path=f"{graph_a.config.save_path}{name1} + {name2}(merged)"
        )

    def _count_degree(self, user_id):

        edges_to = set()

        if user_id in self.users_connections:
            edges_to = set(friend_id for friend_id in self.users_connections[user_id])
        else:
            for tmp_user_id in self.users_connections:
                if user_id in self.users_connections[tmp_user_id]:
                    edges_to.add(tmp_user_id)

        return len(edges_to)

    def generate_gexf(self, path=""):

        graph = nx.Graph()

        for user_id in self.users_connections:

            if len(self.users_connections[user_id]) < self.config.min_degree:
                continue

            graph.add_node(user_id, label=self.users_data[user_id]["fullname"], **(self.users_data[user_id]))

            for friend_id in self.users_connections[user_id]:
                if self._count_degree(friend_id) >= self.config.min_degree:
                    graph.add_node(friend_id, label=self.users_data[friend_id]["fullname"],
                                   **(self.users_data[friend_id]))
                    graph.add_edge(user_id, friend_id)

        nx.write_gexf(graph, f"{self.config.save_path}{self.config.root_user_ids}.gexf" if not path else f"{path}.gexf")
        print(f".gexf-file was be saved")
