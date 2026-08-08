"""Hill Climbing y Random Restart para el problema de ubicacion de hospitales.

Se ubican k hospitales en una cuadricula para minimizar la suma de la distancia
de cada casa al hospital mas cercano. El script corre el algoritmo base, las
tres actividades del taller y cuatro experimentos adicionales sobre optimos
locales, mesetas y costo de exploracion.
"""

# =========================
# Codigo 1: imports y setup
# =========================

from __future__ import annotations

from itertools import combinations
from pathlib import Path
import random

# matplotlib es opcional: si no esta instalado el script corre igual
# y solo se omiten las graficas.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False

# Rutas relativas al archivo, no al directorio desde donde se ejecuta.
BASE_DIR = Path(__file__).parent
FIGURAS_DIR = BASE_DIR / "figuras"

SEED = 8

HEIGHT, WIDTH = 10, 16
NUM_HOUSES = 18
NUM_HOSPITALS = 3


# ==================================
# Codigo 2: metricas de distancia
# ==================================
def manhattan(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Distancia L1. Es la del enunciado: solo se avanza por la cuadricula."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidea(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Distancia L2, en linea recta. Se usa en la Actividad 1."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


METRICAS = {"manhattan": manhattan, "euclidea": euclidea}


# ==============================================
# Codigo 3: representacion del problema
# ==============================================
class HospitalWorld:
    """Cuadricula con casas fijas. Los hospitales son el estado a optimizar."""

    def __init__(self, height: int, width: int, houses: set[tuple[int, int]]):
        self.height = height
        self.width = width
        self.houses = set(houses)

        for (r, c) in self.houses:
            if not self.in_bounds((r, c)):
                raise ValueError(f"La casa {(r, c)} esta fuera de la cuadricula.")

    @classmethod
    def random(cls, height, width, num_houses, rng) -> "HospitalWorld":
        all_cells = [(r, c) for r in range(height) for c in range(width)]
        return cls(height, width, set(rng.sample(all_cells, num_houses)))

    def in_bounds(self, cell: tuple[int, int]) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width

    def available_cells(self) -> list[tuple[int, int]]:
        """Celdas libres: no puede haber un hospital sobre una casa."""
        return sorted(
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in self.houses
        )

    def random_state(self, num_hospitals: int, rng) -> set[tuple[int, int]]:
        return set(rng.sample(self.available_cells(), num_hospitals))

    def cost(self, hospitals, metric=manhattan) -> float:
        """Suma de la distancia de cada casa al hospital mas cercano."""
        return sum(
            min(metric(house, hospital) for hospital in hospitals)
            for house in self.houses
        )

    # ------------------------------------------------------------------
    # Codigo 4: vecindario
    # ------------------------------------------------------------------
    def neighbors(self, hospitals, radius: int = 1) -> list[set[tuple[int, int]]]:
        """Estados vecinos: mover UN hospital dentro de un radio Manhattan.

        Con radius=1 son los cuatro movimientos del enunciado. Con radius=2 se
        agregan los saltos de dos celdas, que es lo que pide la Actividad 3.
        """
        moves = [
            (dr, dc)
            for dr in range(-radius, radius + 1)
            for dc in range(-radius, radius + 1)
            if (dr or dc) and abs(dr) + abs(dc) <= radius
        ]

        neighbors = []
        for hospital in hospitals:
            for dr, dc in moves:
                candidate = (hospital[0] + dr, hospital[1] + dc)
                if not self.in_bounds(candidate):
                    continue
                if candidate in self.houses or candidate in hospitals:
                    continue

                new_state = set(hospitals)
                new_state.remove(hospital)
                new_state.add(candidate)
                neighbors.append(new_state)

        return neighbors

    # ------------------------------------------------------------------
    # Codigo 5: visualizacion
    # ------------------------------------------------------------------
    def show(self, hospitals, title="Estado", save_as=None, figsize=(8, 4.5)):
        """Dibuja la cuadricula. Con save_as guarda un PNG sin abrir ventana."""
        if not MATPLOTLIB_DISPONIBLE:
            return

        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(-0.5, self.width - 0.5)
        ax.set_ylim(self.height - 0.5, -0.5)
        ax.set_xticks(range(self.width))
        ax.set_yticks(range(self.height))
        ax.grid(True)

        if self.houses:
            hr, hc = zip(*self.houses)
            ax.scatter(hc, hr, marker="s", s=110, label="Casas")
        if hospitals:
            rr, cc = zip(*hospitals)
            ax.scatter(cc, rr, marker="P", s=180, label="Hospitales")

        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        ax.set_title(title)
        fig.tight_layout()
        guardar_figura(fig, save_as)


def guardar_figura(fig, save_as):
    """Guarda en figuras/ y cierra. Nunca bloquea la ejecucion."""
    if save_as is None:
        plt.close(fig)
        return
    FIGURAS_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURAS_DIR / save_as, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ==============================================
# Codigo 6: validacion de estados
# ==============================================
def validar_estado(world: HospitalWorld, hospitals, num_hospitals: int) -> None:
    """Confirma que la solucion es legal. Se aplica a toda solucion devuelta."""
    assert len(hospitals) == num_hospitals, (
        f"Se esperaban {num_hospitals} hospitales, hay {len(hospitals)}."
    )
    for hospital in hospitals:
        assert world.in_bounds(hospital), f"Hospital fuera de la cuadricula: {hospital}"
        assert hospital not in world.houses, f"Hospital sobre una casa: {hospital}"


def validar_historial(history: list[float]) -> None:
    """El costo nunca debe subir entre iteraciones de Hill Climbing."""
    for anterior, actual in zip(history, history[1:]):
        assert actual <= anterior, f"El costo subio de {anterior} a {actual}."


# ==============================================
# Codigo 7: Hill Climbing
# ==============================================
def hill_climbing(world, num_hospitals, metric=manhattan, radius=1,
                  initial_state=None, max_iterations=200, max_sideways=0,
                  rng=None):
    """Hill Climbing de ascenso mas pronunciado (steepest descent).

    Devuelve un diccionario con la solucion, el historial de costos, la
    trayectoria de estados, el numero de vecinos evaluados y el motivo de
    parada. Distinguir el motivo es lo que permite separar un optimo local
    de una meseta.

    max_sideways permite aceptar movimientos de igual costo para atravesar
    mesetas. Con 0 el algoritmo se detiene en la primera meseta, que es el
    comportamiento del enunciado.
    """
    # rng or random.Random() respeta la semilla recibida. Asignar
    # random.Random() directamente pisaria el argumento y romperia la
    # reproducibilidad de todo el experimento.
    rng = rng or random.Random()

    if initial_state is not None:
        current = set(initial_state)
    else:
        current = world.random_state(num_hospitals, rng)

    history = [world.cost(current, metric)]
    states = [set(current)]
    evaluaciones = 0
    laterales = 0
    motivo = "max_iteraciones"

    for _ in range(max_iterations):
        neighbors = world.neighbors(current, radius)
        if not neighbors:
            motivo = "sin_vecinos"
            break

        costs = [world.cost(n, metric) for n in neighbors]
        evaluaciones += len(neighbors)
        best_cost = min(costs)
        current_cost = history[-1]

        if best_cost > current_cost:
            motivo = "optimo_local"
            break

        if best_cost == current_cost:
            # Meseta: ningun vecino mejora, pero al menos uno empata.
            if laterales >= max_sideways:
                motivo = "meseta" if max_sideways == 0 else "meseta_sin_presupuesto"
                break
            laterales += 1
        else:
            laterales = 0

        best_neighbors = [n for n, c in zip(neighbors, costs) if c == best_cost]
        current = set(rng.choice(best_neighbors))
        history.append(best_cost)
        states.append(set(current))

    validar_estado(world, current, num_hospitals)
    validar_historial(history)

    return {
        "solution": current,
        "history": history,
        "states": states,
        "evaluaciones": evaluaciones,
        "iteraciones": len(history) - 1,
        "motivo": motivo,
    }


# ==============================================
# Codigo 8: Random Restart
# ==============================================
def random_restart(world, num_hospitals, metric=manhattan, radius=1,
                   restarts=40, max_sideways=0, seed=0):
    """Corre Hill Climbing desde varios estados iniciales y guarda el mejor.

    El master_rng deriva una semilla por corrida, asi la ejecucion completa es
    reproducible a partir de un unico seed.
    """
    master_rng = random.Random(seed)
    runs = []
    best = None

    for restart in range(restarts):
        run_seed = master_rng.randrange(10**9)
        resultado = hill_climbing(
            world, num_hospitals, metric=metric, radius=radius,
            max_sideways=max_sideways, rng=random.Random(run_seed),
        )
        record = {
            "restart": restart,
            "solution": resultado["solution"],
            "initial_cost": resultado["history"][0],
            "final_cost": resultado["history"][-1],
            "iteraciones": resultado["iteraciones"],
            "evaluaciones": resultado["evaluaciones"],
            "motivo": resultado["motivo"],
        }
        runs.append(record)
        if best is None or record["final_cost"] < best["final_cost"]:
            best = record

    return best, runs


# ==============================================
# Codigo 9: optimo global por fuerza bruta
# ==============================================
def optimo_global(world, num_hospitals, metric=manhattan):
    """Recorre todas las combinaciones posibles. Solo viable para k pequeno.

    Sirve como referencia: sin el no se puede afirmar si Random Restart
    encontro el optimo global o simplemente un buen optimo local.
    """
    celdas = world.available_cells()
    mejor, mejor_costo = None, float("inf")
    for combinacion in combinations(celdas, num_hospitals):
        costo = world.cost(combinacion, metric)
        if costo < mejor_costo:
            mejor, mejor_costo = set(combinacion), costo
    return mejor, mejor_costo


# ==============================================
# Codigo 10: utilidades de impresion
# ==============================================
def fmt(valor, decimales=2):
    """Los costos Manhattan son enteros, los euclideos no."""
    if isinstance(valor, float) and not valor.is_integer():
        return f"{valor:.{decimales}f}"
    return str(int(valor))


def imprimir_tabla(encabezados, filas, titulo=None):
    if titulo:
        print(titulo)
    columnas = [len(h) for h in encabezados]
    filas = [[str(c) for c in fila] for fila in filas]
    for fila in filas:
        for i, celda in enumerate(fila):
            columnas[i] = max(columnas[i], len(celda))

    linea = "  ".join(h.ljust(columnas[i]) for i, h in enumerate(encabezados))
    print(linea)
    print("-" * len(linea))
    for fila in filas:
        print("  ".join(celda.ljust(columnas[i]) for i, celda in enumerate(fila)))
    print()


def coords(hospitals):
    return " ".join(str(h) for h in sorted(hospitals))


# ==============================================
# Codigo 11: algoritmo base
# ==============================================
def ejecutar_base(world, initial_hospitals):
    print("=" * 70)
    print("HILL CLIMBING BASE (Manhattan, vecindario de 1 paso)")
    print("=" * 70 + "\n")

    resultado = hill_climbing(
        world, NUM_HOSPITALS, initial_state=initial_hospitals,
        rng=random.Random(SEED),
    )

    vecinos_inicio = world.neighbors(initial_hospitals, radius=1)
    print(f"Vecinos del estado inicial : {len(vecinos_inicio)}")
    print(f"Costo inicial              : {fmt(resultado['history'][0])}")
    print(f"Costo final                : {fmt(resultado['history'][-1])}")
    print(f"Iteraciones con mejora     : {resultado['iteraciones']}")
    print(f"Vecinos evaluados          : {resultado['evaluaciones']}")
    print(f"Motivo de parada           : {resultado['motivo']}")
    print(f"Hospitales                 : {coords(resultado['solution'])}\n")

    world.show(initial_hospitals,
               title=f"Estado inicial - costo {fmt(resultado['history'][0])}",
               save_as="01_estado_inicial.png")
    world.show(resultado["solution"],
               title=f"Hill Climbing - costo {fmt(resultado['history'][-1])}",
               save_as="02_hill_climbing.png")
    graficar_historial(resultado["history"], "Evolucion del costo",
                       "03_evolucion_costo.png")
    graficar_trayectoria(world, resultado["states"], "04_trayectoria.png")
    return resultado


def graficar_historial(history, titulo, save_as):
    if not MATPLOTLIB_DISPONIBLE:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(len(history)), history, marker="o")
    ax.set_xlabel("Iteracion")
    ax.set_ylabel("Costo")
    ax.set_title(titulo)
    ax.grid(True)
    fig.tight_layout()
    guardar_figura(fig, save_as)


