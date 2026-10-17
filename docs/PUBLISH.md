# Publicar en GitHub

El proyecto está preparado para revisión local. No se ha creado repositorio remoto
ni se ha enviado código. Esta sesión no expone un conector GitHub y no tiene la
herramienta `gh` disponible. No se han buscado tokens ni usado credenciales del equipo.

Decisiones necesarias antes de publicar: cuenta u organización de destino,
nombre disponible y visibilidad pública o privada. Hace falta autorización explícita
del usuario para crear el remoto y enviar el código. Conectar GitHub por sí solo
no implica autorizar la publicación.

Una vez autorizado y disponible el acceso, crear un repositorio vacío en GitHub
(sin generar README o licencia), conectar su URL y enviar la rama main:

```console
git remote add origin URL_DEL_REPOSITORIO_AUTORIZADO
git push -u origin main
```

Alternativa con GitHub CLI, si se instala y autentica: desde la raíz del proyecto,
`gh repo create CUENTA/NOMBRE --private --source=. --remote=origin --push`.
Cambiar a `--public` únicamente si esa visibilidad fue autorizada. Los nombres de
estas instrucciones son marcadores, no una cuenta o remoto configurados.

No publicar aún en PyPI: el nombre de distribución `cauce-lang` es provisional
y su disponibilidad no se ha verificado. El workflow está preparado, pero sus
trabajos remotos solo podrán verificarse después de subir a GitHub.
