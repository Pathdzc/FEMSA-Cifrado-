# Proyecto Discos Duros Cifrados

Herramienta para evaluar el control de cifrado de discos en las PCs de FEMSA.

## Cómo correrlo
Con Docker

```
docker compose up --build
```

Abrir http://localhost:5000

Sin Docker: ver la sección de instalación en `docs/stack.md`, luego:

```
flask --app app run
```

## Datos

- Por defecto se usan los datos simulados (`datos/simulados/`).
- Los datos reales nunca se suben al repositorio ni quedan dentro de la imagen.
  Para usarlos con Docker, define dos variables antes de `docker compose up`:
  - `CARPETA_REALES`: la carpeta de la computadora donde está el archivo real.
  - `ARCHIVO_DATOS`: `datos/reales/<nombre del archivo>`.

## Documentación

| Archivo | Contenido |
|---|---|
| `docs/diccionario_datos.csv` | Qué significa cada columna |
| `docs/modelo_datos.md` | Modelo de la base de datos |
| `docs/dudas_y_supuestos.md` | Dudas para FEMSA y supuestos de trabajo |
| `docs/stack.md` | Herramientas, versiones y reglas del equipo |
| `datos/simulados/LEEME_datos_simulados.md` | Cómo se generan los datos simulados |