def graficar_trayectoria(world, states, save_as):
    """Usa la lista de estados que el algoritmo ya venia guardando.

    Muestra como se desplaza cada hospital desde el estado inicial hasta el
    optimo local, informacion que antes se calculaba y se descartaba.
    """
    if not MATPLOTLIB_DISPONIBLE:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_xlim(-0.5, world.width - 0.5)
    ax.set_ylim(world.height - 0.5, -0.5)
    ax.set_xticks(range(world.width))
    ax.set_yticks(range(world.height))
    ax.grid(True)

    hr, hc = zip(*world.houses)
    ax.scatter(hc, hr, marker="s", s=110, label="Casas")

    for paso, estado in enumerate(states):
        rr, cc = zip(*sorted(estado))
        alpha = 0.15 + 0.85 * (paso / max(len(states) - 1, 1))
        ax.scatter(cc, rr, marker="P", s=90, color="tab:orange", alpha=alpha)

    rr, cc = zip(*sorted(states[-1]))
    ax.scatter(cc, rr, marker="P", s=200, color="tab:red", label="Posicion final")

    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.set_title("Trayectoria de los hospitales")
    fig.tight_layout()
    guardar_figura(fig, save_as)


def ejecutar_random_restart(world):
    print("=" * 70)
    print("RANDOM RESTART (40 reinicios)")
    print("=" * 70 + "\n")

    best, runs = random_restart(world, NUM_HOSPITALS, restarts=40, seed=SEED)
    costos = [run["final_cost"] for run in runs]

    print(f"Mejor costo          : {fmt(best['final_cost'])}")
    print(f"Reinicio ganador     : {best['restart']}")
    print(f"Peor costo           : {fmt(max(costos))}")
    print(f"Costo promedio       : {sum(costos) / len(costos):.2f}")
    print(f"Corridas en el mejor : {costos.count(min(costos))} de {len(costos)}")
    print(f"Hospitales           : {coords(best['solution'])}\n")

    motivos = {}
    for run in runs:
        motivos[run["motivo"]] = motivos.get(run["motivo"], 0) + 1
    print("Motivo de parada de las 40 corridas:")
    for motivo, veces in sorted(motivos.items()):
        print(f"  {motivo:<15} {veces}")
    print()

    world.show(best["solution"],
               title=f"Random Restart - mejor costo {fmt(best['final_cost'])}",
               save_as="05_random_restart.png")
    graficar_historial(costos, "Variabilidad entre reinicios",
                       "06_variabilidad_reinicios.png")
    return best, runs


