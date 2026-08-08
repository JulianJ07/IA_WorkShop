# Cambios e implementacion del proyecto

Este documento resume los cambios realizados al proyecto de busqueda en laberintos.

## Archivos agregados

Se agrego el archivo principal:

```text
02_busqueda_en_laberintos.py
```

Este archivo contiene el codigo del notebook en formato ejecutable de Python, organizado por secciones numeradas como `Codigo 1`, `Codigo 2`, `Codigo 3`, etc.

Tambien se agrego la carpeta:

```text
mazes/
```

Dentro de ella estan el archivo del laberinto:

```text
mazes/maze1.txt
```

Ese archivo contiene el diseno del laberinto usando caracteres:

```text
# = muro
  = camino libre
A = punto inicial
B = meta
```

## Organizacion del codigo

El archivo `02_busqueda_en_laberintos.py` quedo separado con comentarios de seccion:

```text
Codigo 1: imports y setup
Codigo 2: representacion del problema Maze
Codigo 3: estructuras comunes de busqueda
Codigo 4: DFS con StackFrontier
Codigo 5: BFS con QueueFrontier
Codigo 6: UCS con PriorityFrontier
Codigo 7: heuristica distancia Manhattan
Codigo 8: Greedy Best-First Search
Codigo 9: A star
Codigo 10: comparacion final y experimentos
```

Esto permite ubicar facilmente cada bloque del notebook original dentro del archivo `.py`.

## Implementacion del Codigo 5: BFS

Se completo la clase `QueueFrontier`, que representa una cola FIFO.

La diferencia principal frente a DFS es que DFS usa una pila y elimina el ultimo elemento:

```python
return self.frontier.pop()
```

Mientras que BFS elimina el primer elemento:

```python
return self.frontier.pop(0)
```

Tambien se implemento la funcion:

```python
def breadth_first_search(maze, start, goal, verbose=False):
```

Esta funcion:

1. Crea una frontera tipo cola.
2. Agrega el nodo inicial.
3. Expande estados por niveles.
4. Evita repetir estados ya explorados o ya presentes en la frontera.
5. Retorna el camino, el orden de expansion y el costo.

BFS encuentra el camino mas corto cuando todos los pasos cuestan lo mismo.

## Implementacion del Codigo 8: Greedy Best-First Search

Se implemento:

```python
def greedy_best_first_search(maze, heuristic, start, goal, verbose=False):
```

Este algoritmo usa una cola de prioridad, pero su prioridad depende solo de la heuristica:

```python
priority = heuristic(child_state, goal)
```

En este caso se usa la distancia Manhattan:

```python
def manhattan(state, goal):
    return abs(state[0] - goal[0]) + abs(state[1] - goal[1])
```

Greedy intenta acercarse rapidamente a la meta, pero no garantiza el camino optimo porque ignora el costo acumulado.

## Implementacion del Codigo 9: A*

Se implemento:

```python
def a_star_search(maze, heuristic, start, goal, verbose=False):
```

A* combina el costo acumulado con la heuristica:

```python
priority = new_cost + heuristic(child_state, goal)
```

Es decir:

```text
f(n) = g(n) + h(n)
```

Tambien mantiene un diccionario `best_cost` para recordar el mejor costo encontrado hasta cada estado:

```python
best_cost = {start: 0}
```

Esto permite actualizar rutas si aparece una mejor forma de llegar a una celda.

Con la heuristica Manhattan, A* encuentra el camino optimo en este laberinto.

## Correccion del tamano del laberinto

Se detecto que algunas filas de `maze1.txt` tenian espacios sobrantes al final. Eso hacia que el programa interpretara el laberinto como si algunas filas tuvieran ancho 18, aunque visualmente parecia de 17 columnas.

El ancho se calcula en la clase `Maze` con:

```python
self.width = max(len(line) for line in lines)
```

Por eso, si una sola fila tenia un espacio extra, todo el laberinto podia mostrarse con una columna adicional.

Para corregirlo, se hicieron dos ajustes:

1. Se eliminaron los espacios sobrantes de `mazes/maze1.txt`.
2. Se cambio la lectura de lineas para limpiar espacios finales:

```python
lines = [line.rstrip() for line in contents.splitlines()]
```

Con esto, el laberinto queda correctamente como una matriz de `17 x 17`.

## Visualizacion del laberinto

La clase `Maze` ya tenia el metodo:

```python
def show(self, path=None, explored=None, title="Laberinto", figsize=(6, 6)):
```

Pero el script no lo estaba llamando al final. Por eso solo se veian los resultados en texto.

Se agregaron llamadas a `maze1.show(...)` para mostrar:

