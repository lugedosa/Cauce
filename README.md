# Cauce

**Calcular, validar y publicar.** Un lenguaje experimental de celdas inmutables,
funciones puras y salida condicionada por invariantes, diseñado por IA a petición
de Luis. Este repositorio contiene un intérprete funcional 0.1.0 en Python.

```cau
input personas: Int = 4;
cell total = costo(personas) + envio;
cell envio = 80;
fn costo(n: Int) -> Int = n * 250;
require total <= 1200, "Se supera el presupuesto";
emit "Total: " + text(total);
```

Resultado: `Total: 1080`. Cambiar `personas` a 5 hace fallar la condición sin
publicar salidas del programa. Las celdas pueden declararse después de sus usos;
los ciclos y los errores de tipos se detectan antes de ejecutar.

## Probarlo

Requiere Python 3.11 o posterior. Desde esta carpeta, sin instalar dependencias:

```console
python -m cauce run examples/presupuesto.cau
python -m cauce run examples/presupuesto.cau --set personas=3
python -m cauce check examples/funciones.cau
python -m cauce graph examples/presupuesto.cau
python -m unittest discover -s tests -v
```

La primera ejecución publica `Total: 1000` y `Envío: 0`. Con tres personas publica
`Total: 830` y `Envío: 80`. `--set` recibe JSON: usa enteros, `true`/`false`, listas
o cadenas JSON correctamente entrecomilladas según tu terminal. Se puede repetir
para distintas entradas. Solo `run` acepta sustituciones.

Instalación opcional en un entorno virtual: `python -m pip install -e .`.
Después puede usarse `cauce run archivo.cau`. La instalación puede descargar
herramientas de empaquetado; la ejecución directa no necesita red.

## Qué hay implementado

- Tipado estático: Int, Bool, Text y listas homogéneas; sin coerciones implícitas.
- Celdas evaluadas una vez por ejecución y entradas con valores iniciales literales.
- Funciones puras con firmas explícitas, referencias adelantadas y sin recursión.
- Condicionales, cortocircuito, operadores y `len`, `sum`, `range`, `text`.
- Validaciones `require` previas a todas las publicaciones `emit`.
- Diagnósticos con posiciones, CLI, API, ejemplos de éxito y de error, tests y CI.

El grafo se ejecuta secuencialmente. No hay compilación nativa, concurrencia,
reactividad incremental, acceso a archivos desde Cauce, módulos o sandbox. Todas
las celdas se calculan antes de comprobar `require`; usar `if` dentro de una
expresión para proteger una operación como una división por cero.

El objetivo práctico es explorar cálculos reproducibles y pequeños flujos de
datos. No es una afirmación de novedad absoluta o de superioridad: no se han hecho
comparativas de rendimiento ni una revisión exhaustiva de trabajos previos.
El nombre es provisional y la compatibilidad entre versiones aún no es estable.

## API y estructura

```python
from cauce import CauceError, check, run

source = 'input n: Int = 2; cell doble = n * 2; emit doble;'
plan = check(source)  # Valida sin ejecutar; plan.order contiene el orden de celdas.
assert run(source, {"n": 7}) == ["14"]
```

`run` devuelve todas las salidas formateadas o lanza `CauceError`. No escribe por
su cuenta. La garantía ante error del lenguaje cubre toda la preparación de las
salidas, no fallos del dispositivo durante su escritura. La CLI usa stderr para
diagnósticos y devuelve 0 en éxito, 1 en error de programa/archivo y 2 en uso inválido.

| Ruta | Contenido |
| --- | --- |
| [docs/DESIGN.md](docs/DESIGN.md) | Filosofía, decisiones, costes y garantías |
| [docs/SPEC.md](docs/SPEC.md) | Gramática y semántica del MVP |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Etapas y criterios de aceptación |
| `cauce/syntax.py` | Lexer, AST y parser |
| `cauce/runtime.py` | Tipos, grafo e intérprete |
| `cauce/cli.py` | Terminal |
| `examples/` | Programas ejecutables y errores intencionales |
| `tests/` | Pruebas de semántica y CLI |
| [docs/PUBLISH.md](docs/PUBLISH.md) | Preparación para GitHub |

Para contribuir, incluye un caso mínimo, una decisión semántica explícita y una
prueba de regresión. Consulta [CONTRIBUTING.md](CONTRIBUTING.md). Licencia MIT.
