# Correcciones y faltantes del proyecto

Este documento lista los errores encontrados en la version anterior del notebook
`01_hill_climbing.ipynb` y lo que hacia falta para completar el taller. Cada
punto indica el problema, por que importaba y como quedo resuelto en
`01_hill_climbing.py`.

---

## 1. La funcion de la Actividad 1 ignoraba la semilla que recibia

**Problema.** `hill_c` declaraba el parametro `rng` y en la primera linea lo
pisaba:

```python
def hill_c(..., rng=None):
    rng = random.Random()      # descarta el argumento recibido
```

Todas las llamadas pasaban `rng=random.Random(SEED)`, pero ese argumento no
tenia ningun efecto: el algoritmo corria con la semilla aleatoria del sistema.

**Por que importaba.** Las Actividades 1 y 3 dejaban de ser reproducibles. El
caso grave era `random_restart_generic`, que llama a `hill_c` **sin**
`initial_state`, asi que hasta los estados iniciales de los 40 reinicios salian
del generador roto. El parametro `seed=SEED` de esa funcion era decorativo.

Comprobado con `restarts=3` y la misma semilla, cinco corridas seguidas:

```text
con el bug   (2,4),(3,12),(7,3) / (2,4),(3,12),(6,4) / (2,5),(6,14),(7,3) / ...
corregido    siempre (2,4),(3,12),(6,4)
```

Con 40 reinicios el costo final igual daba 56 por suerte, asi que el error
quedaba camuflado.

**Solucion.** Se restauro la forma correcta, que ya estaba bien en la funcion
`hill_climbing` original del notebook:

```python
rng = rng or random.Random()
```

---

## 2. La Actividad 1 comparaba unidades distintas

**Problema.** El notebook imprimia el costo euclideo de la solucion euclidea
(`46.70`) y lo dejaba junto al costo Manhattan de la solucion Manhattan (`62`).
Esos dos numeros no se pueden comparar: miden cosas diferentes. Ademas el
enunciado pedia comparar tambien la **ubicacion** de los hospitales, y eso no
aparecia.

**Solucion.** Cada solucion se evalua ahora con **las dos** metricas, de modo
que las columnas si son comparables:

```text
Solucion      Hospitales             Costo Manhattan  Costo euclideo  Iter
--------------------------------------------------------------------------
HC manhattan  (2, 5) (3, 12) (7, 6)  62               53.76           9
HC euclidea   (2, 4) (5, 13) (7, 6)  62               49.81           13
```

En Manhattan las dos empatan en 62 aunque los hospitales estan en celdas
distintas: existen varias configuraciones con el mismo costo. En la metrica
euclidea si se separan, y cada corrida gana en la metrica que optimizo.

---

## 3. Faltaban las discusiones que pedian las tres actividades

**Problema.** Las tres actividades terminaban en un `print` o en una lista, sin
la conclusion que el enunciado pedia explicitamente:

```text
Actividad 1  "Compara la ubicacion de los hospitales y el costo"   no estaba
Actividad 2  "discute si agregar hospitales produce siempre la
              misma reduccion"                                      no estaba
Actividad 3  "Mejora el resultado?"                                 no estaba
```

La Actividad 2 solo dejaba la lista `[(1, 114), (2, 76), ...]` sin interpretarla.

**Solucion.** Cada actividad imprime ahora su tabla y debajo la discusion. En la
Actividad 2 se agrego la columna de reduccion, que es justamente lo que la
pregunta pedia mirar:

```text
k  Mejor costo  Reduccion  Reduccion %
--------------------------------------
1  114          -          -
2  75           39         34.2%
3  56           19         25.3%
4  46           10         17.9%
5  39           7          15.2%
```

Las reducciones no son constantes: son rendimientos decrecientes.

---

## 4. La Actividad 3 comparaba dos implementaciones distintas

**Problema.** El caso de 1 paso usaba `hill_climbing` y el de 2 pasos usaba
`hill_c`, que ademas tenia el error del punto 1. La diferencia observada no se
podia atribuir al vecindario, porque habia mas de una variable cambiando.

**Solucion.** Existe una sola funcion `hill_climbing` con el vecindario como
parametro (`radius`), y los dos casos corren con la misma semilla:

```python
world.neighbors(hospitals, radius=1)   # 4 movimientos del enunciado
world.neighbors(hospitals, radius=2)   # agrega los saltos de 2 celdas
```

---

## 5. No se contaba el costo real de la exploracion

**Problema.** La Actividad 3 pregunta cuanto aumenta el numero de vecinos
evaluados. El notebook solo informaba el tamano del vecindario en el estado
inicial (12 y 31), que no es lo mismo que el total evaluado durante la corrida.

**Solucion.** `hill_climbing` lleva un contador `evaluaciones`. Con eso la
comparacion queda completa:

```text
Vecindario  Costo 1 corrida  Iter  Evaluaciones  Costo con RR(40)  Evaluaciones RR
----------------------------------------------------------------------------------
1 paso(s)   62               9     87            56                3110
2 paso(s)   56               8     269           56                8706
```

El vecindario amplio mejora la corrida unica, pero con Random Restart los dos
llegan al mismo costo y el de 2 pasos gasta 2.8 veces mas computo.

---

## 6. Las mesetas eran un objetivo declarado y no se tocaban

**Problema.** Los objetivos del notebook incluyen "identificar optimos locales y
**mesetas**", pero las mesetas no aparecian en ninguna parte. La linea que corta
el ciclo:

```python
if best_cost >= current_cost:
    break
```

