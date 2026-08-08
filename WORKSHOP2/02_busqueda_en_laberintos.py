"""Busqueda en laberintos con DFS, BFS, UCS, Greedy Best-First y A*.

Cada algoritmo devuelve un diccionario con el camino, el orden de expansion
y el costo, o None si no existe camino hasta la meta.
"""

# =========================
# Codigo 1: imports y setup
# =========================

from __future__ import annotations

from itertools import count
from pathlib import Path
import heapq

import numpy as np

# matplotlib es opcional: si no esta instalado el script corre igual
# y solo se omiten las graficas.
try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False

# Rutas relativas al archivo, no al directorio desde donde se ejecuta.
BASE_DIR = Path(__file__).parent
MAZES_DIR = BASE_DIR / "mazes"
FIGURAS_DIR = BASE_DIR / "figuras"


# ==========================================
# Codigo 2: representacion del problema Maze
# ==========================================
class Maze:
    def __init__(self, filename: str | Path):
        self.filename = Path(filename)
        contents = self.filename.read_text(encoding="utf-8")

        if contents.count("A") != 1:
            raise ValueError("El laberinto debe tener exactamente un punto inicial A.")
        if contents.count("B") != 1:
            raise ValueError("El laberinto debe tener exactamente una meta B.")

        # rstrip evita que un espacio sobrante al final de una fila
        # agregue una columna fantasma a todo el laberinto.
        lines = [line.rstrip() for line in contents.splitlines()]
        self.height = len(lines)
        self.width = max(len(line) for line in lines)
        self.walls = np.zeros((self.height, self.width), dtype=bool)

        for row in range(self.height):
            for col in range(self.width):
                # Las filas mas cortas se rellenan con muro.
                symbol = lines[row][col] if col < len(lines[row]) else "#"

                if symbol == "A":
                    self.start = (row, col)
                elif symbol == "B":
                    self.goal = (row, col)
                elif symbol != " ":
                    self.walls[row, col] = True

    def neighbors(self, state: tuple[int, int]):
        """Vecinos como lista de tuplas (estado, costo).

        El orden de las direcciones determina que rama explora DFS primero.
        """
        row, col = state
        candidates = [
            (row - 1, col),  # arriba
            (row + 1, col),  # abajo
            (row, col - 1),  # izquierda
            (row, col + 1),  # derecha
        ]

        valid = []
        for r, c in candidates:
            dentro_del_mapa = 0 <= r < self.height and 0 <= c < self.width
            if dentro_del_mapa and not self.walls[r, c]:
                valid.append(((r, c), 1))  # todos los pasos cuestan 1
        return valid

    def show(self, path=None, explored=None, title="Laberinto", figsize=(6, 6),
             save_as=None):
        """Dibuja el laberinto. Si save_as tiene valor guarda un PNG en vez
        de abrir una ventana bloqueante."""
        if not MATPLOTLIB_DISPONIBLE:
            print(f"  [sin matplotlib] se omite la grafica: {title}")
            return

        # 0: libre, 1: muro, 2: explorado, 3: camino, 4: inicio, 5: meta
        grid = np.zeros((self.height, self.width), dtype=int)
        grid[self.walls] = 1

        if explored:
            for r, c in explored:
                if grid[r, c] == 0:
                    grid[r, c] = 2

        if path:
            for r, c in path:
                if grid[r, c] in (0, 2):
                    grid[r, c] = 3

        # Inicio y meta se pintan al final para que nada los tape.
        grid[self.start] = 4
        grid[self.goal] = 5

        colors = ["white", "#222222", "#a9d6e5", "#ffb703", "#2a9d8f", "#e63946"]
        cmap = ListedColormap(colors)

        plt.figure(figsize=figsize)
        plt.imshow(grid, cmap=cmap, vmin=0, vmax=5)
        plt.xticks([])
        plt.yticks([])
        plt.title(title)

        if save_as:
            FIGURAS_DIR.mkdir(exist_ok=True)
            destino = FIGURAS_DIR / save_as
            plt.savefig(destino, dpi=120, bbox_inches="tight")
            plt.close()
            print(f"  Figura guardada: {destino.name}")
        else:
            plt.show()


# =========================================
# Codigo 3: estructuras comunes de busqueda
# =========================================
class Node:
    def __init__(self, state, parent=None, cost=0):
        self.state = state
        self.parent = parent
        self.cost = cost

    # Respaldo por si dos entradas de la cola empatan en prioridad y contador.
    def __lt__(self, other):
        return self.cost < other.cost

    def __repr__(self):
        return f"{self.state}(g={self.cost})"