# ==============================================
# Codigo 12: Actividad 1 - distancia euclidea
# ==============================================
def actividad_1(world, initial_hospitals):
    print("=" * 70)
    print("ACTIVIDAD 1: distancia Manhattan frente a distancia euclidea")
    print("=" * 70 + "\n")

    resultados = {}
    for nombre, metric in METRICAS.items():
        resultados[nombre] = hill_climbing(
            world, NUM_HOSPITALS, metric=metric,
            initial_state=initial_hospitals, rng=random.Random(SEED),
        )

    # Comparacion cruzada: cada solucion se evalua con AMBAS metricas.
    # Comparar 46.70 euclideo contra 62 Manhattan no dice nada, son unidades
    # distintas. Lo unico comparable es una misma metrica sobre las dos
    # soluciones.
    filas = []
    for nombre, resultado in resultados.items():
        solucion = resultado["solution"]
        filas.append([
            f"HC {nombre}",
            coords(solucion),
            fmt(world.cost(solucion, manhattan)),
            fmt(world.cost(solucion, euclidea)),
            resultado["iteraciones"],
        ])

    imprimir_tabla(
        ["Solucion", "Hospitales", "Costo Manhattan", "Costo euclideo", "Iter"],
        filas,
        "Cada solucion evaluada con las dos metricas:\n",
    )

    sol_m = resultados["manhattan"]["solution"]
    sol_e = resultados["euclidea"]["solution"]
    man_m = world.cost(sol_m, manhattan)
    man_e = world.cost(sol_e, manhattan)

    euc_m = world.cost(sol_m, euclidea)
    euc_e = world.cost(sol_e, euclidea)

    print("Lectura de la tabla:")
    print("  - Comparar el costo euclideo contra el Manhattan directamente no")
    print("    dice nada: son unidades distintas. Lo unico comparable es una")
    print("    misma columna de la tabla.")
    print(f"  - Las ubicaciones no coinciden: {coords(sol_m)}")
    print(f"    frente a {coords(sol_e)}.")
    if man_e < man_m:
        print("  - La solucion hallada optimizando la metrica euclidea resulta")
        print(f"    MEJOR en Manhattan ({fmt(man_e)}) que la que optimizo Manhattan")
        print(f"    directamente ({fmt(man_m)}). No es una contradiccion: la")
        print("    segunda quedo atrapada en un optimo local peor. Cambiar la")
        print("    metrica cambia la forma del paisaje y por lo tanto tambien")
        print("    cambia donde estan las trampas.")
    elif man_e == man_m:
        print(f"  - En Manhattan las dos empatan ({fmt(man_m)}), aunque los")
        print("    hospitales quedaron en celdas distintas: hay varias")
        print("    configuraciones con el mismo costo.")
        print(f"  - En la metrica euclidea si se separan: {fmt(euc_e)} frente a")
        print(f"    {fmt(euc_m)}. Cada corrida gana en la metrica que optimizo,")
        print("    que es lo esperable.")
    else:
        print(f"  - En Manhattan gana la solucion que optimizo Manhattan")
        print(f"    ({fmt(man_m)} frente a {fmt(man_e)}), como era de esperarse.")
    print("  - La euclidea penaliza menos las diagonales, por eso tiende a")
    print("    centrar los hospitales en la nube de casas en vez de alinearlos")
    print("    con las filas y columnas de la cuadricula.\n")

    world.show(sol_e,
               title=f"Hill Climbing euclideo - costo {fmt(world.cost(sol_e, euclidea))}",
               save_as="07_actividad1_euclidea.png")
    return resultados


