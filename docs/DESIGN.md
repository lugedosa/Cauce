# Cauce: decisiones de diseño

Estado: propuesta implementada como intérprete experimental 0.1.0. Nombre de trabajo;
no se ha comprobado su disponibilidad como marca o nombre de paquete.

## Propósito

Cauce explora una combinación concreta: fórmulas declarativas, funciones puras y
salida condicionada por invariantes. Su unidad de trabajo es un cálculo completo,
como un presupuesto o una transformación pequeña, no una secuencia de mutaciones.
Está diseñado creativamente por IA a petición de Luis. La combinación busca ser
útil y tener identidad propia; no constituye una afirmación de novedad académica
ni de superioridad sobre otros lenguajes.

Una celda describe una relación. `require` declara cuándo el resultado es aceptable.
`emit` solicita su publicación. Se comprueba todo el programa, se calculan todas
las celdas, se evalúan las condiciones y se preparan todas las salidas antes de
entregarlas al anfitrión. Un error del lenguaje no deja salida parcial. Una avería
del dispositivo de salida durante la escritura está fuera de esta garantía.

## Decisiones y costes

| Aspecto | Decisión 0.1 | Motivo y coste |
| --- | --- | --- |
| Paradigmas | Flujo de datos declarativo y funciones de expresión puras | Dependencias visibles; sin actualización de estado ni bucles imperativos |
| Tipado | Estático, estructural para listas, inferencia de celdas; firmas explícitas de funciones | Diagnósticos previos a ejecución; sin polimorfismo de usuario ni coerciones |
| Valores | Int, Bool, Text, listas homogéneas anidadas | Superficie pequeña; sin flotantes, null, registros ni tipos algebraicos todavía |
| Memoria | Valores inmutables y gestión por Python; una evaluación por celda y ejecución | Sin punteros o liberación manual; no promete baja latencia, cuotas o uso constante de memoria |
| Concurrencia | Secuencial en MVP; grafo apto para planificación paralela futura | Reproducibilidad primero; todavía no hay tareas, hilos ni aceleración paralela |
| Efectos | Solo `emit`, después de validaciones | No hay acceso al sistema desde programas; no es un sandbox contra agotamiento de recursos |
| Errores | Diagnósticos con línea y columna; fallo explícito | Sin excepciones capturables dentro del lenguaje |
| Recursión | Ciclos de celdas y de llamadas rechazados, incluso si no se ejecutan | Facilita inspección; limita algoritmos generales y no garantiza ausencia de fallos de recursos |

Las funciones no capturan celdas ni entradas: los datos se pasan como argumentos.
Así el grafo no oculta dependencias dentro de funciones. Una entrada tiene un valor
literal por defecto y puede sustituirse desde la CLI mediante JSON del mismo tipo.
El programa fuente sigue comprobándose aunque se sustituya una entrada.

## Garantías efectivas y fronteras

- Todo nombre, operador, argumento, rama y condición se comprueba estáticamente,
  incluidas expresiones que no se ejecutan. Bool e Int son tipos distintos.
- Orden textual independiente para celdas y funciones; orden textual de `emit`.
- Una celda se calcula una vez por ejecución. No hay actualización incremental
  entre ejecuciones ni reactividad a archivos o servicios externos.
- `and`, `or` e `if` evalúan solo los operandos o ramas necesarios, aunque sus
  dependencias sintácticas cuentan para detectar ciclos.
- `require false` o un fallo al calcular una salida devuelve un error sin salidas
  del programa. La API devuelve una lista completa; la CLI hace una escritura.
- Mismo programa y entradas producen los mismos valores dentro de la semántica
  del MVP. No se promete rendimiento o consumo de memoria determinista.
- La implementación depende de la pila, enteros y memoria del anfitrión. Convierte
  errores comunes de límites del anfitrión en diagnósticos, pero no ofrece cuotas,
  terminación formal, resistencia a entradas hostiles ni seguridad de procesos.

## Por qué este alcance

Un compilador nativo, un sistema de ownership y un runtime concurrente harían más
difícil validar la propuesta inicial. Un intérprete en Python sin dependencias de
ejecución permite discutir la semántica mediante programas reales. La separación
lexer → parser → comprobación/grafo → evaluación permite reemplazar el backend.

Antes de comparar con Python, hojas de cálculo u otros sistemas se necesitan
mediciones reproducibles de claridad, diagnósticos, tiempo y memoria. No existen
todavía. Tampoco se ha realizado una búsqueda exhaustiva de lenguajes previos.