def reconstruct_path(node):
    """Recorre los padres desde la meta hasta el inicio y devuelve el camino."""
    path = []

    while node is not None:
        path.append(node.state)
        node = node.parent

    return list(reversed(path))


def build_result(node, expansion_order):
    """Formato unico de salida para los cinco algoritmos."""
    return {
        "path": reconstruct_path(node),
        "expansion_order": expansion_order,
        "cost": node.cost,
    }


# ================================
# Codigo 4: DFS con StackFrontier
# ================================
class StackFrontier:
    """Frontera LIFO: se saca el ultimo nodo agregado."""

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


def depth_first_search(maze, start, goal, verbose=False):
    """Explora una rama hasta el fondo antes de retroceder.

    Encuentra un camino, pero no garantiza que sea el mas corto ni el mas barato.
    """
    frontier = StackFrontier()
    frontier.add(Node(start))

    explored = set()
    expansion_order = []

    while not frontier.empty():
        node = frontier.remove()
        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo: {node.state}")

        if node.state == goal:
            return build_result(node, expansion_order)

        explored.add(node.state)

        for child_state, edge_cost in maze.neighbors(node.state):
            # Se descartan estados ya expandidos o ya encolados.
            if (
                child_state not in explored
                and not frontier.contains_state(child_state)
            ):
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost,
                )
                frontier.add(child)

    return None  # se agoto la frontera sin llegar a la meta


# ===============================
# Codigo 5: BFS con QueueFrontier
# ===============================
class QueueFrontier(StackFrontier):
    """Frontera FIFO: cambiar pop() por pop(0) es toda la diferencia con DFS."""

    def remove(self):
        if self.empty():
            raise Exception("La frontier está vacía.")

        return self.frontier.pop(0)


def breadth_first_search(maze, start, goal, verbose=False):
    """Explora por niveles de profundidad.

    Con costos uniformes garantiza el camino con menos pasos.
    """
    frontier = QueueFrontier()
    frontier.add(Node(start))

    explored = set()
    expansion_order = []

    while not frontier.empty():
        node = frontier.remove()
        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo: {node.state}")

        if node.state == goal:
            return build_result(node, expansion_order)

        explored.add(node.state)

        for child_state, edge_cost in maze.neighbors(node.state):
            if (
                child_state not in explored
                and not frontier.contains_state(child_state)
            ):
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost,
                )
                frontier.add(child)

    return None


# ===================================
# Codigo 6: UCS con PriorityFrontier
# ===================================
class PriorityFrontier:
    """Cola de prioridad: siempre sale el nodo de menor prioridad."""

    def __init__(self):
        self.heap = []
        self.counter = count()

    def add(self, node, priority):
        # El contador desempata prioridades iguales respetando el orden
        # de insercion y evita comparar objetos Node entre si.
        heapq.heappush(
            self.heap,
            (priority, next(self.counter), node),
        )

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


def uniform_cost_search(maze, start, goal, verbose=False):
    """Expande siempre el nodo de menor costo acumulado g(n).

    Garantiza el camino de menor costo aunque las aristas valgan distinto.
    """
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=0)

    # Mejor costo conocido hasta cada estado.
    best_cost = {start: 0}
    expansion_order = []

    while not frontier.empty():
        node, _ = frontier.remove()

        # Entrada obsoleta: despues de encolarla se hallo un camino mas barato.
        if node.cost != best_cost.get(node.state):
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: g={node.cost}")

        if node.state == goal:
            return build_result(node, expansion_order)

        for child_state, edge_cost in maze.neighbors(node.state):
            new_cost = node.cost + edge_cost

            # Solo se encola si mejora el mejor costo conocido.
            if new_cost < best_cost.get(child_state, float("inf")):
                best_cost[child_state] = new_cost

                child = Node(
                    state=child_state,
                    parent=node,
                    cost=new_cost,
                )

                frontier.add(child, priority=new_cost)

    return None


# =========================================
# Codigo 7: heuristica distancia Manhattan
# =========================================
def manhattan(state, goal):
    """Pasos minimos ignorando los muros.

    Es admisible porque solo hay movimientos en cruz y cada uno cuesta 1,
    asi que nunca sobreestima el costo real.
    """
    return abs(state[0] - goal[0]) + abs(state[1] - goal[1])


def weighted_manhattan(state, goal, weight=3):
    """Manhattan multiplicada: sobreestima y deja de ser admisible.

    A* pierde la garantia de optimalidad pero suele explorar menos estados.
    """
    return weight * manhattan(state, goal)


def zero_heuristic(state, goal):
    """h(n) = 0. Con ella A* se reduce exactamente a UCS."""
    return 0