# ==============================================
# Codigo 13: Actividad 2 - numero de hospitales
# ==============================================
def actividad_2(world):
    print("=" * 70)
    print("ACTIVIDAD 2: efecto del numero de hospitales")
    print("=" * 70 + "\n")

    filas = []
    costos = []
    anterior = None
    for k in range(1, 6):
        best, _ = random_restart(world, k, restarts=40, seed=SEED)
        costo = best["final_cost"]
        costos.append(costo)
        reduccion = "-" if anterior is None else fmt(anterior - costo)
        porcentaje = "-" if anterior is None else f"{100 * (anterior - costo) / anterior:.1f}%"
        filas.append([k, fmt(costo), reduccion, porcentaje, coords(best["solution"])])
        anterior = costo

    imprimir_tabla(
        ["k", "Mejor costo", "Reduccion", "Reduccion %", "Hospitales"],
        filas,
        "Random Restart con 40 reinicios para cada k:\n",
    )

    reducciones = [costos[i] - costos[i + 1] for i in range(len(costos) - 1)]
    print("Discusion:")
    print(f"  - Las reducciones sucesivas son {reducciones}. NO son constantes:")
    print("    cada hospital adicional aporta menos que el anterior.")
    print("  - Es el efecto de rendimientos decrecientes. El primer hospital")
    print("    cubre toda la nube de casas, el segundo parte esa nube en dos")
    print("    grupos grandes, y a partir de ahi cada hospital nuevo solo puede")
    print("    dividir grupos cada vez mas pequenos.")
    print("  - El limite es claro: con k igual al numero de casas el costo seria")
    print("    0, y de ahi en adelante agregar hospitales no reduce nada.")
    print("  - Consecuencia practica: si cada hospital cuesta dinero, el punto")
    print("    donde deja de convenir construir uno mas se ve en esta tabla.\n")

    if MATPLOTLIB_DISPONIBLE:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(range(1, 6), costos, marker="o")
        ax.set_xlabel("Numero de hospitales (k)")
        ax.set_ylabel("Mejor costo")
        ax.set_title("Rendimientos decrecientes al agregar hospitales")
        ax.set_xticks(range(1, 6))
        ax.grid(True)
        fig.tight_layout()
        guardar_figura(fig, "08_actividad2_k_hospitales.png")

    return costos


