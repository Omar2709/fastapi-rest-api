# FastAPI REST API

API REST desarrollada con **FastAPI**, **PostgreSQL** y **SQLAlchemy** como proyecto práctico de ingeniería backend.

El proyecto parte de una API CRUD sencilla para estudiar los fundamentos de FastAPI, Pydantic, SQLAlchemy, PostgreSQL, migraciones y testing, y evolucionará progresivamente hacia una API orientada a procesamiento asíncrono e integraciones.

El objetivo no es únicamente construir una API funcional, sino comprender problemas reales de backend como transacciones, idempotencia, procesamiento de trabajos, colas, reintentos, webhooks, seguridad y observabilidad.

> El proyecto se encuentra en desarrollo activo y evoluciona por bloques funcionales pequeños, comprobables y versionados con Git.

---

## Dirección del proyecto

La implementación actual de usuarios y tareas funciona como base para aprender y validar los fundamentos de FastAPI, Pydantic, SQLAlchemy, PostgreSQL y testing.

A partir de esta base, el proyecto evolucionará hacia una API orientada a procesamiento asíncrono e integraciones, incorporando conceptos como:

- API Keys y scopes.
- Procesamiento de Jobs.
- Idempotencia.
- Máquinas de estados.
- Transactional Outbox.
- AWS SQS.
- Workers y reintentos.
- Dead Letter Queues.
- Webhooks firmados.
- Rate limiting.
- Observabilidad y correlation IDs.

El objetivo es estudiar problemas propios de APIs distribuidas y procesamiento asíncrono, evitando convertir el proyecto en una aplicación tradicional de gestión de tareas.

---

## Contenido