```text
Maze 1: problema inicial
DFS: estados explorados y solucion
BFS: estados explorados y solucion
UCS: estados explorados y solucion
Greedy Best-First Search
A* con distancia Manhattan
```

## Salida organizada en consola

Tambien se cambio la impresion final para que no aparezca una lista larga en una sola linea.

Ahora la salida se muestra por algoritmo:

```text
Resultados sobre maze1:

Algoritmo: DFS
  Estados explorados: ...
  Longitud del camino: ...
  Costo del camino: ...

Algoritmo: BFS
  Estados explorados: ...
  Longitud del camino: ...
  Costo del camino: ...
```

## Como ejecutar

Desde la carpeta del proyecto:

```powershell
python 02_busqueda_en_laberintos.py
```

El programa imprime los resultados en consola y abre las visualizaciones del laberinto con Matplotlib.

## Verificaciones realizadas

Se verifico que el archivo compila correctamente con:

```powershell
python -m py_compile 02_busqueda_en_laberintos.py
```

Tambien se ejecuto el proyecto y se confirmaron los resultados principales sobre `maze1`:

```text
BFS costo: 28
Greedy costo: 32
A* costo: 28
```

## Preguntas de cierre

### 1. Que algoritmos garantizan el camino de menor numero de pasos?

Cuando todas las acciones tienen el mismo costo, como ocurre en este laberinto donde cada movimiento cuesta `1`, el algoritmo que garantiza encontrar el camino con menor numero de pasos es:

```text
BFS
```

BFS explora el laberinto por niveles. Primero revisa todos los estados a distancia 1 del inicio, luego todos los estados a distancia 2, luego distancia 3, y asi sucesivamente. Por eso, cuando encuentra la meta por primera vez, esa ruta tiene la menor cantidad posible de pasos.

A* tambien encuentra el camino con menor numero de pasos en este caso, porque los costos son uniformes y la heuristica Manhattan es admisible.

### 2. Que algoritmos garantizan el camino de menor costo?

Los algoritmos que garantizan el camino de menor costo son:

```text
UCS
A*
```

UCS lo garantiza porque siempre expande primero el nodo con menor costo acumulado:

```text
g(n)
```

A* tambien lo garantiza si la heuristica es admisible, es decir, si nunca sobreestima el costo real hasta la meta. En este proyecto se usa la distancia Manhattan, que es admisible para movimientos arriba, abajo, izquierda y derecha.

BFS tambien encuentra el menor costo en este laberinto porque todos los movimientos cuestan `1`. Sin embargo, si los costos fueran diferentes, BFS ya no garantizaría el menor costo.

### 3. Por que Greedy puede encontrar un camino suboptimo aunque explore muy pocos estados?

Greedy Best-First Search decide que nodo expandir usando solamente la heuristica:

```text
h(n)
```

Eso significa que elige el estado que parece estar mas cerca de la meta, pero no toma en cuenta cuanto costo ya lleva acumulado desde el inicio.

Por eso puede meterse en un camino que parece prometedor segun la distancia Manhattan, pero que en realidad obliga a dar un rodeo. En el `maze1`, Greedy explora menos estados que BFS o UCS, pero encuentra un camino de costo `32` en lugar del optimo de costo `28`.

### 4. Que ocurre con A* si h(n) = 0 para todos los nodos?

A* usa esta funcion de prioridad:

```text
f(n) = g(n) + h(n)
```

Si la heuristica vale `0` para todos los nodos, entonces:

```text
f(n) = g(n) + 0
```

Por lo tanto:

```text
f(n) = g(n)
```

En ese caso, A* se comporta igual que Uniform Cost Search, porque solo usa el costo acumulado para decidir que nodo expandir.

Entonces, si `h(n) = 0` para todos los nodos, A* se convierte en:

```text
UCS
```

En el notebook de grafos, seria equivalente a la busqueda de costo uniforme.

### 5. Que efecto tiene el orden en que neighbors() genera las direcciones sobre DFS y BFS?

El metodo `neighbors()` genera los vecinos en este orden:

```python
candidates = [
    (row - 1, col),  # arriba
    (row + 1, col),  # abajo
    (row, col - 1),  # izquierda
    (row, col + 1),  # derecha
]
```

Ese orden afecta el orden en que los algoritmos exploran el laberinto.

En DFS, el efecto puede ser muy grande, porque DFS sigue una rama hasta el fondo antes de retroceder. Si el orden de vecinos cambia, DFS puede tomar primero otro pasillo y encontrar una solucion muy diferente.

En BFS, el orden de vecinos no cambia la garantia de encontrar el camino mas corto cuando todos los costos son iguales. Sin embargo, si existen varios caminos optimos con la misma longitud, el orden de `neighbors()` determina cual de esos caminos se encuentra primero.