# ==============================================
# Codigo 14: Actividad 3 - diseno del vecindario
# ==============================================
def actividad_3(world, initial_hospitals):
    print("=" * 70)
    print("ACTIVIDAD 3: vecindario de 1 paso frente a vecindario de 2 pasos")
    print("=" * 70 + "\n")

    # Tamano del vecindario en el estado inicial.
    tamanos = {}
    filas_tamano = []
    for radius in (1, 2):
        tamanos[radius] = len(world.neighbors(initial_hospitals, radius))
        filas_tamano.append([f"{radius} paso(s)", tamanos[radius]])
    imprimir_tabla(["Vecindario", "Vecinos en el estado inicial"], filas_tamano)

    # Misma funcion y misma semilla para los dos: si se usaran funciones
    # distintas la comparacion no diria nada sobre el vecindario.
    datos = {}
    filas = []
    for radius in (1, 2):
        una_corrida = hill_climbing(
            world, NUM_HOSPITALS, radius=radius,
            initial_state=initial_hospitals, rng=random.Random(SEED),
        )
        best, runs = random_restart(world, NUM_HOSPITALS, radius=radius,
                                    restarts=40, seed=SEED)
        datos[radius] = {
            "costo": una_corrida["history"][-1],
            "iteraciones": una_corrida["iteraciones"],
            "evaluaciones": una_corrida["evaluaciones"],
            "costo_rr": best["final_cost"],
            "evaluaciones_rr": sum(run["evaluaciones"] for run in runs),
        }
        filas.append([
            f"{radius} paso(s)",
            fmt(datos[radius]["costo"]),
            datos[radius]["iteraciones"],
            datos[radius]["evaluaciones"],
            fmt(datos[radius]["costo_rr"]),
            datos[radius]["evaluaciones_rr"],
        ])

    imprimir_tabla(
        ["Vecindario", "Costo 1 corrida", "Iter", "Evaluaciones",
         "Costo con RR(40)", "Evaluaciones RR"],
        filas,
        "Comparacion con la misma implementacion y la misma semilla:\n",
    )

    mejor_global, costo_global = optimo_global(world, NUM_HOSPITALS)
    uno, dos = datos[1], datos[2]
    factor = tamanos[2] / tamanos[1]

    print("Discusion:")
    if dos["costo"] < uno["costo"]:
        print(f"  - Si mejora la corrida unica: baja de {fmt(uno['costo'])} a "
              f"{fmt(dos['costo'])}.")
        print("    El vecindario amplio salta sobre configuraciones intermedias")
        print("    malas, asi que escapa de optimos locales que atrapan al de 1")
        print("    paso.")
    elif dos["costo"] == uno["costo"]:
        print(f"  - La corrida unica NO mejora: los dos terminan en "
              f"{fmt(uno['costo'])}.")
    else:
        print(f"  - La corrida unica empeora: {fmt(uno['costo'])} frente a "
              f"{fmt(dos['costo'])}. Mas vecinos no garantiza mejor resultado.")
    print(f"  - El precio es el numero de vecinos por iteracion, que pasa de "
          f"{tamanos[1]} a {tamanos[2]}")
    print(f"    en el estado inicial: cada paso cuesta {factor:.1f} veces mas. En la")
    print(f"    corrida unica son {uno['evaluaciones']} evaluaciones frente a "
          f"{dos['evaluaciones']}.")
    if uno["costo_rr"] == dos["costo_rr"] == costo_global:
        print(f"  - Con Random Restart los dos alcanzan {fmt(costo_global)}, que es el")
        print("    optimo global verificado por fuerza bruta, pero el de 2 pasos")
        print(f"    gasta {dos['evaluaciones_rr']} evaluaciones contra "
              f"{uno['evaluaciones_rr']}.")
        print("    Ampliar el vecindario y reiniciar atacan el MISMO problema:")
        print("    escapar de optimos locales. Si ya se usa Random Restart, el")
        print("    vecindario grande solo agrega costo de computo.")
    else:
        print(f"  - Con Random Restart: {fmt(uno['costo_rr'])} con 1 paso frente a "
              f"{fmt(dos['costo_rr'])} con 2 pasos")
        print(f"    (el optimo global es {fmt(costo_global)}).")
    print()

    una_corrida_2 = hill_climbing(
        world, NUM_HOSPITALS, radius=2,
        initial_state=initial_hospitals, rng=random.Random(SEED),
    )
    world.show(una_corrida_2["solution"],
               title=f"Vecindario de 2 pasos - costo {fmt(una_corrida_2['history'][-1])}",
               save_as="09_actividad3_dos_pasos.png")
    return mejor_global, costo_global