- [Dirección del proyecto](#dirección-del-proyecto)
- [Objetivos de aprendizaje](#objetivos-de-aprendizaje)
- [Tecnologías](#tecnologías)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo de datos](#modelo-de-datos)
- [Endpoints](#endpoints)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Base de datos](#base-de-datos)
- [Migraciones con Alembic](#migraciones-con-alembic)
- [Ejecutar la API](#ejecutar-la-api)
- [Testing](#testing)
- [Calidad de código](#calidad-de-código)
- [Flujo de desarrollo](#flujo-de-desarrollo)
- [Estado actual](#estado-actual)

---

## Objetivos de aprendizaje

Este proyecto busca aprender de forma práctica:

- Cómo funciona una API REST.
- Métodos HTTP: `GET`, `POST`, `PATCH` y `DELETE`.
- Códigos de estado HTTP como `200`, `201`, `204`, `404`, `409` y `422`.
- Path parameters, query parameters y request bodies.
- Validación y serialización de datos con Pydantic.
- Separación entre modelos de entrada, salida y persistencia.
- Persistencia de datos con PostgreSQL.
- SQL y conceptos relacionales.
- ORM con SQLAlchemy 2.x.
- Gestión de sesiones y transacciones.
- Migraciones de base de datos con Alembic.
- Relaciones `1:N` y claves foráneas.
- Manejo de errores de integridad.
- Arquitectura por capas.
- Testing de endpoints con `pytest` y `TestClient`.
- Aislamiento de pruebas mediante una base de datos separada.
- Gestión de dependencias y entornos con `uv`.
- Uso de `pyproject.toml` y `uv.lock`.
- Linting y formateo automático con Ruff.
- Control de versiones con Git y GitHub.
- Preparación del flujo local para futura integración continua con GitHub Actions.

---

## Tecnologías

| Tecnología | Uso |
| --- | --- |
| Python | Lenguaje principal |
| FastAPI | Framework para construir la API |
| Pydantic | Validación y serialización de datos |
| Pydantic Settings | Configuración mediante variables de entorno |
| SQLAlchemy 2.x | ORM y acceso a la base de datos |
| Psycopg 3 | Driver de PostgreSQL para Python |
| PostgreSQL | Base de datos relacional |
| Alembic | Migraciones y versionado del esquema |
| Uvicorn | Servidor ASGI |
| pytest | Suite de tests automatizados |
| FastAPI TestClient | Pruebas HTTP de la aplicación |
| Ruff | Linting, orden de imports y formateo |
| uv | Gestión de dependencias, entorno virtual y lockfile |
| Git | Control de versiones |
| GitHub | Repositorio remoto |

---

## Arquitectura

El proyecto mantiene una separación sencilla por responsabilidades:

```text
Cliente
   |
   | HTTP
   v
FastAPI / Routers
   |
   v
Pydantic
   |
   v
Services
   |
   v
SQLAlchemy ORM
   |
   v
Psycopg
   |
   v
PostgreSQL
```

### Responsabilidad de cada capa

```text
routers/
    Manejo HTTP:
    rutas, parámetros, códigos de estado y HTTPException.

services/
    Lógica de aplicación y operaciones con SQLAlchemy.

schemas.py
    Modelos Pydantic para datos de entrada y salida.

models.py
    Modelos ORM que representan las tablas de PostgreSQL.

database.py
    Engine, Session y conexión con la base de datos.

config.py
    Configuración cargada desde variables de entorno.

migrations/
    Historial de cambios del esquema administrado por Alembic.

tests/
    Pruebas automatizadas y fixtures de testing.
```

---

## Estructura del proyecto

La estructura actual es similar a:

```text
fastapi-rest-api/
|
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── tasks.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── users.py
│       └── tasks.py
│
├── migrations/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── sql/
│   └── 01_users.sql
│
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_tasks.py
│   └── test_users.py
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

> `.env` contiene configuración local sensible y no debe subirse al repositorio.

### Gestión de dependencias

Las dependencias directas del proyecto se declaran en `pyproject.toml`.

Las versiones exactas resueltas, incluidas las dependencias transitivas, quedan registradas en `uv.lock`.

`uv.lock` forma parte del código fuente y debe versionarse con Git para mantener instalaciones reproducibles.

Las herramientas utilizadas exclusivamente durante desarrollo, como `pytest` y Ruff, pertenecen al grupo de dependencias de desarrollo.

---

## Modelo de datos

Actualmente existen dos recursos relacionados:

```text
User
 |
 | 1
 |
 | N
 v
Task
```

Un usuario puede tener muchas tareas y cada tarea pertenece a un único usuario.

### `users`

Campos principales:

```text
id
name
email
created_at
is_active
```

Características principales:

- `id` es la clave primaria.
- PostgreSQL genera automáticamente el `id`.
- `email` es obligatorio y único.
- `name` tiene restricciones de longitud.
- `is_active` permite desactivar usuarios sin eliminarlos físicamente.
- `created_at` se genera automáticamente.

### `tasks`

Campos principales:

```text
id
title
description
is_completed
created_at
user_id
```

Características principales:

- `id` es la clave primaria.
- `user_id` es una clave foránea hacia `users.id`.
- `user_id` tiene un índice para acelerar consultas por usuario.
- Una tarea no puede existir sin usuario.
- `is_completed` comienza en `false`.
- `description` puede ser `NULL`.
- La relación utiliza `ON DELETE RESTRICT`.

Esto significa que PostgreSQL impide eliminar un usuario mientras tenga tareas asociadas.

---

## Endpoints

### General

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/` | Mensaje principal |
| `GET` | `/health` | Comprobación básica del estado de la API |

### Users

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/users` | Obtener usuarios |
| `GET` | `/users/{user_id}` | Obtener un usuario |
| `POST` | `/users` | Crear un usuario |
| `PATCH` | `/users/{user_id}` | Actualizar parcialmente un usuario |
| `DELETE` | `/users/{user_id}` | Eliminar un usuario |

El listado admite un límite validado entre `1` y `100`:

```http
GET /users?limit=10
```

### Tasks

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/users/{user_id}/tasks` | Crear una tarea para un usuario |
| `GET` | `/users/{user_id}/tasks` | Obtener las tareas de un usuario |
| `GET` | `/tasks/{task_id}` | Obtener una tarea por ID |
| `PATCH` | `/tasks/{task_id}` | Actualizar parcialmente una tarea |
| `DELETE` | `/tasks/{task_id}` | Eliminar una tarea |

El CRUD básico de `Task` está completo.

Las actualizaciones mediante `PATCH` modifican únicamente los campos enviados por el cliente. Campos controlados por la aplicación como `id`, `created_at` y `user_id` no forman parte del esquema de actualización.

---

## Códigos HTTP relevantes

```text
200 OK
    Operación realizada correctamente.

201 Created
    Se creó un nuevo recurso.

204 No Content
    El recurso fue eliminado correctamente.

404 Not Found
    El recurso solicitado no existe.

409 Conflict
    La operación entra en conflicto con el estado actual de los datos.

422 Unprocessable Entity
    Los datos enviados no cumplen las validaciones esperadas.
```

Por ejemplo, intentar eliminar un usuario que todavía tiene tareas asociadas devuelve `409 Conflict`.

PostgreSQL bloquea primero la eliminación mediante la clave foránea y la aplicación convierte el error de integridad en una respuesta HTTP comprensible.

---

## Requisitos

Antes de ejecutar el proyecto necesitas:

- Python 3.11 o superior.
- PostgreSQL instalado y ejecutándose.
- Git.
- `uv`.

La versión mínima declarada por el proyecto es Python 3.11.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Omar2709/fastapi-rest-api.git
cd fastapi-rest-api
```

### 2. Verificar `uv`

```bash
uv --version
```

En Windows puede instalarse mediante WinGet:

```powershell
winget install --id=astral-sh.uv -e
```

### 3. Instalar y sincronizar dependencias

Desde la raíz del proyecto:

```bash
uv sync
```

`uv` utiliza `pyproject.toml` y `uv.lock` para crear y sincronizar automáticamente el entorno virtual `.venv`.

No es necesario crear manualmente el entorno con `python -m venv` ni mantener un `requirements.txt` como fuente principal de dependencias.

### 4. Ejecutar comandos dentro del entorno

No es necesario activar manualmente `.venv` si se utiliza `uv run`:

```bash
uv run python --version
```

---

## Gestión de dependencias con uv

### Agregar una dependencia de runtime

```bash
uv add nombre-paquete
```

Ejemplo:

```bash
uv add redis
```

### Agregar una dependencia de desarrollo

```bash
uv add --dev nombre-paquete
```

Ejemplo:

```bash
uv add --dev ruff
```

### Eliminar una dependencia

```bash
uv remove nombre-paquete
```

### Sincronizar el entorno

```bash
uv sync
```

### Ver el árbol de dependencias

```bash
uv tree
```

### Ejecutar comandos del proyecto

```bash
uv run <comando>
```

Ejemplo:

```bash
uv run uvicorn app.main:app --reload
```

Las dependencias directas deben declararse mediante `pyproject.toml`. No se deben agregar manualmente como dependencias directas paquetes transitivos requeridos únicamente por otras librerías.

---

## Configuración

Crea tu archivo `.env` tomando `.env.example` como referencia.

Ejemplo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fastapi_learning
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Nunca subas contraseñas reales, tokens o secretos al repositorio.

El archivo `.env` debe permanecer ignorado por Git.

---

## Base de datos

La base de datos utilizada durante el desarrollo es, por defecto:

```text
fastapi_learning
```

Puedes crearla con PostgreSQL:

```bash
createdb fastapi_learning
```

Dependiendo de la configuración local puede ser necesario indicar un usuario:

```bash
createdb -U postgres fastapi_learning
```

También puede crearse desde `psql`:

```sql
CREATE DATABASE fastapi_learning;
```

---

## Migraciones con Alembic

El esquema de la base de datos se administra mediante Alembic y todos los comandos se ejecutan dentro del entorno gestionado por `uv`.

### Ver la versión actual

```bash
uv run alembic current
```

### Ver las cabezas de migración

```bash
uv run alembic heads
```

### Ver el historial

```bash
uv run alembic history
```

### Aplicar migraciones pendientes

```bash
uv run alembic upgrade head
```

### Crear una migración automáticamente

Después de modificar los modelos SQLAlchemy:

```bash
uv run alembic revision --autogenerate -m "descripcion del cambio"
```

El archivo generado debe revisarse manualmente antes de aplicar la migración:

```bash
uv run alembic upgrade head
```

### Regla del proyecto

```text
Cambio en endpoints        -> no requiere migración
Cambio en services         -> no requiere migración
Cambio en validaciones     -> normalmente no requiere migración

Nueva tabla                -> requiere migración
Nueva columna              -> requiere migración
Nueva foreign key          -> requiere migración
Cambio del esquema SQL     -> requiere migración
```

---

## Ejecutar la API

Desde la raíz del proyecto:

```bash
uv run uvicorn app.main:app --reload
```

Resultado esperado:

```text
Uvicorn running on http://127.0.0.1:8000
```

### Documentación interactiva

Con la API ejecutándose:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Swagger permite probar directamente los endpoints desde el navegador.

---

## Ejemplos

### Crear un usuario

```http
POST /users
Content-Type: application/json

{
  "name": "Ana",
  "email": "ana@example.com"
}
```

Respuesta aproximada:

```json
{
  "id": 1,
  "name": "Ana",
  "email": "ana@example.com",
  "created_at": "2026-01-01T12:00:00Z",
  "is_active": true
}
```

### Actualizar parcialmente un usuario

```http
PATCH /users/1
Content-Type: application/json

{
  "is_active": false
}
```

Solo los campos enviados son modificados.

### Crear una tarea

```http
POST /users/1/tasks
Content-Type: application/json

{
  "title": "Aprender relaciones",
  "description": "Estudiar ForeignKey y relationship"
}
```

### Actualizar parcialmente una tarea

```http
PATCH /tasks/1
Content-Type: application/json

{
  "is_completed": true
}
```

También es posible enviar explícitamente `null` en campos opcionales:

```json
{
  "description": null
}
```

Esto permite eliminar la descripción sin modificar el resto de campos.

### Eliminar una tarea

```http
DELETE /tasks/1
```

Si la tarea existe, la API responde con `204 No Content`. Si no existe, devuelve `404 Not Found`.

---

## Validación de datos

Pydantic se utiliza para validar los datos que entran y salen de la API.

Actualmente existen esquemas como:

```text
UserCreate
UserUpdate
UserResponse

TaskCreate
TaskUpdate
TaskResponse
```

Esta separación permite controlar qué campos puede enviar un cliente y qué campos puede devolver la aplicación.

Para actualizaciones parciales se utilizan únicamente los campos enviados realmente por el cliente mediante `model_dump(exclude_unset=True)`.

Conceptualmente:

```text
JSON
 |
 v
TaskUpdate
 |
 v
Service
 |
 v
SQLAlchemy Model
 |
 v
PostgreSQL
```

---

## Testing

El proyecto utiliza **pytest** y **FastAPI TestClient** para validar el comportamiento de la API.

La suite contiene pruebas para los endpoints generales, usuarios y tareas:

```text
tests/
├── conftest.py
├── test_main.py
├── test_users.py
└── test_tasks.py
```

### Base de datos de testing

Las pruebas no utilizan la base de datos normal de desarrollo. A partir de `DB_NAME`, la configuración de tests utiliza una base separada con sufijo `_test`.

Por ejemplo, si el `.env` contiene:

```env
DB_NAME=fastapi_learning
```

la suite utiliza:

```text
fastapi_learning_test
```

La base debe existir en PostgreSQL antes de ejecutar la suite. Puede crearse con:

```bash
createdb fastapi_learning_test
```

Las fixtures crean las tablas necesarias para la sesión de tests, limpian los datos entre pruebas y sobrescriben temporalmente la dependencia `get_db` de FastAPI para utilizar la sesión de testing.

### Ejecutar todos los tests

```bash
uv run pytest
```

### Ejecutar un archivo concreto

```bash
uv run pytest tests/test_users.py
```

### Ejecutar un test concreto

```bash
uv run pytest tests/test_users.py::nombre_del_test
```

---

## Calidad de código

El proyecto utiliza **Ruff** como herramienta de linting y formateo.

Ruff está configurado en `pyproject.toml` tomando **Python 3.11** como versión mínima objetivo, en línea con `requires-python = ">=3.11"`.

La configuración activa reglas orientadas a:

- errores importantes de `pycodestyle` (`E4`, `E7`, `E9`);
- errores detectados por Pyflakes (`F`);
- orden de imports (`I`);
- modernización compatible con Python 3.11+ (`UP`);
- patrones propensos a bugs (`B`);
- simplificación de código (`SIM`).

El formatter utiliza una longitud de línea de referencia de 88 caracteres, comillas dobles e indentación con espacios.

### Comprobar problemas de código

```bash
uv run ruff check .
```

### Aplicar correcciones automáticas

```bash
uv run ruff check . --fix
```

### Comprobar el formato sin modificar archivos

```bash
uv run ruff format --check .
```

### Aplicar formato

```bash
uv run ruff format .
```

### Control de calidad local

Antes de realizar un commit importante se debe comprobar:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

El resultado esperado es conceptualmente:

```text
Ruff lint       ✅
Ruff format     ✅
Tests           ✅
```

Este conjunto de comandos define el **contrato de calidad local** del proyecto.

Más adelante GitHub Actions ejecutará las mismas comprobaciones en integración continua para reducir diferencias entre el entorno local y CI.

---

## Seguridad y buenas prácticas actuales

El proyecto aplica actualmente las siguientes prácticas:

- Variables sensibles fuera del código mediante `.env`.
- `.env` ignorado por Git.
- Validación de request bodies con Pydantic.
- Restricciones también a nivel PostgreSQL.
- Emails únicos mediante una constraint `UNIQUE`.
- Foreign keys para garantizar integridad referencial.
- `rollback()` después de errores de transacción.
- Modelos de entrada y salida separados.
- Campos modificables controlados mediante schemas específicos.
- Manejo de errores HTTP como `404`, `409` y `422`.
- Migraciones de base de datos versionadas.
- Separación entre routers y services.
- Dependencias directas declaradas explícitamente.
- Versiones reproducibles mediante `uv.lock`.
- Tests de API mediante `pytest` y `TestClient`.
- Base de datos separada para testing.
- Linting y formateo automatizados con Ruff.
- Control de calidad local antes de commits importantes.

Todavía faltan mecanismos importantes como autenticación mediante API Keys, autorización por scopes, rate limiting, observabilidad y automatización mediante CI.

---

## Flujo de desarrollo

El desarrollo se organiza en bloques funcionales. Después de completar y comprobar cada bloque se realiza un commit independiente.

```text
Implementar
    |
    v
Probar
    |
    v
Ruff lint
    |
    v
Ruff format check
    |
    v
pytest
    |
    v
Revisar cambios
    |
    v
Commit
```

Antes de realizar un commit importante:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
git status
git diff
```

Después:

```bash
git add <archivos>
git commit -m "Descripción clara del cambio"
git push
```

Los mensajes de commit buscan ser breves y descriptivos.

Las migraciones de Alembic, `pyproject.toml` y `uv.lock` forman parte del código fuente y deben versionarse cuando correspondan.

Nunca debe incluirse `.env`.

---

## Estado actual

### Implementado

- [x] Proyecto Python.
- [x] FastAPI.
- [x] Uvicorn.
- [x] Documentación OpenAPI / Swagger.
- [x] Validación con Pydantic.
- [x] PostgreSQL.
- [x] SQLAlchemy ORM.
- [x] Psycopg 3.
- [x] Configuración mediante `.env`.
- [x] CRUD de usuarios.
- [x] CRUD de tareas.
- [x] Actualizaciones parciales con `PATCH`.
- [x] Manejo de errores `404`, `409` y `422`.
- [x] Alembic y migraciones.
- [x] Arquitectura con routers y services.
- [x] Relación `User 1:N Task`.
- [x] Foreign keys e integridad referencial.
- [x] Gestión de dependencias con `uv`.
- [x] `pyproject.toml`.
- [x] Lockfile reproducible con `uv.lock`.
- [x] Entorno virtual gestionado mediante `uv`.
- [x] Tests automatizados con `pytest`.
- [x] Pruebas HTTP mediante `TestClient`.
- [x] Base de datos separada para testing.
- [x] Fixtures para aislamiento de tests.
- [x] Ruff para linting y formateo.
- [x] Control de calidad local antes de commits.

### Próximos pasos

- [ ] Versionar la API bajo `/api/v1`.
- [ ] Estandarizar las respuestas de error.
- [ ] Añadir medición de cobertura de tests.
- [ ] Integrar Ruff y pytest en GitHub Actions.
- [ ] Implementar autenticación mediante API Keys.
- [ ] Añadir scopes y revocación de API Keys.
- [ ] Introducir el dominio de procesamiento de Jobs.
- [ ] Implementar estados y transiciones de Jobs.
- [ ] Implementar idempotencia en creación de Jobs.
- [ ] Introducir Transactional Outbox.
- [ ] Integrar AWS SQS.
- [ ] Implementar workers y estrategia de reintentos.
- [ ] Añadir Dead Letter Queue.
- [ ] Implementar webhooks firmados con HMAC.
- [ ] Añadir retry y backoff para webhooks.
- [ ] Implementar rate limiting.
- [ ] Añadir logging estructurado y correlation IDs.
- [ ] Añadir métricas y observabilidad.
- [ ] Dockerizar los componentes del sistema.
- [ ] Preparar despliegue y CI/CD en AWS.

---

## Filosofía del proyecto

Este proyecto intenta evitar utilizar las herramientas como cajas negras. La intención es comprender qué sucede en cada capa y qué problema resuelve cada abstracción.

Por ejemplo:

```python
db.get(User, 1)
```

representa conceptualmente una operación similar a:

```sql
SELECT *
FROM users
WHERE id = 1;
```

Y:

```python
db.delete(user)
db.commit()
```

termina produciendo conceptualmente:

```sql
DELETE FROM users
WHERE id = 1;
```

De forma similar:

```python
task_data.model_dump(exclude_unset=True)
```

permite distinguir los campos enviados realmente durante una actualización parcial.

SQLAlchemy, Pydantic, FastAPI, pytest, Ruff y `uv` simplifican distintas partes del desarrollo, pero el objetivo es comprender qué sucede detrás de cada operación.

---

## Licencia

Por definir.

---

## Nota

Este repositorio forma parte de un proyecto de aprendizaje y evoluciona progresivamente. Algunas decisiones arquitectónicas pueden cambiar a medida que se incorporen nuevos conceptos y necesidades.
