from __future__ import annotations

import networkx as nx


class KnowledgeGraph:
    def __init__(self, semantic_layer) -> None:
        self.semantic_layer = semantic_layer

    def build_graph(self):
        graph = nx.DiGraph()

        for project in self.semantic_layer.projects:
            graph.add_node(f"university:{project['university']}", type="University")
            graph.add_node(f"project:{project['id']}", type="PIProject", name=project["project_name"])
            graph.add_edge(f"university:{project['university']}", f"project:{project['id']}", relation="REQUESTS")

            for module_id in project.get("module_ids", []):
                module = next((m for m in self.semantic_layer.modules if m["id"] == module_id), None)
                if not module:
                    continue
                graph.add_node(f"module:{module['id']}", type="ProjectModule", name=module["name"])
                graph.add_edge(f"project:{project['id']}", f"module:{module['id']}", relation="CONTAINS")
                for role in module.get("required_roles", []):
                    graph.add_node(f"role:{role}", type="Role", name=role)
                    graph.add_edge(f"module:{module['id']}", f"role:{role}", relation="ASSIGNED_TO")
                for deliverable in module.get("deliverables", []):
                    graph.add_node(f"deliverable:{deliverable}", type="Deliverable", name=deliverable)
                    graph.add_edge(f"module:{module['id']}", f"deliverable:{deliverable}", relation="DELIVERS")

            for outcome in self.semantic_layer.outcomes:
                graph.add_node(f"outcome:{outcome['id']}", type="Outcome", name=outcome["name"])
                graph.add_edge(f"project:{project['id']}", f"outcome:{outcome['id']}", relation="PRODUCES")

        for module in self.semantic_layer.modules:
            for dep_id in module.get("dependencies", []):
                dep_name = next((m["name"] for m in self.semantic_layer.modules if m["id"] == dep_id), dep_id)
                graph.add_edge(f"module:{module['id']}", f"module:{dep_id}", relation="DEPENDS_ON")
                graph.add_edge(f"module:{dep_id}", f"module:{module['id']}", relation="REQUIRES")

        return graph

    def get_graph_summary(self):
        graph = self.build_graph()
        return {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "node_types": sorted({data.get("type", "unknown") for _, data in graph.nodes(data=True)}),
            "sample_edges": list(graph.edges(data=True))[:8],
        }
