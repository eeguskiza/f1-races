# F1 Porras

Aplicacion de predicciones para carreras de F1 - Temporada 2026.

## Setup

```bash
# Crear entorno virtual
python -m venv f1
source f1/bin/activate

# Instalar dependencias
pip install django
```

## Reset DB (desarrollo)

Para resetear la base de datos completamente:

```bash
./scripts/reset_db.sh
```

Esto borra `db.sqlite3`, genera nuevas migraciones, las aplica y ejecuta el seed.

## Migraciones manuales

```bash
python manage.py makemigrations
python manage.py migrate
```

## Seeding de datos 2026

### Opcion 1: Desde archivo de datos

```bash
python manage.py seed_2026
```

Lee de `data/f1calendar_2026.json` y crea:
- 10 equipos
- 20 pilotos
- 23 GPs con todas sus sesiones (FP1, FP2, FP3, Quali, Race, Sprint cuando aplique)

### Opcion 2: Desde fixtures

```bash
python manage.py seed_2026 --from-fixtures
```

## Sistema de Deadline

Las predicciones se cierran **48 horas antes del inicio de FP1**.

```
deadline_utc = FP1_start_utc - 48 horas
```

- Si intentas crear/editar una prediccion despues del deadline, se rechaza con ValidationError.
- Cada GP tiene su propio deadline calculado dinamicamente.
- Si un evento no tiene sesion FP1, se considera bloqueado (no se pueden hacer picks).

## Horarios

Los horarios de sesiones provienen de [f1calendar.com](https://f1calendar.com) y estan en **UTC**.

El archivo fuente es `data/f1calendar_2026.json`.

## Tests

```bash
python manage.py test predictions.tests.test_seed
```

Tests incluidos:
- Idempotencia del seed (ejecutar 2 veces no duplica)
- Cada evento tiene sesion FP1
- Deadline es 48h antes de FP1
- Bloqueo de predicciones despues del deadline
- Validacion de pilotos duplicados en Top5

## Servidor de desarrollo

```bash
python manage.py runserver
```

Acceder a http://127.0.0.1:8000/

## Estructura de modelos

- **Team**: Escuderias (Red Bull, Ferrari, etc.)
- **Driver**: Pilotos con codigo unico (VER, HAM, ALO...)
- **GrandPrix**: Evento de fin de semana (Australia GP, Monaco GP...)
- **Session**: Sesiones dentro del evento (FP1, FP2, FP3, QUALI, RACE, SPRINT, SPRINT_QUALI)
- **Prediction**: Prediccion de usuario para un evento
- **NewsPost**: Noticias/feed
