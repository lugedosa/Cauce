# Publicar en GitHub

El destino autorizado por el usuario es el repositorio público
[lugedosa/Cauce](https://github.com/lugedosa/Cauce). La rama principal es `main`.
El acceso se realiza mediante Git y su gestor de credenciales configurado, sin
incorporar credenciales al código ni al remoto. No hace falta instalar `gh`.

La creación y publicación inicial fueron autorizadas en la conversación de origen.
Esta autorización se refiere a este repositorio y no autoriza crear otros destinos
o publicar credenciales. Para futuras publicaciones, revisar los cambios y ejecutar
las pruebas antes de subirlos.

Desde un clon con permiso de escritura, subir la rama principal:

```console
git push -u origin main
```

Para obtener una copia nueva:

```console
git clone https://github.com/lugedosa/Cauce.git
cd Cauce
python -m unittest discover -s tests -v
```

No publicar aún en PyPI: el nombre de distribución `cauce-lang` es provisional
y su disponibilidad no se ha verificado. Consultar la pestaña Actions de GitHub
para comprobar los trabajos remotos; la verificación local está en VALIDATION.md.