# ==============================================
# Codigo 15: experimentos adicionales
# ==============================================
def experimento_optimo_global(world, mejor_global, costo_global, best_rr):
    print("=" * 70)
    print("EXPERIMENTO 1: que tan lejos queda el optimo global")
    print("=" * 70 + "\n")

    print(f"Optimo global (fuerza bruta) : {fmt(costo_global)}  {coords(mejor_global)}")
    print(f"Mejor de Random Restart      : {fmt(best_rr['final_cost'])}  "
          f"{coords(best_rr['solution'])}")
    combinaciones = len(list(combinations(world.available_cells(), NUM_HOSPITALS)))
    print(f"Combinaciones revisadas      : {combinaciones}")
    print()
    if best_rr["final_cost"] == costo_global:
        print("Random Restart si alcanzo el optimo global en este caso. Pero eso")
        print("solo se puede afirmar porque la fuerza bruta lo confirmo: el")
        print("algoritmo por si solo nunca sabe si llego al optimo global.\n")
    else:
        print("Random Restart se quedo por encima del optimo global.\n")


def experimento_mesetas(world):
    """Las mesetas son un objetivo declarado del taller y son invisibles si

    solo se mira el costo final: el algoritmo se detiene igual que en un optimo
    local, pero por una razon distinta.
    """
    print("=" * 70)
    print("EXPERIMENTO 2: optimos locales frente a mesetas")
    print("=" * 70 + "\n")

    _, runs = random_restart(world, NUM_HOSPITALS, restarts=200, seed=SEED)
    motivos = {}
    for run in runs:
        motivos[run["motivo"]] = motivos.get(run["motivo"], 0) + 1

    imprimir_tabla(
        ["Motivo de parada", "Corridas de 200"],
        [[motivo, veces] for motivo, veces in sorted(motivos.items())],
        "Por que se detuvo Hill Climbing (sin movimientos laterales):\n",
    )

    print("En una meseta ningun vecino mejora pero al menos uno EMPATA. El")
    print("algoritmo del enunciado corta en los dos casos con la misma linea")
    print("(best_cost >= current_cost), asi que no puede distinguirlos.\n")

    # Movimientos laterales: la forma clasica de atravesar una meseta.
    filas = []
    for max_sideways in (0, 10, 50):
        best, runs = random_restart(world, NUM_HOSPITALS, restarts=40,
                                    max_sideways=max_sideways, seed=SEED)
        costos = [run["final_cost"] for run in runs]
        filas.append([
            max_sideways,
            fmt(best["final_cost"]),
            f"{sum(costos) / len(costos):.2f}",
            sum(run["evaluaciones"] for run in runs),
        ])

    imprimir_tabla(
        ["Movs. laterales", "Mejor costo", "Costo promedio", "Evaluaciones"],
        filas,
        "Efecto de permitir movimientos de igual costo (Random Restart 40):\n",
    )
    print("Permitir movimientos laterales deja atravesar mesetas y baja el costo")
    print("promedio, a cambio de mas evaluaciones. El limite es necesario: sin")
    print("el, el algoritmo puede quedarse dando vueltas dentro de la meseta.\n")


