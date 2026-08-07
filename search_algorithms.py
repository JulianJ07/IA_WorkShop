import heapq
from itertools import count

graph = {
    "A": [("B", 2), ("C", 1)],
    "B": [("D", 2), ("E", 1)],
    "C": [("E", 3)],
    "D": [("H", 1)],
    "E": [("H", 2)],
    "H": []
}

start = "A"
goal = "H"

# Heuristica del documento guia. No es admisible ni consistente:
# check_heuristic() reporta las violaciones al ejecutar.
heuristic = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 2,
    "E": 1,
    "H": 0
}

class Node:
    def __init__(self, state, parent=None, cost=0):
        self.state = state
        self.parent = parent
        self.cost = cost

    # Necesario si dos entradas de la cola comparten prioridad y contador.
    def __lt__(self, other):
        return self.cost < other.cost

    def __repr__(self):
        return f"{self.state}(g={self.cost})"

def reconstruct_path(node):
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return list(reversed(path))

def neighbors(graph, state):
    """Vecinos de un nodo. Lista vacia si aparece solo como destino."""
    return graph.get(state, [])

def validate(graph, start, goal):
    if start not in graph:
        raise ValueError(f"El nodo inicial '{start}' no existe en el grafo.")
    if goal not in graph:
        raise ValueError(f"El nodo meta '{goal}' no existe en el grafo.")

class StackFrontier:
    def __init__(self):
        self.frontier = []

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("La frontier está vacía.")
        return self.frontier.pop()

    def states(self):
        return [node.state for node in self.frontier]

class QueueFrontier(StackFrontier):
    def remove(self):
        if self.empty():
            raise Exception("La frontier está vacía.")
        return self.frontier.pop(0)

class PriorityFrontier:
    def __init__(self):
        self.heap = []
        self.counter = count()

    def add(self, node, priority):
        # El contador desempata prioridades iguales y mantiene orden FIFO.
        heapq.heappush(self.heap, (priority, next(self.counter), node))

    def contains_state(self, state):
        return any(node.state == state for _, _, node in self.heap)

    def empty(self):
        return len(self.heap) == 0

    def remove(self):
        if self.empty():
            raise Exception("La frontier está vacía.")
        priority, _, node = heapq.heappop(self.heap)
        return node, priority

    def states(self):
        return [node.state for _, _, node in self.heap]

def depth_first_search(graph, start, goal, verbose=False):
    validate(graph, start, goal)
    frontier = StackFrontier()
    frontier.add(Node(start))
    explored = set()
    expansion_order = []

    while not frontier.empty():
        node = frontier.remove()
        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo: {node.state}")
            print(f"Frontier tras extraerlo: {frontier.states()}")

        if node.state == goal:
            return {
                "path": reconstruct_path(node),
                "expansion_order": expansion_order,
                "cost": node.cost
            }

        explored.add(node.state)

        for child_state, edge_cost in neighbors(graph, node.state):
            if (
                child_state not in explored
                and not frontier.contains_state(child_state)
            ):
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost
                )
                frontier.add(child)

        if verbose:
            print(f"Frontier después de expandir: {frontier.states()}")
            print("-" * 45)

    return None

def breadth_first_search(graph, start, goal, verbose=False):
    validate(graph, start, goal)
    frontier = QueueFrontier()
    frontier.add(Node(start))
    explored = set()
    expansion_order = []

    while not frontier.empty():
        node = frontier.remove()
        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo: {node.state} (g={node.cost})")

        if node.state == goal:
            return {
                "path": reconstruct_path(node),
                "expansion_order": expansion_order,
                "cost": node.cost
            }

        explored.add(node.state)

        for child_state, edge_cost in neighbors(graph, node.state):
            if (
                child_state not in explored
                and not frontier.contains_state(child_state)
            ):
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost
                )
                frontier.add(child)

    return None

def uniform_cost_search(graph, start, goal, verbose=False):
    validate(graph, start, goal)
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=0)
    best_cost = {start: 0}
    expansion_order = []

    while not frontier.empty():
        node, _ = frontier.remove()

        # Entrada obsoleta: ya se encontro un camino mas barato a ese estado.
        if node.cost != best_cost.get(node.state):
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: g={node.cost}")

        if node.state == goal:
            return {
                "path": reconstruct_path(node),
                "expansion_order": expansion_order,
                "cost": node.cost
            }

        for child_state, edge_cost in neighbors(graph, node.state):
            new_cost = node.cost + edge_cost

            if new_cost < best_cost.get(child_state, float("inf")):
                best_cost[child_state] = new_cost
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=new_cost
                )
                frontier.add(child, priority=new_cost)

    return None

def greedy_best_first_search(graph, heuristic, start, goal, verbose=False):
    validate(graph, start, goal)
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=heuristic.get(start, 0))
    explored = set()
    expansion_order = []

    while not frontier.empty():
        node, _ = frontier.remove()

        if node.state in explored:
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: h={heuristic.get(node.state, 0)}")

        if node.state == goal:
            return {
                "path": reconstruct_path(node),
                "expansion_order": expansion_order,
                "cost": node.cost
            }

        explored.add(node.state)

        for child_state, edge_cost in neighbors(graph, node.state):
            if child_state not in explored:
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost
                )
                frontier.add(child, priority=heuristic.get(child_state, 0))

    return None

