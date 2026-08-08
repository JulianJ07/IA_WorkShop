# Cambios e implementacion del proyecto

Este documento resume la implementacion del taller de Hill Climbing y Random
Restart.

## Archivos agregados

Se agrego el archivo principal:

```text
01_hill_climbing.py
```

Este archivo contiene el codigo del notebook en formato ejecutable de Python,
organizado por secciones numeradas como `Codigo 1`, `Codigo 2`, `Codigo 3`, etc.

Las figuras ya no se abren en ventanas: se guardan en

```text
figuras/
```

## Organizacion del codigo

```text
Codigo 1:  imports y setup
Codigo 2:  metricas de distancia (Manhattan y euclidea)
Codigo 3:  representacion del problema HospitalWorld
Codigo 4:  vecindario parametrizado por radio
Codigo 5:  visualizacion de la cuadricula
Codigo 6:  validacion de estados
Codigo 7:  Hill Climbing
Codigo 8:  Random Restart
Codigo 9:  optimo global por fuerza bruta
Codigo 10: utilidades de impresion
Codigo 11: algoritmo base
Codigo 12: Actividad 1, distancia euclidea
Codigo 13: Actividad 2, numero de hospitales
Codigo 14: Actividad 3, diseno del vecindario
Codigo 15: experimentos adicionales
Codigo 16: ejecucion completa
```

## El problema

En una cuadricula de `10 x 16` hay 18 casas y se quieren ubicar `k` hospitales.
El costo de una solucion es la suma de la distancia de cada casa al hospital mas
cercano:

```text
min sobre H de la suma, para cada casa c, de la distancia de c al hospital
mas cercano de H
```

Un estado es el conjunto de posiciones de los hospitales. Un vecino se obtiene
moviendo **un** hospital a una celda libre cercana.

## La clase HospitalWorld

Se agrupo el problema en una clase, igual que `Maze` en el taller anterior:

```python
class HospitalWorld:
    def in_bounds(self, cell)                  # limites de la cuadricula
    def available_cells(self)                  # celdas sin casa, ordenadas
    def random_state(self, num_hospitals, rng) # estado inicial aleatorio
    def cost(self, hospitals, metric)          # funcion objetivo
    def neighbors(self, hospitals, radius)     # vecindario
    def show(self, hospitals, title, save_as)  # figura
```

La metrica es un parametro de `cost`, no una funcion aparte. Eso es lo que
permite que la Actividad 1 reutilice exactamente el mismo algoritmo.

## Implementacion del vecindario

El vecindario quedo parametrizado por un radio Manhattan, en vez de escribir una
funcion distinta para cada caso:

```python
moves = [
    (dr, dc)
    for dr in range(-radius, radius + 1)
    for dc in range(-radius, radius + 1)
    if (dr or dc) and abs(dr) + abs(dc) <= radius
]
```

Con `radius=1` salen los cuatro movimientos del enunciado. Con `radius=2` se
agregan los ocho saltos de dos celdas, que es lo que pide la Actividad 3.

Un vecino se descarta si sale de la cuadricula, si cae sobre una casa o si cae
sobre otro hospital.

## Implementacion de Hill Climbing

```python
def hill_climbing(world, num_hospitals, metric=manhattan, radius=1,
                  initial_state=None, max_iterations=200, max_sideways=0,
                  rng=None):
```

En cada iteracion genera todos los vecinos, evalua sus costos y se mueve al
mejor. La diferencia con la version del notebook esta en como termina. Antes
habia una sola condicion:

```python
if best_cost >= current_cost:
    break
```

Esa linea junta dos situaciones distintas. Ahora se separan:

```python
if best_cost > current_cost:
    motivo = "optimo_local"      # ningun vecino iguala siquiera
    break

if best_cost == current_cost:
    motivo = "meseta"            # hay empate, el terreno es plano
    break
```

Distinguirlas era necesario porque las mesetas son un objetivo declarado del
taller, y resultan ser el caso mas frecuente: 179 de 200 corridas.

El parametro `max_sideways` permite aceptar movimientos de igual costo para
atravesar una meseta, con un limite para no quedar dando vueltas dentro de ella.

La funcion devuelve un diccionario:

```text
solution       conjunto final de hospitales
history        costo en cada iteracion
states         trayectoria completa de estados
evaluaciones   vecinos evaluados en total
iteraciones    iteraciones con mejora
motivo         optimo_local, meseta, sin_vecinos o max_iteraciones
```

## Implementacion de Random Restart

```python
def random_restart(world, num_hospitals, metric=manhattan, radius=1,
                   restarts=40, max_sideways=0, seed=0):
```

Un generador maestro deriva una semilla por corrida, de modo que toda la
ejecucion es reproducible a partir de un unico `seed`:

```python
master_rng = random.Random(seed)
run_seed = master_rng.randrange(10**9)
```

## Resultados principales

Algoritmo base, vecindario de 1 paso, semilla 8:

```text
Costo inicial           : 87
Costo final             : 62
Iteraciones con mejora  : 9
Vecinos evaluados       : 87
Motivo de parada        : meseta
```

Random Restart con 40 reinicios:

```text
Mejor costo          : 56
Peor costo           : 87
Costo promedio       : 64.97
Corridas en el mejor : 3 de 40
```

## Actividad 1: distancia euclidea

Cada solucion se evalua con las dos metricas, porque comparar un costo euclideo
contra uno Manhattan no dice nada:

```text
Solucion      Hospitales             Costo Manhattan  Costo euclideo  Iter
--------------------------------------------------------------------------
HC manhattan  (2, 5) (3, 12) (7, 6)  62               53.76           9
HC euclidea   (2, 4) (5, 13) (7, 6)  62               49.81           13
```

Las ubicaciones no coinciden. En Manhattan las dos empatan en 62, lo que muestra
que hay varias configuraciones con el mismo costo. En la metrica euclidea si se
separan, y cada corrida gana en la metrica que optimizo.

La euclidea penaliza menos las diagonales, asi que tiende a centrar los
hospitales en la nube de casas en vez de alinearlos con las filas y columnas.

## Actividad 2: numero de hospitales

Random Restart con 40 reinicios para cada `k`:

```text
k  Mejor costo  Reduccion  Reduccion %
--------------------------------------
1  114          -          -
2  75           39         34.2%
3  56           19         25.3%
4  46           10         17.9%
5  39           7          15.2%
```

Agregar hospitales **no** produce siempre la misma reduccion. Las reducciones
sucesivas son `39, 19, 10, 7`: cada hospital nuevo aporta menos que el anterior.

La razon es geometrica. El primer hospital tiene que cubrir toda la nube de
casas. El segundo la parte en dos grupos grandes, y de ahi en adelante cada
hospital solo puede subdividir grupos cada vez mas pequenos. El limite es claro:
con `k` igual al numero de casas el costo seria 0.

## Actividad 3: diseno del vecindario

```text
Vecindario  Costo 1 corrida  Iter  Evaluaciones  Costo con RR(40)  Evaluaciones RR
----------------------------------------------------------------------------------
1 paso(s)   62               9     87            56                3110
2 paso(s)   56               8     269           56                8706
```

En una corrida unica si mejora: baja de 62 a 56, porque el vecindario amplio
salta sobre configuraciones intermedias malas y escapa de optimos locales que
atrapan al de un paso.

El numero de vecinos por iteracion pasa de 10 a 31 en el estado inicial, unas
3.1 veces mas.

Con Random Restart los dos llegan a 56, pero el de 2 pasos gasta 8706
evaluaciones contra 3110. Ampliar el vecindario y reiniciar atacan el mismo
problema: escapar de optimos locales. Si ya se usa Random Restart, el vecindario
grande solo agrega costo de computo.

## Experimentos adicionales

```text
Experimento 1  optimo global por fuerza bruta como referencia
Experimento 2  optimos locales frente a mesetas
Experimento 3  dependencia del estado inicial
Experimento 4  cuantos reinicios hacen falta
```

El Experimento 1 confirma que 56 es el optimo global, revisando las 467180
combinaciones posibles.

El Experimento 4 muestra donde deja de rendir el reinicio:

```text
Reinicios  Mejor costo  Es el optimo global  Evaluaciones
---------------------------------------------------------
1          62           no                   65
5          57           no                   377
10         57           no                   679
20         56           si                   1503
40         56           si                   3110
80         56           si                   6534
```

## Como ejecutar