def experimento_estado_inicial(world):
    print("=" * 70)
    print("EXPERIMENTO 3: dependencia del estado inicial")
    print("=" * 70 + "\n")

    _, runs = random_restart(world, NUM_HOSPITALS, restarts=200, seed=SEED)
    costos = [run["final_cost"] for run in runs]
    distintos = sorted(set(costos))

    print(f"Corridas                 : {len(costos)}")
    print(f"Costos finales distintos : {len(distintos)}")
    print(f"Rango                    : {fmt(min(costos))} a {fmt(max(costos))}")
    print(f"Promedio                 : {sum(costos) / len(costos):.2f}")
    print(f"Llegaron al mejor        : {costos.count(min(costos))} "
          f"({100 * costos.count(min(costos)) / len(costos):.1f}%)")
    print()
    print("El mismo algoritmo, sobre el mismo problema, produce")
    print(f"{len(distintos)} resultados distintos segun donde empiece. Esa es la")
    print("razon de ser de Random Restart.\n")

    if MATPLOTLIB_DISPONIBLE:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(costos, bins=range(int(min(costos)), int(max(costos)) + 2), align="left")
        ax.set_xlabel("Costo final")
        ax.set_ylabel("Corridas")
        ax.set_title("Distribucion de optimos locales (200 corridas)")
        ax.grid(True, axis="y")
        fig.tight_layout()
        guardar_figura(fig, "10_distribucion_optimos_locales.png")