def a_star_search(graph, heuristic, start, goal, verbose=False):
    validate(graph, start, goal)
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=heuristic.get(start, 0))
    best_cost = {start: 0}
    expansion_order = []

    while not frontier.empty():
        node, priority = frontier.remove()

        if node.cost != best_cost.get(node.state):
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: g={node.cost}, f={priority}")

        if node.state == goal:
            return {
                "path": reconstruct_path(node),
                "expansion_order": expansion_order,
                "cost": node.cost
            }

        for child_state, edge_cost in neighbors(graph, node.state):
            new_cost = node.cost + edge_cost

            # Al reabrir con g menor, A* se recupera de heuristicas inconsistentes.
            if new_cost < best_cost.get(child_state, float("inf")):
                best_cost[child_state] = new_cost
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=new_cost
                )
                f_cost = new_cost + heuristic.get(child_state, 0)
                frontier.add(child, priority=f_cost)

    return None

def true_costs(graph, goal):
    """Costo real minimo de cada nodo a la meta: Dijkstra sobre el grafo invertido."""
    reverse = {}
    for u, edges in graph.items():
        reverse.setdefault(u, [])
        for v, w in edges:
            reverse.setdefault(v, []).append((u, w))

    dist = {n: float("inf") for n in reverse}
    dist[goal] = 0
    heap = [(0, goal)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for parent, w in reverse[u]:
            if d + w < dist[parent]:
                dist[parent] = d + w
                heapq.heappush(heap, (dist[parent], parent))

    return dist

def check_heuristic(graph, heuristic, goal):
    """Verifica admisibilidad (h <= h*) y consistencia (h(n) <= c(n,m) + h(m))."""
    validate(graph, goal, goal)
    h_star = true_costs(graph, goal)

    no_admisibles = [
        (n, heuristic.get(n, 0), h_star[n])
        for n in sorted(h_star)
        if heuristic.get(n, 0) > h_star[n]
    ]
    no_consistentes = [
        (u, v, heuristic.get(u, 0), w + heuristic.get(v, 0))
        for u, edges in graph.items()
        for v, w in edges
        if heuristic.get(u, 0) > w + heuristic.get(v, 0)
    ]

    print("\n--- Diagnóstico de la heurística ---")
    if no_admisibles:
        for n, h, real in no_admisibles:
            print(f"  No admisible en {n}: h={h} > h*={real}")
    else:
        print("  Admisible: h(n) <= h*(n) en todos los nodos.")

    if no_consistentes:
        for u, v, h, cota in no_consistentes:
            print(f"  No consistente en {u}->{v}: h({u})={h} > {cota}")
    else:
        print("  Consistente en todas las aristas.")

    if no_admisibles:
        print("  A* no garantiza el óptimo con esta heurística.")

    return not no_admisibles and not no_consistentes

def compare(graph, start, goal, heuristic=None, verbose=False):
    """Ejecuta los algoritmos disponibles y los compara en una tabla."""
    runs = [
        ("DFS", lambda: depth_first_search(graph, start, goal, verbose)),
        ("BFS", lambda: breadth_first_search(graph, start, goal, verbose)),
        ("UCS", lambda: uniform_cost_search(graph, start, goal, verbose)),
    ]
    if heuristic:
        runs += [
            ("Greedy", lambda: greedy_best_first_search(graph, heuristic, start, goal, verbose)),
            ("A*", lambda: a_star_search(graph, heuristic, start, goal, verbose)),
        ]

    results = [(name, fn()) for name, fn in runs]

    # UCS es la referencia de optimalidad: siempre halla el costo minimo.
    optimal = next((r["cost"] for n, r in results if n == "UCS" and r), None)

    print(f"\n{'Algoritmo':<10}{'Expandidos':>12}{'Costo':>8}{'Óptimo':>9}  Camino")
    print("-" * 70)
    for name, res in results:
        if res is None:
            print(f"{name:<10}{'-':>12}{'-':>8}{'-':>9}  sin solución")
            continue
        mark = "sí" if res["cost"] == optimal else "no"
        print(
            f"{name:<10}{len(res['expansion_order']):>12}{res['cost']:>8}{mark:>9}  "
            f"{' -> '.join(res['path'])}"
        )
    return results

# Grafo con ciclos: verifica que el control de explorados evita bucles infinitos.
cyclic_graph = {
    "A": [("B", 1), ("C", 4)],
    "B": [("A", 1), ("C", 1), ("D", 7)],
    "C": [("A", 4), ("B", 1), ("D", 2)],
    "D": [("B", 7), ("C", 2)]
}
cyclic_heuristic = {"A": 3, "B": 2, "C": 2, "D": 0}

# Grafo sin camino hacia la meta: los algoritmos deben devolver None.
disconnected_graph = {
    "A": [("B", 1)],
    "B": [("A", 1)],
    "Z": []
}

# Greedy cae en la trampa de S->P (h bajo, ruta cara); UCS y A* toman S->Q.
trap_graph = {
    "S": [("P", 1), ("Q", 4)],
    "P": [("G", 20)],
    "Q": [("G", 2)],
    "G": []
}
trap_heuristic = {"S": 2, "P": 1, "Q": 2, "G": 0}

if __name__ == "__main__":
    print(">>> GRAFO DEL DOCUMENTO GUÍA <<<")
    check_heuristic(graph, heuristic, goal)
    compare(graph, start, goal, heuristic)

    print("\n\n>>> GRAFO CON CICLOS (A -> D) <<<")
    compare(cyclic_graph, "A", "D", cyclic_heuristic)

    print("\n\n>>> GRAFO SIN SOLUCIÓN (A -> Z) <<<")
    compare(disconnected_graph, "A", "Z")

    print("\n\n>>> GRAFO TRAMPA PARA GREEDY (S -> G) <<<")
    check_heuristic(trap_graph, trap_heuristic, "G")
    compare(trap_graph, "S", "G", trap_heuristic)