se detiene en los dos casos con la misma condicion, asi que era imposible
distinguirlos mirando solo el costo final.

**Solucion.** `hill_climbing` devuelve el campo `motivo`, que separa
`optimo_local` (ningun vecino empata) de `meseta` (al menos uno empata). Sobre
200 corridas:

```text
Motivo de parada  Corridas de 200
---------------------------------
meseta            179
optimo_local      21
```

Es decir, casi el 90 por ciento de las corridas no se detienen en un optimo
local sino en una meseta. Se agrego ademas el parametro `max_sideways`, que
permite aceptar movimientos de igual costo para atravesarlas:

```text
Movs. laterales  Mejor costo  Costo promedio  Evaluaciones
----------------------------------------------------------
0                56           64.97           3110
10               56           60.85           6619
50               56           60.85           16066
```

El costo promedio baja de 64.97 a 60.85 a cambio del doble de evaluaciones. El
limite es necesario: sin el, el algoritmo puede quedarse dando vueltas dentro de
la meseta sin avanzar.

---

## 7. No habia con que comparar el resultado

**Problema.** El notebook reportaba costo 56 con Random Restart, pero nada
permitia saber si ese numero era bueno, malo o ya optimo.

**Solucion.** La funcion `optimo_global` recorre las 467180 combinaciones
posibles de 3 hospitales y confirma que 56 **es** el optimo global:

```text
Optimo global (fuerza bruta) : 56  (2, 4) (3, 12) (6, 4)
Mejor de Random Restart      : 56  (2, 5) (5, 12) (7, 3)
```

Vale la pena notar que las celdas no coinciden: hay mas de una configuracion
optima. Solo es viable para k pequeno, y por eso se usa como referencia, no como
metodo.

---

## 8. Nadie verificaba que la solucion fuera legal

**Problema.** No habia ninguna comprobacion. Un error en la generacion de
vecinos podia colocar un hospital sobre una casa, fuera de la cuadricula, o
perder uno por el camino, y el programa habria terminado sin avisar.

**Solucion.** Toda solucion devuelta pasa por dos validaciones:

```python
validar_estado(world, hospitals, num_hospitals)  # cantidad, limites, casas
validar_historial(history)                       # el costo nunca sube
```

---

## 9. Habia codigo que se calculaba y se descartaba

**Problema.** Tres piezas sobraban o se desperdiciaban:

```text
numpy                importado y np.random.seed llamado, nunca se usa
states               calculado y devuelto en cada corrida, nunca se usa
available en hill_c  se calculaba aun cuando se pasaba initial_state
```

**Solucion.** Se elimino numpy, con lo que `requirements.txt` queda solo con
matplotlib. La trayectoria `states` ahora si se aprovecha: la figura
`04_trayectoria.png` muestra como se desplazan los hospitales desde el estado
inicial hasta el optimo local. La lista de celdas disponibles solo se calcula
cuando hace falta generar un estado aleatorio.

---

## 10. Las visualizaciones bloqueaban el programa

**Problema.** Cada `plt.show()` detiene la ejecucion hasta que el usuario cierra
la ventana, y las imagenes no quedaban guardadas en ninguna parte.

**Solucion.** El metodo `show` acepta `save_as` y guarda un PNG en `figuras/`
sin abrir ventanas. Ademas matplotlib quedo como dependencia opcional: si no
esta instalado el script corre completo y solo avisa que omite las graficas.

---

## 11. Las respuestas de cierre estaban incompletas

**Problema.** Las cuatro preguntas estaban contestadas en una linea y con
errores de ortografia ("moyoria", y sin tildes en "unicamente", "evalua",
"busqueda", "optimo", "informacion"). La respuesta 4 era imprecisa: decia solo
que se puede "saltar el optimo global".

**Solucion.** Las cuatro respuestas se reescribieron en
`CAMBIOS_IMPLEMENTACION.md`, y cada una se apoya en un experimento del script en
vez de quedarse en la afirmacion.

---

## 12. El estado inicial dependia del orden de un conjunto

**Problema.** Las celdas disponibles se construian asi:

```python
available = list(set(all_cells) - houses)
```

El orden de `list(set(...))` no esta garantizado por el lenguaje: depende del
hash y de la version de Python. Como de ahi salen los estados iniciales, dos
maquinas podian obtener resultados distintos con la misma semilla.

**Solucion.** `available_cells()` devuelve la lista ordenada, asi la semilla si
determina completamente la corrida.

**Consecuencia esperada.** Las casas son exactamente las mismas que en el
notebook (salen de la misma semilla y del mismo `all_cells`), pero el estado
inicial de los hospitales cambia, y con el los numeros de la primera corrida:

```text
                       notebook   version corregida
Costo inicial          134        87
Vecinos del inicio     12         10
Costo tras Hill Climb  62         62
Optimo global          56         56
```

El problema es el mismo y las conclusiones no cambian; solo cambia el punto de
partida.

---

## Resumen de archivos

```text
01_hill_climbing.py            codigo corregido y comentado
CAMBIOS_IMPLEMENTACION.md      documento de implementacion y preguntas de cierre
CORRECCIONES.md                este documento
requirements.txt               dependencias
figuras/                       PNG generados por el script (no versionado)
```

## Como ejecutar

```powershell
pip install -r requirements.txt
python 01_hill_climbing.py
```

El script imprime el algoritmo base, Random Restart, las tres actividades y los
cuatro experimentos, valida todas las soluciones y guarda diez figuras en
`figuras/`.