def experimento_reinicios(world, costo_global):
    print("=" * 70)
    print("EXPERIMENTO 4: cuantos reinicios hacen falta")
    print("=" * 70 + "\n")

    filas = []
    for restarts in (1, 5, 10, 20, 40, 80):
        best, runs = random_restart(world, NUM_HOSPITALS,
                                    restarts=restarts, seed=SEED)
        filas.append([
            restarts,
            fmt(best["final_cost"]),
            "si" if best["final_cost"] == costo_global else "no",
            sum(run["evaluaciones"] for run in runs),
        ])

    imprimir_tabla(
        ["Reinicios", "Mejor costo", "Es el optimo global", "Evaluaciones"],
        filas,
    )
    print("La mejora se concentra en los primeros reinicios y despues se")
    print("aplana. Duplicar los reinicios no duplica la calidad, pero si")
    print("duplica el costo de computo.\n")


# ==============================================
# Codigo 16: ejecucion completa
# ==============================================
def run_all():
    rng_mundo = random.Random(SEED)
    world = HospitalWorld.random(HEIGHT, WIDTH, NUM_HOUSES, rng_mundo)
    initial_hospitals = world.random_state(NUM_HOSPITALS, rng_mundo)

    print()
    print(f"Cuadricula {HEIGHT}x{WIDTH} | {NUM_HOUSES} casas | "
          f"{NUM_HOSPITALS} hospitales | semilla {SEED}\n")

    ejecutar_base(world, initial_hospitals)
    best_rr, _ = ejecutar_random_restart(world)
    actividad_1(world, initial_hospitals)
    actividad_2(world)
    mejor_global, costo_global = actividad_3(world, initial_hospitals)
    experimento_optimo_global(world, mejor_global, costo_global, best_rr)
    experimento_mesetas(world)
    experimento_estado_inicial(world)
    experimento_reinicios(world, costo_global)

    if MATPLOTLIB_DISPONIBLE:
        print(f"Figuras guardadas en: {FIGURAS_DIR}")
    else:
        print("matplotlib no esta instalado: se omitieron las figuras.")
        print("Para instalarlo: pip install -r requirements.txt")
    print()


if __name__ == "__main__":
    run_all()
