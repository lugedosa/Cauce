# Hoja de ruta

Las versiones son objetivos, sin fechas prometidas. Cada cambio de semántica debe
actualizar SPEC.md, ejemplos y pruebas. La compatibilidad aún es experimental.

## 0.1 — base actual

- [x] Filosofía, gramática, tipos y garantías explícitas.
- [x] Lexer con posiciones, AST y parser sin evaluación de Python.
- [x] Comprobación estática y detección de ciclos de celdas y funciones.
- [x] Intérprete de celdas, entradas sustituibles y funciones puras.
- [x] Validación previa a publicación, CLI, ejemplos, tests y CI.

## 0.2 — experiencia y diagnósticos

- Mostrar fragmento fuente, subrayado y sugerencias en errores.
- Exportar grafo con aristas y explicar de qué depende cada resultado.
- Evaluación iterativa y cuotas configurables de pasos/tamaños.
- Formateador y pruebas generativas del parser/comprobador.
- Criterio de salida: corpus de errores documentados; casos profundos no dependen
  de la pila del anfitrión; límites verificables de ejecución.

## 0.3 — datos que merezcan usar el lenguaje

- Diseñar registros estructurales y tipos Result/Option.
- Transformaciones de listas con funciones puras, sin ocultar dependencias.
- Importar datos mediante capacidades explícitas en el anfitrión, con esquemas.
- Estudiar decimales exactos antes de usar Cauce en cálculos monetarios reales.
- Criterio de salida: tres casos completos de transformación de datos; sin coerciones
  silenciosas; errores de datos no provocan publicación parcial.

## 0.4 — evaluar la promesa del grafo

- Caché incremental con invalidación por entradas y semántica definida.
- Prototipo de ejecución paralela solo para celdas independientes.
- Definir selección determinista de errores ante fallos concurrentes.
- Criterio de salida: pruebas de equivalencia con ejecución secuencial y mediciones
  de sobrecoste frente a beneficio. Retirar paralelismo si no aporta.

## Antes de 1.0

- Revisión de semántica y comparación con lenguajes de flujo de datos existentes.
- Política de compatibilidad, empaquetado, revisión de nombre y seguridad.
- Corpus reproducible: resultados iguales antes de medir tiempos y memoria,
  versiones fijadas, hardware, calentamiento y múltiples repeticiones publicados.
- Evaluar tareas pequeñas y grandes frente a implementaciones equivalentes en
  Python y herramientas declarativas. No elegir solo casos favorables.
- Revisar si hace falta bytecode o compilación nativa basándose en perfiles.

No se publican afirmaciones de superioridad: el repositorio aún no contiene benchmarks.
