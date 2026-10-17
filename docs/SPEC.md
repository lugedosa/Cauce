# Especificación de Cauce 0.1

Esta especificación describe el MVP implementado. En caso de divergencia, abrir
una incidencia con un programa mínimo; no asumir que el comportamiento accidental
del intérprete forma parte del lenguaje.

## Fuente y declaraciones

Archivos UTF-8 con extensión convencional `.cau`. La CLI acepta BOM. Identificadores
ASCII `[A-Za-z_][A-Za-z_0-9]*`, sensibles a mayúsculas. Los textos admiten Unicode.
Espacios y saltos de línea no son significativos. `#` inicia un comentario hasta
fin de línea. Cada declaración termina en `;`.

```ebnf
program     = { declaration } ;
declaration = "input" name ":" type "=" expression ";"
            | "cell" name [ ":" type ] "=" expression ";"
            | "fn" name "(" [ parameter { "," parameter } ] ")"
              "->" type "=" expression ";"
            | "require" expression "," string ";"
            | "emit" expression ";" ;
parameter   = name ":" type ;
type        = "Int" | "Bool" | "Text" | "[" type "]" ;
expression  = literal | name | "[" [ expression { "," expression } ] "]"
            | name "(" [ expression { "," expression } ] ")"
            | "(" expression ")" | unary expression
            | expression binary expression
            | "if" expression "then" expression "else" expression ;
unary       = "-" | "not" ;
binary      = "or" | "and" | "==" | "!=" | "<" | "<=" | ">" | ">="
            | "+" | "-" | "*" | "//" | "%" ;
literal     = integer | string | "true" | "false" ;
```

`integer` es una secuencia no vacía de dígitos decimales, sin separadores ni punto.
Los negativos usan el operador unario. `string` usa comillas dobles y escapes JSON;
no admite saltos de línea literales. No se admiten comas finales. Las llaves no
forman parte de la gramática. Las palabras de la gramática y los nombres de tipo
son reservados. Los nombres de funciones integradas también están reservados en
declaraciones. No hay módulos, mutación, funciones como valores ni llamadas por campo.

## Expresiones y tipos

Precedencia de menor a mayor: `or`; `and`; `== !=`; `< <= > >=`;
`+ -`; `* // %`; unarios. Los binarios son asociativos a la izquierda.
`not 1 == 2` intenta negar un Int y falla: escribir `not (1 == 2)`.
Las comparaciones encadenadas no son una construcción especial: `1 < 2 < 3`
falla por tipos. Un `if` consume expresiones completas y el `else` corresponde al
`if` abierto más próximo. Usar paréntesis para operar sobre el resultado completo.

| Operación | Tipos | Resultado |
| --- | --- | --- |
| `+ - * // %`, unario `-` | Int | Int |
| `+` | Text, Text | Text concatenado |
| `< <= > >=` | Int, Int | Bool |
| `== !=` | Dos valores del mismo tipo | Bool; igualdad por contenido en listas |
| `and or not` | Bool | Bool |
| `if b then x else y` | b: Bool; x e y del mismo tipo | Tipo de x |

No hay conversiones implícitas. Int no incluye Bool. La división `//` redondea
hacia menos infinito; `%` satisface `a == (a // b) * b + a % b`. Dividir por cero
es error dinámico. Los enteros tienen la precisión del anfitrión, sin anchura fija;
no hay garantía de memoria ilimitada. Text es una secuencia de puntos de código
Unicode, sin normalización automática; `len` no cuenta grafemas visuales.

Las listas son homogéneas, inmutables y pueden anidarse. `[]` requiere un tipo
esperado, recibido de una anotación de celda, firma de retorno, parámetro, `sum`,
elemento de lista contextualizado o rama alternativa de `if`. La inferencia es
dirigida de izquierda a derecha, no unificación global: `cell xs = [[], [1]];`
se rechaza, mientras `cell xs: [[Int]] = [[], [1]];` se acepta. No hay indexación.

## Entradas, celdas y funciones

