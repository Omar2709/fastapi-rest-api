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
- [Versionado de la API](#versionado-de-la-api)
- [Códigos HTTP relevantes](#códigos-http-relevantes)
- [Contrato de errores](#contrato-de-errores)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Gestión de dependencias con uv](#gestión-de-dependencias-con-uv)
- [Configuración](#configuración)
- [Provisionamiento de API Keys](#provisionamiento-de-api-keys)
- [Autenticación mediante API Key](#autenticación-mediante-api-key)
- [Gestión de API Keys](#gestión-de-api-keys)
- [Base de datos](#base-de-datos)
- [Migraciones con Alembic](#migraciones-con-alembic)
- [Ejecutar la API](#ejecutar-la-api)
- [Ejemplos](#ejemplos)
- [Validación de datos](#validación-de-datos)
- [Testing](#testing)
- [Cobertura de tests](#cobertura-de-tests)
- [Calidad de código](#calidad-de-código)
- [Seguridad y buenas prácticas actuales](#seguridad-y-buenas-prácticas-actuales)
- [Flujo de desarrollo](#flujo-de-desarrollo)
- [Estado actual](#estado-actual)
- [Filosofía del proyecto](#filosofía-del-proyecto)
- [Licencia](#licencia)
- [Nota](#nota)

---

## Objetivos de aprendizaje

Este proyecto busca aprender de forma práctica:

- Cómo funciona una API REST.
- Métodos HTTP: `GET`, `POST`, `PATCH` y `DELETE`.
- Códigos de estado HTTP como `200`, `201`, `204`, `404`, `405`, `409` y `422`.
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
- Medición de cobertura de líneas y ramas con `pytest-cov`.
- Quality gates mínimos para proteger la cobertura del proyecto.
- Aislamiento de pruebas mediante una base de datos separada.
- Gestión de dependencias y entornos con `uv`.
- Uso de `pyproject.toml` y `uv.lock`.
- Linting y formateo automático con Ruff.
- Control de versiones con Git y GitHub.
- Uso de Conventional Commits para mantener un historial consistente.
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
| pytest-cov | Cobertura de líneas y ramas sobre el código de aplicación |
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
    rutas, parámetros, códigos de estado y traducción de errores a APIError.
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
api/errors.py
    Contrato transversal de errores, códigos estables y handlers globales.
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
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   │
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── tasks.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── users.py
│       └── tasks.py
│
├── migrations/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── sql/
│   └── 01_users.sql
│
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_tasks.py
│   └── test_users.py
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

Actualmente existen tres recursos relacionados:

```text
         User
         /    \\
       1/      \1
       /        \\
     N/          \N
     v            v
   Task         ApiKey
```

Un usuario puede tener muchas tareas y muchas API Keys; cada tarea y cada API Key pertenecen a un único usuario.

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

### `api_keys`

Campos principales:

```text
id
user_id
name
key_id
key_digest
created_at
expires_at
revoked_at
last_used_at
```

Características principales:

- Cada API Key pertenece a un único usuario.
- `key_id` es público, único y permite localizar eficientemente la credencial.
- La API Key completa nunca se almacena en PostgreSQL.
- `key_digest` almacena el digest criptográfico utilizado para verificación.
- `revoked_at` permite revocar una credencial conservando información de auditoría.
- `expires_at` permite configurar expiración opcional.
- `last_used_at` registra el uso reciente de la credencial mediante actualizaciones limitadas para evitar una escritura en PostgreSQL por cada request.
- La relación utiliza `ON DELETE CASCADE`, por lo que las credenciales desaparecen si se elimina su propietario.

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
| `GET` | `/api/v1/users` | Obtener usuarios |
| `GET` | `/api/v1/users/{user_id}` | Obtener un usuario |
| `POST` | `/api/v1/users` | Crear un usuario |
| `PATCH` | `/api/v1/users/{user_id}` | Actualizar parcialmente un usuario |
| `DELETE` | `/api/v1/users/{user_id}` | Eliminar un usuario |

El listado admite un límite validado entre `1` y `100`:

```http
GET /api/v1/users?limit=10
```

### Tasks

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/users/{user_id}/tasks` | Crear una tarea para un usuario |
| `GET` | `/api/v1/users/{user_id}/tasks` | Obtener las tareas de un usuario |
| `GET` | `/api/v1/tasks/{task_id}` | Obtener una tarea por ID |
| `PATCH` | `/api/v1/tasks/{task_id}` | Actualizar parcialmente una tarea |
| `DELETE` | `/api/v1/tasks/{task_id}` | Eliminar una tarea |

El CRUD básico de `Task` está completo.

Las actualizaciones mediante `PATCH` modifican únicamente los campos enviados por el cliente. Campos controlados por la aplicación como `id`, `created_at` y `user_id` no forman parte del esquema de actualización.

### API Keys

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/api-keys` | Crear una API Key para el usuario autenticado |
| `GET` | `/api/v1/api-keys` | Listar las API Keys del usuario autenticado |
| `POST` | `/api/v1/api-keys/{key_id}/revoke` | Revocar una API Key del usuario autenticado |

---

## Versionado de la API

Los endpoints de negocio se publican bajo un prefijo de versión:

```text
/api/v1
```

Por ejemplo:

```text
GET  /api/v1/users
POST /api/v1/users
GET  /api/v1/tasks/{task_id}
```

El versionado permite evolucionar el contrato HTTP de la API sin introducir cambios incompatibles directamente sobre los endpoints existentes.

Los endpoints operacionales:

```text
/
/health
```

permanecen fuera del prefijo de versión.

La versión definida en `FastAPI(version="0.1.0")` representa la versión del software y no debe confundirse con la versión pública del contrato HTTP `/api/v1`.

---

## Códigos HTTP relevantes

```text
200 OK
    Operación realizada correctamente.
201 Created
    Se creó un nuevo recurso.
204 No Content
    El recurso fue eliminado correctamente.
401 Unauthorized
    La solicitud no incluye una credencial válida para acceder al recurso protegido.
404 Not Found
    El recurso solicitado no existe.
405 Method Not Allowed
    El método HTTP no está permitido para la ruta solicitada.
409 Conflict
    La operación entra en conflicto con el estado actual de los datos.
422 Unprocessable Entity
    Los datos enviados no cumplen las validaciones esperadas.
```

Por ejemplo, intentar eliminar un usuario que todavía tiene tareas asociadas devuelve `409 Conflict`.

PostgreSQL bloquea primero la eliminación mediante la clave foránea y la aplicación convierte el error de integridad en una respuesta HTTP comprensible.

---

## Contrato de errores

Los errores de la API utilizan una estructura uniforme:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "Usuario no encontrado",
    "details": null
  }
}
```

### Campos

- `code`: código estable y procesable por clientes.
- `message`: descripción legible del error.
- `details`: información adicional cuando aplica.

El código HTTP continúa indicando la categoría general del problema (`401`, `404`, `405`, `409`, `422`, etc.), mientras que `error.code` identifica el caso concreto de forma estable. Los clientes pueden tomar decisiones usando el código sin depender del texto de `message`.

Actualmente se utilizan códigos como:

```text
USER_NOT_FOUND
TASK_NOT_FOUND
DUPLICATE_EMAIL
USER_HAS_TASKS
VALIDATION_ERROR
NOT_FOUND
METHOD_NOT_ALLOWED
HTTP_ERROR
API_KEY_MISSING
API_KEY_INVALID
API_KEY_REVOKED
API_KEY_EXPIRED
API_KEY_OWNER_INACTIVE
```

Los errores de validación utilizan el código `VALIDATION_ERROR` y pueden incluir detalles de los campos inválidos:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son válidos",
    "details": [
      {
        "field": "body.email",
        "message": "valor inválido",
        "type": "value_error"
      }
    ]
  }
}
```

Los valores originales recibidos no se reflejan en los detalles de validación para evitar exponer potencialmente información sensible. Solo se publican `field`, `message` y `type`.

Los errores generados por el propio framework también utilizan este contrato. Por ejemplo, una ruta inexistente devuelve `NOT_FOUND` y un método HTTP no permitido devuelve `METHOD_NOT_ALLOWED`.

En OpenAPI, las respuestas `422` de los endpoints bajo `/api/v1` se documentan mediante el modelo `ErrorResponse`.

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
uv run \<comando>
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

## Provisionamiento de API Keys

Las API Keys se crean inicialmente mediante una herramienta administrativa local.

No existe un endpoint público sin autenticación para crear credenciales.

### Configuración

La aplicación requiere:

```env
API_KEY_PEPPER=\<secret>
```

El pepper debe generarse mediante una fuente criptográficamente segura y nunca debe versionarse.

La API Key completa tampoco se almacena en PostgreSQL. La base de datos conserva únicamente su identificador público y un digest HMAC utilizado para verificarla.

### Provisionar una API Key

```bash
uv run python -m scripts.provision_api_key \\
    --user-id 1 \\
    --name "Local development"
```

También puede establecerse una expiración:

```bash
uv run python -m scripts.provision_api_key \\
    --user-id 1 \\
    --name "Temporary integration" \\
    --expires-in-days 90
```

La credencial completa se muestra únicamente durante el provisionamiento y debe tratarse como un secreto.

---

## Autenticación mediante API Key

Los endpoints protegidos utilizan una API Key enviada mediante el header:

```http
X-API-Key: \<api-key>
```

Las API Keys se validan mediante:

1\. extracción del identificador público `key_id`;

2\. búsqueda de la credencial en PostgreSQL;

3\. verificación criptográfica del digest HMAC;

4\. comprobación de revocación;

5\. comprobación de expiración;

6\. comprobación del estado del propietario.

Las credenciales inválidas devuelven `401 Unauthorized`.

Ejemplo:

```json
{
  "error": {
    "code": "API_KEY_INVALID",
    "message": "API Key inválida",
    "details": null
  }
}
```

La aplicación puede utilizar códigos como:

```text
API_KEY_MISSING
API_KEY_INVALID
API_KEY_REVOKED
API_KEY_EXPIRED
API_KEY_OWNER_INACTIVE
```

El header de respuesta `WWW-Authenticate: APIKey` acompaña los errores de autenticación.

El esquema de seguridad está integrado con OpenAPI, por lo que Swagger UI reconoce la API Key mediante el header `X-API-Key`.

`last_used_at` se actualiza de forma limitada para evitar escribir en PostgreSQL en cada request.

---

## Gestión de API Keys

Una API Key autenticada puede crear, listar y revocar únicamente las credenciales pertenecientes a su propio usuario.

- La credencial completa solo se devuelve al crear una API Key.
- Los listados nunca incluyen la credencial completa ni su digest.
- El propietario se obtiene de la API Key autenticada; el cliente no puede enviar `user_id` para administrar credenciales de terceros.
- La revocación conserva la fila en PostgreSQL mediante `revoked_at` para mantener información de auditoría.

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
Cambio en endpoints        -> no requiere migración
Cambio en services         -> no requiere migración
Cambio en validaciones     -> normalmente no requiere migración
Nueva tabla                -> requiere migración
Nueva columna              -> requiere migración
Nueva foreign key          -> requiere migración
Cambio del esquema SQL     -> requiere migración
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
POST /api/v1/users
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
PATCH /api/v1/users/1
Content-Type: application/json
{
  "is_active": false
}
```

Solo los campos enviados son modificados.

### Crear una tarea

```http
POST /api/v1/users/1/tasks
Content-Type: application/json
{
  "title": "Aprender relaciones",
  "description": "Estudiar ForeignKey y relationship"
}
```

### Actualizar parcialmente una tarea

```http
PATCH /api/v1/tasks/1
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
DELETE /api/v1/tasks/1
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

## Cobertura de tests

El proyecto utiliza `pytest-cov` para medir la cobertura del código de aplicación.

La medición incluye cobertura de líneas y ramas sobre el paquete `app`.

La configuración se mantiene en `pyproject.toml`:

```toml
[tool.coverage.run]
branch = true
source = ["app"]
[tool.coverage.report]
show_missing = true
precision = 2
fail_under = 90
[tool.coverage.html]
directory = "htmlcov"
```

### Ejecutar tests con cobertura

```bash
uv run pytest --cov=app --cov-report=term-missing
```

El proyecto mantiene actualmente un umbral mínimo de cobertura del **90%**.

Si la cobertura total cae por debajo de ese porcentaje, el comando finaliza con error aunque los tests funcionales hayan pasado. De esta forma, la cobertura actúa como un quality gate independiente.

### Generar reporte HTML

```bash
uv run pytest --cov=app --cov-report=html
```

El reporte se genera en:

```text
htmlcov/index.html
```

Los archivos generados por Coverage no forman parte del código fuente y están excluidos mediante `.gitignore`:

```text
.coverage
.coverage.*
htmlcov/
```

### Quality gate local

Antes de realizar un commit importante:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=app --cov-report=term-missing
```

El último comando ejecuta la suite de tests, mide cobertura de líneas y ramas y comprueba que se mantiene el umbral mínimo configurado.

Actualmente el proyecto mantiene una cobertura superior al umbral mínimo establecido. El porcentaje exacto no se fija en el README porque evoluciona con el código.

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
uv run pytest --cov=app --cov-report=term-missing
```

El resultado esperado es conceptualmente:

```text
Ruff lint       ✅
Ruff format     ✅
Tests           ✅
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
- Contrato uniforme para errores `404`, `405`, `409` y `422` mediante códigos estables.
- Migraciones de base de datos versionadas.
- Separación entre routers y services.
- Dependencias directas declaradas explícitamente.
- Versiones reproducibles mediante `uv.lock`.
- Tests de API mediante `pytest` y `TestClient`.
- Base de datos separada para testing.
- Linting y formateo automatizados con Ruff.
- Control de calidad local antes de commits importantes.
- Cobertura de líneas y ramas mediante `pytest-cov` con quality gate mínimo del 90%.
- Historial de cambios siguiendo Conventional Commits.
- Los errores de validación no reflejan el valor original recibido.
- API Keys enviadas mediante `X-API-Key` para endpoints protegidos.
- API Keys completas no almacenadas en PostgreSQL; se conserva `key_id` y un digest HMAC.
- Pepper de servidor mantenido fuera del repositorio.
- Validación de revocación, expiración y estado activo del propietario.
- Respuestas de autenticación uniformes con `401 Unauthorized` y `WWW-Authenticate: APIKey`.
- Seguimiento limitado de uso mediante `last_used_at` para reducir escrituras innecesarias.

Todavía faltan mecanismos importantes como autorización por scopes, rate limiting, observabilidad y automatización mediante CI.

---

## Flujo de desarrollo

El desarrollo se organiza en bloques funcionales. Después de completar y comprobar cada bloque se realiza un commit independiente.

```text
Bloque funcional
    |
    v
Ruff lint
    |
    v
Ruff format check
    |
    v
Tests + coverage
    |
    v
Revisar git diff
    |
    v
Conventional Commit
    |
    v
Push
```

Antes de realizar un commit importante:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=app --cov-report=term-missing
git status
git diff
```

Después:

```bash
git add \<archivos>
git commit -m "type(scope): short description"
git push
```

### Convención de commits

El proyecto utiliza **Conventional Commits**.

Formato:

```text
type(scope): description
```

Ejemplos:

```text
feat(api): add v1 versioning
fix(users): handle duplicate email conflicts
test(coverage): add minimum coverage quality gate
docs: update project documentation
ci: run quality checks in GitHub Actions
```

Los scopes son opcionales y se utilizan cuando ayudan a identificar el área afectada.

Los tipos utilizados habitualmente son:

```text
feat      nueva funcionalidad o capacidad
fix       corrección de un bug
refactor  cambio interno sin modificar el comportamiento esperado
test      tests o infraestructura de testing
docs      documentación
ci        integración continua o pipelines
perf      mejoras de rendimiento
chore     mantenimiento general
build     dependencias, packaging o build
style     cambios de formato sin alterar lógica
```

El tipo representa el propósito principal del commit. Los tests y la documentación que acompañan a una nueva funcionalidad no requieren tipos adicionales en el mismo mensaje.

Las descripciones se escriben en inglés y en minúsculas después de `:`.

Los cambios incompatibles pueden marcarse con `!`:

```text
feat(api)!: change job response schema
```

Cuando sea necesario, el cuerpo del commit puede documentar explícitamente el cambio incompatible mediante `BREAKING CHANGE:`.

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
- [x] Manejo de errores `404`, `405`, `409` y `422`.
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
- [x] Versionado de la API bajo `/api/v1`.
- [x] Contrato uniforme de respuestas de error.
- [x] Manejadores globales para errores HTTP y validación.
- [x] Respuestas `422` documentadas en OpenAPI mediante `ErrorResponse`.
- [x] Medición de cobertura mediante `pytest-cov`.
- [x] Cobertura de líneas y branches.
- [x] Quality gate mínimo de cobertura del 90%.
- [x] Artefactos locales de Coverage excluidos mediante `.gitignore`.
- [x] Convención de commits mediante Conventional Commits.
- [x] Fundamentos criptográficos para API Keys.
- [x] Modelo persistente de API Keys.
- [x] Relación `User 1:N ApiKey`.
- [x] Constraints e índices para API Keys.
- [x] Migración de la tabla `api_keys`.
- [x] Pepper de servidor para API Keys.
- [x] Servicio de provisionamiento de API Keys.
- [x] Reintentos defensivos ante colisiones de `key_id`.
- [x] Provisionamiento administrativo sin endpoint público.
- [x] Autenticación mediante `X-API-Key`.
- [x] Verificación HMAC de API Keys.
- [x] Validación de expiración y revocación.
- [x] Rechazo de credenciales pertenecientes a usuarios inactivos.
- [x] Integración de API Key authentication con OpenAPI.
- [x] Seguimiento limitado mediante `last_used_at`.
- [x] Creación autenticada de API Keys.
- [x] Listado privado de API Keys.
- [x] Revocación de API Keys.
- [x] Aislamiento de credenciales por propietario.
- [x] Raw API Key visible únicamente durante su creación.

### Próximos pasos

- [ ] Integrar Ruff y pytest en GitHub Actions.
- [ ] Añadir scopes y autorización basada en scopes para API Keys.
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

Este repositorio forma parte de un proyecto de aprendizaje y evoluciona progresivamente. Algunas decisiones arquitectónicas pueden cambiar a medida que se incorpor
