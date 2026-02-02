# Deploy en Render (Free) + Neon Postgres (Free) para 2026

Este documento describe un despliegue 100% gratis y sostenible para todo 2026.

## 0) Resumen rápido
- Render Free como Web Service (filesystem efímero; sin SMTP saliente).
- Neon Postgres Free como base de datos (no expira a 30 días).
- `build.sh` hace `collectstatic` y `migrate`.
- Datos seed y superuser se crean **desde local** contra Neon.

---

## 1) Plan para aguantar todo el año (obligatorio)

### Por qué NO Render Postgres
- Render Postgres Free expira a los 30 días. Para un uso todo 2026 no es válido.

### Por qué Neon
- Neon ofrece Postgres free con autosuspend/scale-to-zero. Cumple el objetivo de 0€ y no caduca a 30 días.

### Riesgos del free-tier y mitigaciones
1) **Cambios de políticas/cuotas**
   - Mitigación: revisa una vez al mes el panel de Neon y Render; mantén backups.
2) **Suspensión por inactividad**
   - Mitigación: acceso ocasional (login) despierta la DB; se espera latencia inicial.
3) **Cuotas de almacenamiento**
   - Mitigación: backups y limpieza de datos antiguos si aplica.
4) **Filesystem efímero en Render**
   - Mitigación: no usar SQLite en prod; no guardar media local.
5) **SMTP bloqueado en Render Free**
   - Mitigación: usar proveedor de email con API HTTP gratuita o un bot de Telegram.

### Backups (scripts incluidos)
- `scripts/db_backup.sh` hace `pg_dump` en formato custom.
- `scripts/db_restore.sh` restaura con `pg_restore`.
- Recomendación: ejecutar backup mensual (o semanal si hay mucho uso) desde tu equipo local.

---

## 2) Paso a paso: Neon (DB gratis)

1) Crea cuenta en Neon.
2) Crea un **Project** nuevo.
3) En la sección **Compute**, selecciona el tamaño más bajo disponible y habilita autosuspend.
4) En **Connection Details**, copia el connection string (Postgres URL).
5) Asegúrate de que tenga `sslmode=require`.

Resultado: tendrás un `DATABASE_URL` tipo:

```
postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

---

## 3) Paso a paso: Render (Free Web Service)

1) Conecta tu GitHub a Render.
2) Nuevo **Web Service** → selecciona el repo `f1-races`.
3) Build & Start:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn config.wsgi:application`
4) Plan: **Free**.
5) Environment Variables (Render dashboard → Environment):
   - `SECRET_KEY` = clave segura
   - `DEBUG` = `0`
   - `DATABASE_URL` = (la URL de Neon)
   - `ALLOWED_HOSTS` = `tu-servicio.onrender.com`
   - `CSRF_TRUSTED_ORIGINS` = `https://tu-servicio.onrender.com`

Nota: Render define `RENDER_EXTERNAL_HOSTNAME`; si no quieres usar `ALLOWED_HOSTS`, puedes omitirlo.

6) Deploy manual.

---

## 4) Validación post-deploy

1) Abre la URL pública de Render y comprueba que carga la home.
2) `/admin/` debe responder.
3) Static: CSS e imágenes de circuitos se cargan (si ves 404, revisa `collectstatic`).

---

## 5) Crear superuser y seed (desde local)

> En Render Free no hay shell; hazlo local contra Neon.

1) Exporta `DATABASE_URL` con el de Neon:

```
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require'
```

2) Ejecuta migraciones:

```
python manage.py migrate
```

3) Crea superuser:

```
python manage.py createsuperuser
```

4) Seed idempotente:

```
python manage.py seed_2026
```

---

## 6) Backups manuales

1) Backup:

```
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require'
./scripts/db_backup.sh
```

2) Restore:

```
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require'
./scripts/db_restore.sh ./backups/f1-races_YYYYMMDD_HHMMSS.dump
```

Requiere tener `pg_dump` y `pg_restore` instalados localmente.

---

## 7) Email en Render Free (planificado)

Render Free bloquea SMTP saliente. Alternativas gratuitas:
- Proveedor de email con API HTTP (free tier) desde la app.
- Bot de Telegram para avisos.

No implementado por ahora; queda listo para planificarlo cuando quieras.

---

## 8) Comandos de comprobación local (modo prod)

```
SECRET_KEY='local-check' \
DEBUG=0 \
ALLOWED_HOSTS='example.onrender.com' \
CSRF_TRUSTED_ORIGINS='https://example.onrender.com' \
DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require' \
python manage.py check --deploy
```

```
python manage.py collectstatic --noinput
```
