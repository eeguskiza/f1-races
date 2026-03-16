# F1 Porras

Aplicacion web para hacer predicciones de carreras de Formula 1. Los usuarios pueden registrarse, predecir el Top 5 de cada Gran Premio y la posicion de Fernando Alonso, y competir en un ranking global. Las predicciones se cierran el viernes a las 23:59:59 UTC de cada finde de GP (o antes, si la QUALI empieza antes).

## Comandos de resultados

```bash
# 1) Procesar todos los GPs pendientes y guardar en BBDD
python manage.py fetch_results

# 2) Procesar una ronda concreta (ejemplo: ronda 2) y guardar en BBDD
python manage.py fetch_results --round 2

# 3) Reprocesar una ronda aunque ya tenga resultados guardados
python manage.py fetch_results --round 2 --force
```
