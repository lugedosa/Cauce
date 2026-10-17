# Verificación local de 0.1.0

Entorno: Windows, Python 3.12.10. Esta es evidencia de desarrollo, no una auditoría
formal ni una medición de rendimiento.

- 52 pruebas automatizadas aprobadas con `python -m unittest discover -s tests -v`.
- Pruebas del lexer y parser: posiciones, escapes, precedencia y errores sintácticos.
- Pruebas estáticas: tipos, firmas, captura prohibida, referencias adelantadas,
  ciclos, funciones sin uso y listas contextualizadas.
- Pruebas dinámicas: entradas, división entera, cortocircuito, biblioteca y salidas.
- Pruebas de CLI en procesos independientes: salida vacía ante validación fallida,
  error estático, fallo en el último emit y límite del anfitrión al formatear enteros.
- Los tres ejemplos válidos producen resultados esperados; los tres ejemplos de
  error fallan sin publicar nada.
- Paquete wheel construido con herramientas de empaquetado aisladas.
- Instalación y ejecución del paquete verificadas en un entorno virtual separado.

El workflow incluye Windows y Linux con Python 3.11, 3.12 y 3.13, pero esa matriz
remota aún no se ha ejecutado. Las pruebas no sustituyen revisión independiente,
fuzzing, pruebas de seguridad ni benchmarks, que quedan pendientes.
