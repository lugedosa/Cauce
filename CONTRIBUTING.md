# Contribuir a Cauce

Python ≥ 3.11. No hay dependencias de ejecución ni de pruebas. Ejecuta:

```console
python -m unittest discover -s tests -v
python -m cauce check examples/presupuesto.cau
```

Para cambiar semántica, describe el programa antes/después, actualiza SPEC.md y
añade una prueba que verifique el resultado o diagnóstico observable. Para fallos
de publicación incluye una prueba que confirme stdout vacío. No uses eval/exec
del anfitrión para evaluar Cauce. Conserva separadas sintaxis, comprobación y ejecución.

No añadir comparativas de rendimiento sin corpus reproducible y resultados iguales.
Las propuestas de concurrencia deben definir orden de errores y publicación antes
de introducir hilos. No subir credenciales, entornos virtuales ni archivos privados.