# ====================================
# Codigo 8: Greedy Best-First Search
# ====================================
def greedy_best_first_search(maze, heuristic, start, goal, verbose=False):
    """Expande el nodo que parece mas cercano a la meta segun h(n).

    Ignora el costo acumulado, por eso es rapido pero puede dar un rodeo.
    """
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=heuristic(start, goal))

    explored = set()
    expansion_order = []

    while not frontier.empty():
        node, priority = frontier.remove()

        # Puede haber copias del mismo estado en la cola; se ignoran las repetidas.
        if node.state in explored:
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: h={priority}")

        if node.state == goal:
            return build_result(node, expansion_order)

        explored.add(node.state)

        for child_state, edge_cost in maze.neighbors(node.state):
            if child_state not in explored:
                child = Node(
                    state=child_state,
                    parent=node,
                    cost=node.cost + edge_cost,
                )
                frontier.add(child, priority=heuristic(child_state, goal))

    return None


# =================
# Codigo 9: A star
# =================
def a_star_search(maze, heuristic, start, goal, verbose=False):
    """Combina costo acumulado y heuristica: f(n) = g(n) + h(n).

    Con heuristica admisible encuentra el camino optimo explorando menos que UCS.
    """
    frontier = PriorityFrontier()
    frontier.add(Node(start, cost=0), priority=heuristic(start, goal))

    best_cost = {start: 0}
    expansion_order = []

    while not frontier.empty():
        node, priority = frontier.remove()

        # Entrada obsoleta de la cola de prioridad.
        if node.cost != best_cost.get(node.state):
            continue

        expansion_order.append(node.state)

        if verbose:
            print(f"Expandiendo {node.state}: g={node.cost}, f={priority}")

        if node.state == goal:
            return build_result(node, expansion_order)

        for child_state, edge_cost in maze.neighbors(node.state):
            new_cost = node.cost + edge_cost

            # Reabrir con g menor permite corregir heuristicas inconsistentes.
            if new_cost < best_cost.get(child_state, float("inf")):
                best_cost[child_state] = new_cost

                child = Node(
                    state=child_state,
                    parent=node,
                    cost=new_cost,
                )
                frontier.add(
                    child,
                    priority=new_cost + heuristic(child_state, goal),
                )

    return None


# ===========================================
# Codigo 10: comparacion final y experimentos
# ===========================================
def run_all(maze, heuristic=manhattan):
    """Corre los cinco algoritmos sobre el mismo laberinto."""
    start, goal = maze.start, maze.goal
    return {
        "DFS": depth_first_search(maze, start, goal),
        "BFS": breadth_first_search(maze, start, goal),
        "UCS": uniform_cost_search(maze, start, goal),
        "Greedy": greedy_best_first_search(maze, heuristic, start, goal),
        "A*": a_star_search(maze, heuristic, start, goal),
    }


def summarize_results(results):
    """Convierte los resultados en filas de resumen.

    Un algoritmo sin solucion queda con los campos numericos en None.
    """
    rows = []
    for name, result in results.items():
        if result is None:
            rows.append({
                "algoritmo": name,
                "estados_explorados": None,
                "longitud_camino": None,
                "costo_camino": None,
            })
        else:
            rows.append({
                "algoritmo": name,
                "estados_explorados": len(result["expansion_order"]),
                "longitud_camino": len(result["path"]) - 1,
                "costo_camino": result["cost"],
            })
    return rows


def print_table(results, titulo="Comparacion de algoritmos"):
    """Imprime la tabla comparativa marcando cual alcanzo el costo minimo."""
    rows = summarize_results(results)
    costos = [r["costo_camino"] for r in rows if r["costo_camino"] is not None]
    optimo = min(costos) if costos else None

    print(f"\n{titulo}")
    print(f"{'Algoritmo':<10}{'Explorados':>12}{'Pasos':>8}{'Costo':>8}{'Optimo':>9}")
    print("-" * 47)

    for row in rows:
        if row["costo_camino"] is None:
            print(f"{row['algoritmo']:<10}{'-':>12}{'-':>8}{'-':>8}{'sin sol.':>9}")
            continue
        marca = "si" if row["costo_camino"] == optimo else "no"
        print(
            f"{row['algoritmo']:<10}"
            f"{row['estados_explorados']:>12}"
            f"{row['longitud_camino']:>8}"
            f"{row['costo_camino']:>8}"
            f"{marca:>9}"
        )


def validate_path(maze, path):
    """Comprueba que el camino sea fisicamente valido dentro del laberinto.

    Verifica extremos, adyacencia entre pasos consecutivos y ausencia de muros.
    """
    if not path or path[0] != maze.start or path[-1] != maze.goal:
        return False

    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        if abs(r1 - r2) + abs(c1 - c2) != 1:  # no son celdas contiguas
            return False
        if maze.walls[r2, c2]:
            return False

    return True