```powershell
pip install -r requirements.txt
python 01_hill_climbing.py
```

## Verificaciones realizadas

Se verifico que el archivo compila:

```powershell
python -m py_compile 01_hill_climbing.py
```

Toda solucion devuelta pasa por `validar_estado`, que confirma que hay
exactamente `k` hospitales, que todos estan dentro de la cuadricula y que
ninguno quedo sobre una casa. El historial pasa por `validar_historial`, que
confirma que el costo nunca sube entre iteraciones.

Se confirmo tambien que la ejecucion es reproducible: dos corridas con la misma
semilla dan resultados identicos.

---

# Preguntas de cierre

### 1. Por que Hill Climbing no necesita construir todo el espacio de busqueda?

Porque en cada momento solo necesita dos cosas: el estado actual y sus vecinos
inmediatos. Nunca guarda una frontera ni una lista de explorados, como si hacen
DFS, BFS o A*.

En este problema el espacio completo tiene 467180 estados para `k = 3`. Hill
Climbing llega a un optimo local evaluando 87 vecinos, es decir menos del 0.02
por ciento del espacio.

El precio de esa economia es que solo ve el terreno que tiene al lado. No sabe
que hay mas alla de sus vecinos, y por eso no puede darse cuenta de que existe
una solucion mejor en otra region.

### 2. El resultado depende del estado inicial?

Si, y bastante. Sobre 200 corridas desde estados iniciales distintos:

```text
Costos finales distintos : 32
Rango                    : 56 a 96
Promedio                 : 65.93
Llegaron al mejor        : 10 (5.0%)
```

El mismo algoritmo, sobre el mismo problema, produce 32 resultados distintos
segun donde empiece, y el peor es casi el doble de costoso que el mejor. Solo el
5 por ciento de los estados iniciales conduce al optimo global.

Esa dependencia es precisamente la razon de ser de Random Restart.

### 3. Random Restart garantiza encontrar el optimo global?

No lo garantiza. Cada reinicio es independiente y ninguno tiene forma de saber
si el resultado al que llego es el optimo global; el algoritmo solo puede
comparar entre las corridas que hizo.

Lo que hace es aumentar la probabilidad. Si un estado inicial cualquiera lleva
al optimo con probabilidad `p`, con `n` reinicios la probabilidad de fallar en
todos es `(1 - p)^n`, que baja rapido pero nunca llega a cero. Aqui `p` es
aproximadamente `0.05`, y se ve el efecto:

```text
Reinicios  Mejor costo  Es el optimo global
-------------------------------------------
1          62           no
5          57           no
10         57           no
20         56           si
40         56           si
80         56           si
```

Con 20 reinicios lo encontro, pero eso es un resultado de esta corrida, no una
garantia. En este taller se puede afirmar que 56 es el optimo global unicamente
porque la fuerza bruta lo confirmo aparte.

La unica forma de garantizarlo es recorrer todo el espacio, que es justo lo que
Hill Climbing evita hacer.

### 4. Que informacion se pierde al conservar unicamente el mejor vecino?

Se pierden tres cosas distintas.

**Los vecinos descartados.** En cada iteracion se calcula el costo de todos los
vecinos y se usa solo el minimo. Un vecino que hoy es apenas peor puede ser la
entrada a una region mucho mejor, y esa informacion se bota apenas se calcula.
Es exactamente lo que se ve en la Actividad 3: el vecindario de 2 pasos llega a
56 y el de 1 paso se queda en 62, y la diferencia esta en configuraciones
intermedias que el de 1 paso nunca llega a considerar.

**La trayectoria recorrida.** Al guardar solo el estado actual, el algoritmo no
recuerda por donde paso. No puede evitar volver sobre sus pasos ni retroceder a
una bifurcacion anterior para probar otra rama, que es lo que si hacen los
algoritmos con frontera.

**La forma del paisaje.** Conservar solo el mejor costo hace que un empate y una
subida se vean igual, y por eso el algoritmo no distingue un optimo local de una
meseta. En este problema esa distincion no es un detalle: 179 de 200 corridas se
detienen en una meseta y no en un optimo local. Al recuperar esa informacion se
puede aplicar movimientos laterales, y el costo promedio baja de 64.97 a 60.85.
