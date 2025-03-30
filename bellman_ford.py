import networkx as nx

def bellman_ford(graph, source):
    distances = {node: float('infinity') for node in graph.nodes()}
    predecessors = {node: None for node in graph.nodes()}
    distances[source] = 0
    
    for _ in range(len(graph.nodes()) - 1):
        for u, v, weight in graph.edges(data='weight', default=1):
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                predecessors[v] = u
    
    for u, v, weight in graph.edges(data='weight', default=1):
        if distances[u] + weight < distances[v]:
            raise ValueError("Graph contains negative weight cycle")
            
    return distances, predecessors

def get_shortest_path(predecessors, source, target):
    path = []
    current = target
    
    while current is not None:
        path.append(current)
        current = predecessors[current]
    
    path.reverse()
    return path if path[0] == source else [] 