def experimento_heuristica_cero(maze):
    """Verifica empiricamente que A* con h(n) = 0 se comporta igual que UCS."""
    start, goal = maze.start, maze.goal
    ucs = uniform_cost_search(maze, start, goal)
    astar_cero = a_star_search(maze, zero_heuristic, start, goal)

    print("\nExperimento 1: A* con h(n) = 0 frente a UCS")
    print(f"  UCS         -> costo {ucs['cost']}, explorados {len(ucs['expansion_order'])}")
    print(f"  A* con h=0  -> costo {astar_cero['cost']}, "
          f"explorados {len(astar_cero['expansion_order'])}")

    iguales = ucs["expansion_order"] == astar_cero["expansion_order"]
    print(f"  Mismo orden de expansion: {'si' if iguales else 'no'}")


def experimento_heuristica_ponderada(maze):
    """Compara Manhattan admisible contra la version ponderada que sobreestima."""
    start, goal = maze.start, maze.goal
    admisible = a_star_search(maze, manhattan, start, goal)
    ponderada = a_star_search(maze, weighted_manhattan, start, goal)

    print("\nExperimento 2: heuristica admisible frente a heuristica ponderada")
    print(f"  A* Manhattan (admisible) -> costo {admisible['cost']}, "
          f"explorados {len(admisible['expansion_order'])}")
    print(f"  A* ponderada (x3)        -> costo {ponderada['cost']}, "
          f"explorados {len(ponderada['expansion_order'])}")

    if ponderada["cost"] > admisible["cost"]:
        print("  La heuristica ponderada perdio la optimalidad.")
    else:
        print("  En este laberinto mantuvo el optimo, pero no esta garantizado.")


def resolver_laberinto(nombre_archivo, titulo, guardar_figuras=False):
    """Carga un laberinto, ejecuta todo, valida los caminos y muestra la tabla."""
    maze = Maze(MAZES_DIR / nombre_archivo)
    print(f"\n{'=' * 60}")
    print(f"{titulo}  ({maze.height}x{maze.width})")
    print("=" * 60)

    results = run_all(maze)

    # Ningun algoritmo deberia devolver un camino invalido.
    for name, result in results.items():
        if result is not None:
            assert validate_path(maze, result["path"]), f"{name} devolvio un camino invalido"

    print_table(results, titulo=f"Resultados sobre {nombre_archivo}")

    if guardar_figuras:
        print()
        maze.show(title=titulo, save_as=f"{maze.filename.stem}_inicial.png")
        for name, result in results.items():
            if result is None:
                continue
            maze.show(
                path=result["path"],
                explored=set(result["expansion_order"]),
                title=f"{name}: estados explorados y solucion",
                save_as=f"{maze.filename.stem}_{name.replace('*', 'star')}.png",
            )

    return maze, results


# ===================================
# Ejecucion local y pruebas publicas
# ===================================
if __name__ == "__main__":
    maze1, results_maze1 = resolver_laberinto(
        "maze1.txt", "Maze 1: laberinto del taller", guardar_figuras=True
    )

    # Pruebas publicas del enunciado sobre maze1.
    bfs_result = results_maze1["BFS"]
    greedy_result = results_maze1["Greedy"]
    astar_result = results_maze1["A*"]

    assert bfs_result["path"][0] == maze1.start
    assert bfs_result["path"][-1] == maze1.goal
    assert bfs_result["cost"] == 28
    assert len(bfs_result["path"]) == 29

    assert greedy_result["path"][0] == maze1.start
    assert greedy_result["path"][-1] == maze1.goal
    assert greedy_result["cost"] == 32

    assert astar_result["path"][0] == maze1.start
    assert astar_result["path"][-1] == maze1.goal
    assert astar_result["cost"] == 28

    print("\nPruebas publicas completadas correctamente.")

    experimento_heuristica_cero(maze1)
    experimento_heuristica_ponderada(maze1)

    # Segundo laberinto: confirma que los resultados no dependen de un solo mapa.
    resolver_laberinto("maze2.txt", "Maze 2: topologia distinta")

    # Tercer laberinto: la meta es inalcanzable, todos deben devolver None.
    _, results_sin_sol = resolver_laberinto(
        "maze3_sin_solucion.txt", "Maze 3: meta inalcanzable"
    )
    assert all(r is None for r in results_sin_sol.values()), \
        "Un algoritmo reporto camino en un laberinto sin solucion"

    print("\nTodas las verificaciones pasaron.")