`input` exige tipo y valor inicial literal (incluidas listas y enteros negativos).
No acepta referencias, cálculos, condicionales o llamadas como valor inicial.
`--set nombre=JSON` sustituye solo entradas; valores y listas se validan exactamente,
sin convertir cadenas o flotantes a enteros. Una lista externa vacía es válida si
su tipo declarado es lista. Una sustitución no evita comprobar el fuente original.

Celdas y funciones permiten referencias hacia adelante. Todas las declaraciones
comparten un espacio de nombres sin duplicados. Las funciones requieren tipos en
todos los parámetros y el retorno; parámetros duplicados o que oculten funciones
se rechazan. Las funciones solo leen parámetros y llaman funciones puras. No
capturan entradas o celdas. Pueden recibir cualquier tipo del MVP.

Se rechazan ciclos de dependencias entre celdas y ciclos de llamadas entre
funciones, incluyendo autorreferencias y referencias en ramas inalcanzables.
Todo el programa se comprueba, incluidas funciones y celdas sin uso. Primero se
validan las funciones; después se infieren celdas recorriendo sus dependencias.
El primer diagnóstico depende de ese recorrido y no necesariamente de la primera
línea con error. No se acumulan múltiples errores en una ejecución.

## Biblioteca integrada

| Función | Firma | Semántica |
| --- | --- | --- |
| `len` | Text → Int o [T] → Int | Puntos de código o elementos |
| `sum` | [Int] → Int | Suma; lista vacía produce 0 |
| `range` | Int → [Int] | 0 hasta n exclusivo; exige 0 ≤ n ≤ 100000 |
| `text` | T → Text | Misma representación que emit |

T en esta tabla es una notación de la especificación. El usuario no puede declarar
funciones genéricas. El límite de `range` es una protección puntual del MVP, no
una cuota general de memoria o tiempo.

## Ejecución y publicación

1. Lexer, parser y comprobación de todo el programa.
2. Validación de sustituciones externas.
3. Evaluación de todas las entradas y celdas, incluso las no utilizadas, en orden
   de dependencias; cada una se evalúa exactamente una vez.
4. Evaluación de cada `require` en orden textual. El primer falso es un error con
   su mensaje. Un error de cálculo en una condición también aborta.
5. Evaluación y conversión de todos los `emit` en orden textual.
6. Entrega de la lista completa a la API; la CLI añade un salto de línea por salida
   y realiza una escritura al flujo estándar. Un programa vacío no produce salida.

Las expresiones se evalúan de izquierda a derecha. `and`, `or` y `if` tienen
cortocircuito. El cortocircuito no omite la evaluación previa de celdas: una celda
con `1 // 0` falla aunque se mencione solo en una rama no tomada. Para proteger una
división, el `if` debe contener la operación peligrosa dentro de la misma expresión.
`require` comprueba resultados; no es un guardián previo a calcular celdas.

Text se publica sin comillas, Bool como `true`/`false`, Int en decimal, listas como
JSON (incluidas comillas de textos). No hay publicación parcial ante errores del
lenguaje, incluso si falla el último `emit`. Esta garantía no cubre fallos de E/S,
terminación externa del proceso ni caída del anfitrión durante la escritura.

La CLI devuelve 0 en éxito y 1 en errores del programa o de archivo. Errores de uso
de argumentos devuelven 2. Los diagnósticos van a stderr con archivo y, cuando hay
token asociado, línea y columna de base 1. `check` no calcula valores: puede aceptar
un programa que luego falle por división por cero o `require`. `graph` comprueba y
muestra un orden válido de evaluación con tipos; no dibuja aristas ni evalúa.

## Implementación y límites

Intérprete de AST en Python ≥ 3.11, sin dependencias de ejecución. El parser y el
comprobador usan recursión del anfitrión: programas muy profundos pueden rechazarse.
No hay sandbox, cuotas generales, reactividad incremental, paralelismo, archivos,
red, reloj, aleatoriedad o manejo de errores dentro del lenguaje. No ejecutar
programas hostiles sin aislamiento externo. El chequeo estático no garantiza que
las expresiones eviten división por cero o agotamiento de recursos.
