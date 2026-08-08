# Correcciones y faltantes del proyecto

Este documento lista los errores encontrados en la version anterior de
`02_busqueda_en_laberintos.py` y lo que hacia falta para completar el taller.
Cada punto indica el problema, por que importaba y como quedo resuelto.

---

## 1. El programa se caia si un algoritmo no encontraba camino

**Problema.** Los cinco algoritmos devuelven `None` cuando la meta es
inalcanzable, pero `summarize_results` accedia a las llaves del resultado sin
verificarlo:

```python
"estados_explorados": len(result["expansion_order"])
```

Con un laberinto sin solucion el programa terminaba en:

```text
TypeError: 'NoneType' object is not subscriptable
```

Lo mismo ocurria en las seis llamadas a `maze1.show(path=...["path"])`.

**Por que no se detecto.** Solo se probaba `maze1.txt`, que si tiene solucion.

**Solucion.** `summarize_results` ahora deja los campos numericos en `None` y la
tabla imprime `sin sol.` en esa fila. Las figuras se omiten para los algoritmos
sin resultado.

---

## 2. Las rutas relativas rompian la ejecucion

**Problema.** El laberinto se cargaba asi:

```python
maze1 = Maze("mazes/maze1.txt")
```

Esa ruta depende del directorio desde donde se ejecuta el script, no de donde
esta el archivo. Al correrlo desde la carpeta padre:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'mazes\maze1.txt'
```

**Solucion.** Las rutas se calculan desde la ubicacion del archivo:

```python
BASE_DIR = Path(__file__).parent
MAZES_DIR = BASE_DIR / "mazes"
FIGURAS_DIR = BASE_DIR / "figuras"
```

---

## 3. Habia codigo definido que nunca se usaba

**Problema.** Tres piezas estaban escritas pero muertas:

```text
run_all()             definida, nunca llamada
weighted_manhattan()  definida, nunca llamada
explored en UCS       se llenaba, nunca se consultaba
```

Ademas, el bloque `__main__` repetia a mano exactamente lo que ya hacia
`run_all`, duplicando cinco llamadas.

**Solucion.** `run_all` es ahora el unico punto de ejecucion,
`weighted_manhattan` se usa en el Experimento 2, y el `explored` sobrante de UCS
se elimino porque el diccionario `best_cost` ya cumplia esa funcion.

---

## 4. La clase Node no era comparable

**Problema.** `PriorityFrontier` guarda tuplas `(prioridad, contador, nodo)`. El
contador evita comparar nodos, pero si alguien modificaba esa estructura el
programa fallaba con `TypeError: '<' not supported between instances of 'Node'`.

**Solucion.** Se agrego el metodo de comparacion como respaldo:

```python
def __lt__(self, other):
    return self.cost < other.cost
```

---

## 5. Faltaba declarar las dependencias

**Problema.** El script importa `matplotlib` y `numpy` en la primera linea. Si
`matplotlib` no esta instalado, el programa no arranca:

```text
ModuleNotFoundError: No module named 'matplotlib'
```

**Solucion.** Se agrego `requirements.txt` y el import de matplotlib quedo
opcional. Sin la libreria el script corre completo y solo avisa que omite las
graficas:

```python
try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False
```

Para instalar las dependencias:

```powershell
pip install -r requirements.txt
```

---

## 6. Solo existia un laberinto de prueba

**Problema.** Con un unico mapa no se puede afirmar que el comportamiento de los
algoritmos sea general. Tampoco se ejercitaba el retorno `None`.

**Solucion.** Se agregaron dos laberintos:

```text
mazes/maze2.txt                topologia distinta, 9x11
mazes/maze3_sin_solucion.txt   meta encerrada tras un muro, 5x9
```

El tercero incluye una verificacion de que los cinco algoritmos devuelven `None`.

---

## 7. No existia una tabla comparativa

**Problema.** La salida era una lista vertical por algoritmo, lo que dificulta
compararlos, que es el objetivo del taller.

**Solucion.** La funcion `print_table` imprime una tabla y marca cual alcanzo el
costo minimo:

```text
Algoritmo   Explorados   Pasos   Costo   Optimo
-----------------------------------------------
DFS                 69      64      64       no
BFS                106      28      28       si
UCS                106      28      28       si
Greedy              33      32      32       no
A*                  59      28      28       si
```

---

## 8. Nadie verificaba que el camino fuera valido

**Problema.** Los `assert` solo revisaban el primer nodo, el ultimo y el costo.
Un camino que atravesara un muro o saltara celdas habria pasado la prueba.

**Solucion.** La funcion `validate_path` recorre el camino completo y confirma
que cada par de celdas consecutivas sea adyacente y que ninguna sea muro. Se
aplica automaticamente a los cinco algoritmos en cada laberinto.

---

## 9. Faltaba demostrar la pregunta 4 con codigo

**Problema.** El documento afirmaba que con `h(n) = 0` el algoritmo A* equivale a
UCS, pero solo como texto.

**Solucion.** El Experimento 1 lo comprueba ejecutando ambos y comparando el
orden de expansion completo:

```text
Experimento 1: A* con h(n) = 0 frente a UCS
  UCS         -> costo 28, explorados 106
  A* con h=0  -> costo 28, explorados 106
  Mismo orden de expansion: si
```

---

## 10. Faltaba el experimento de heuristica no admisible

**Problema.** `weighted_manhattan` sugeria un experimento sobre que pasa cuando
la heuristica sobreestima, pero nunca se ejecutaba.

**Solucion.** El Experimento 2 compara ambas heuristicas:

```text
Experimento 2: heuristica admisible frente a heuristica ponderada
  A* Manhattan (admisible) -> costo 28, explorados 59
  A* ponderada (x3)        -> costo 28, explorados 35
  En este laberinto mantuvo el optimo, pero no esta garantizado.
```

La version ponderada explora un 40 por ciento menos de estados. En `maze1`
mantuvo el costo optimo, pero al sobreestimar pierde la garantia y en otros
laberintos puede devolver un camino peor.

---

## 11. Las visualizaciones bloqueaban el programa

**Problema.** Se llamaba seis veces a `plt.show()` de forma consecutiva. Cada
ventana detiene la ejecucion hasta que el usuario la cierra, y las imagenes no
quedaban guardadas.

**Solucion.** El metodo `show` acepta el parametro `save_as`. Cuando se usa,
guarda un PNG en `figuras/` sin abrir ventanas:

```python
maze.show(path=..., explored=..., title=..., save_as="maze1_BFS.png")
```

---

## Resumen de archivos

```text
02_busqueda_en_laberintos.py   codigo corregido y comentado
CAMBIOS_IMPLEMENTACION.md      documento original de implementacion
CORRECCIONES.md                este documento
requirements.txt               dependencias
mazes/maze1.txt                laberinto del taller
mazes/maze2.txt                laberinto adicional
mazes/maze3_sin_solucion.txt   laberinto sin camino a la meta
```

## Como ejecutar

```powershell
pip install -r requirements.txt
python 02_busqueda_en_laberintos.py
```

El script imprime las tablas de los tres laberintos, corre los dos experimentos,
valida todos los caminos y guarda las figuras de `maze1` en `figuras/`.
