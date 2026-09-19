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
- [Scopes y autorización](#scopes-y-autorización)
- [Jobs](#procesamiento-de-jobs)
- [Transactional Outbox](#transactional-outbox)
- [Outbox Publisher](#outbox-publisher)
- [Amazon SQS](#amazon-sqs)
- [Base de datos](#base-de-datos)
- [Migraciones con Alembic](#migraciones-con-alembic)
- [Ejecutar la API](#ejecutar-la-api)
- [Ejemplos](#ejemplos)
- [Validación de datos](#validación-de-datos)
- [Testing](#testing)
- [Cobertura de tests](#cobertura-de-tests)
- [Calidad de código](#calidad-de-código)
- [Integración continua](#integración-continua)
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
- Códigos de estado HTTP como `200`, `201`, `202`, `204`, `404`, `405`, `409` y `422`.
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
- Integración continua con GitHub Actions y quality gates automáticos.
- Idempotencia HTTP mediante `Idempotency-Key`.
- Fingerprints deterministas SHA-256 sobre payloads normalizados.
- Control de concurrencia mediante constraints transaccionales de PostgreSQL.

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
| Boto3 | AWS SDK para Python y cliente de Amazon SQS |
| Amazon SQS | Cola estándar para publicación asíncrona de eventos |
| Git | Control de versiones |
| GitHub | Repositorio remoto |
| GitHub Actions | Integración continua y quality gates |

---

## Arquitectura

La arquitectura separa el contrato HTTP, la autenticación, los casos de uso, el dominio, la persistencia y las integraciones externas mediante ports y adapters:

```text
                         Client
                           |
                           | HTTP
                           v
                    FastAPI / Routers
                           |
                 Authentication / Scopes
                           |
                           v
                        Services
                       /        \
                      v          v
                  Domain     SQLAlchemy ORM
                                 |
                                 v
                             PostgreSQL
                         /       |        \
                        v        v         v
                      Jobs   Outbox     Job Idempotency
                              Events        Keys
                                |
                                v
                         Outbox Publisher
                                |
                                v
                         MessageBroker Port
                                |
                                v
                         SQSMessageBroker
                                |
                                v
                           Amazon SQS
```

La creación de Jobs añade una capa idempotente antes de persistir una nueva intención:

```text
POST /api/v1/jobs
Idempotency-Key: X
        |
        v
validar + normalizar payload
        |
        v
fingerprint SHA-256
        |
        v
buscar (user_id, X)
     /             \
 existente        ausente
    |                |
    v                v
 mismo Job      transacción PostgreSQL
 o 409          Job + Outbox + Idempotency
```

### Responsabilidades

`api/`

Configuración transversal de la API: errores, dependencias y router versionado.

`routers/`

Contrato HTTP: rutas, headers, parámetros, códigos de estado y traducción de errores de aplicación.

`contracts/`

Contratos semánticos de payload. Actualmente `contracts/jobs.py` valida y normaliza payloads de Jobs antes de persistirlos o calcular su fingerprint.

`schemas.py`

Modelos Pydantic de entrada y salida.

`services/`

Casos de uso, transacciones, coordinación de persistencia e idempotencia de submit.

`domain/`

Reglas independientes de infraestructura: estados, transiciones, tipos de eventos y cálculo determinista de fingerprints de idempotencia.

`security/`

Generación/verificación de API Keys y scopes.

`ports/`

Interfaces que la aplicación necesita de sistemas externos, como `MessageBroker`.

`adapters/`

Implementaciones concretas de los ports. Actualmente incluye Amazon SQS mediante Boto3.

`models.py`

Modelos SQLAlchemy y restricciones PostgreSQL, incluida la persistencia de `job_idempotency_keys`.

`database.py`

Engine, Session y configuración de persistencia.

`scripts/`

Operaciones administrativas y procesos ejecutables, como provisionamiento y Outbox Publisher.

`migrations/`

Historial de evolución del schema mediante Alembic.

`tests/`

Tests unitarios, HTTP, PostgreSQL, idempotencia, concurrencia, Outbox y adapters externos mediante fakes.

---

## Estructura del proyecto

La estructura principal del proyecto se resume así:

```text
fastapi-rest-api/
|
├── app/
│   ├── adapters/
│   │   └── aws/
│   │       └── sqs.py
│   │
│   ├── api/
│   │   ├── dependencies/
│   │   │   └── auth.py
│   │   ├── errors.py
│   │   └── v1/
│   │       └── router.py
│   │
│   ├── contracts/
│   │   └── jobs.py
│   │
│   ├── domain/
│   │   ├── events.py
│   │   ├── idempotency.py
│   │   └── jobs.py
│   │
│   ├── ports/
│   │   └── message_broker.py
│   │
│   ├── routers/
│   │   ├── api_keys.py
│   │   ├── auth.py
│   │   ├── jobs.py
│   │   ├── tasks.py
│   │   └── users.py
│   │
│   ├── security/
│   │   ├── api_keys.py
│   │   └── scopes.py
│   │
│   ├── services/
│   │   ├── api_keys.py
│   │   ├── jobs.py
│   │   ├── outbox.py
│   │   ├── tasks.py
│   │   └── users.py
│   │
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── migrations/
│   └── versions/
│       └── e13e045eeb8b_add_job_idempotency_keys.py
│
├── scripts/
│   ├── provision_api_key.py
│   └── publish_outbox.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api_key_auth.py
│   ├── test_api_key_management.py
│   ├── test_api_key_model.py
│   ├── test_api_key_scopes.py
│   ├── test_api_key_security.py
│   ├── test_api_key_service.py
│   ├── test_event_domain.py
│   ├── test_job_domain.py
│   ├── test_job_idempotency.py
│   ├── test_job_model.py
│   ├── test_job_service.py
│   ├── test_jobs.py
│   ├── test_main.py
│   ├── test_openapi.py
│   ├── test_outbox_model.py
│   ├── test_outbox_publisher.py
│   ├── test_sqs_adapter.py
│   ├── test_tasks.py
│   └── test_users.py
│
├── .env.example
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

Los archivos `__init__.py`, los directorios `__pycache__/` y los bytecodes `*.pyc` se omiten deliberadamente del árbol documental porque no aportan información arquitectónica.

> `.env` contiene configuración local sensible y no debe subirse al repositorio.

### Gestión de dependencias

Las dependencias directas del proyecto se declaran en `pyproject.toml`.

Las versiones exactas resueltas, incluidas las dependencias transitivas, quedan registradas en `uv.lock`.

`uv.lock` forma parte del código fuente y debe versionarse con Git para mantener instalaciones reproducibles.

Las herramientas utilizadas exclusivamente durante desarrollo, como `pytest` y Ruff, pertenecen al grupo de dependencias de desarrollo.

---

## Modelo de datos

Los recursos principales de la aplicación se apoyan en tablas auxiliares para autenticación, mensajería e idempotencia:

```text
                         User
                    /      |       \
                   v       v        v
                Task    ApiKey     Job
                                   |
                                   v
                         JobIdempotencyKey
Job --(aggregate_id lógico)--> OutboxEvent
```

Un usuario puede tener muchas tareas, muchas API Keys y muchos Jobs. La idempotencia de creación de Jobs se persiste por propietario mediante `job_idempotency_keys`.

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
scopes
```

Características principales:

- Cada API Key pertenece a un único usuario.
- `key_id` es público, único y permite localizar eficientemente la credencial.
- La API Key completa nunca se almacena en PostgreSQL.
- `key_digest` almacena el digest criptográfico utilizado para verificación.
- `revoked_at` permite revocar una credencial conservando información de auditoría.
- `expires_at` permite configurar expiración opcional.
- `last_used_at` registra el uso reciente de la credencial mediante actualizaciones limitadas para evitar una escritura en PostgreSQL por cada request.
- `scopes` persiste los permisos granulares concedidos a la credencial.
- La relación utiliza `ON DELETE CASCADE`, por lo que las credenciales desaparecen si se elimina su propietario.

### `jobs`

Los Jobs representan unidades de trabajo destinadas a procesamiento asíncrono.

Campos principales:

```text
id
user_id
job_type
status
payload
result
error_code
error_message
attempts
created_at
queued_at
started_at
completed_at
```

Los Jobs utilizan UUID como identificador público y PostgreSQL `JSONB` para payloads y resultados estructurados.

El estado se persiste como `VARCHAR` protegido mediante una `CHECK constraint`, evitando depender de un ENUM nativo de PostgreSQL.

Los Jobs utilizan `ON DELETE RESTRICT` respecto a su propietario para preservar el historial de procesamiento.

### `job_idempotency_keys`

Cada fila representa una intención de creación de Job identificada dentro del namespace de un propietario.

Campos principales:

```text
id
user_id
idempotency_key
request_fingerprint
job_id
created_at
```

Garantías principales:

- `UNIQUE(user_id, idempotency_key)` evita que dos requests concurrentes creen dos Jobs para la misma intención.
- `request_fingerprint` almacena un SHA-256 hexadecimal de 64 caracteres calculado sobre `job_type` y el payload validado y normalizado.
- `user_id` referencia `users.id` con `ON DELETE CASCADE`.
- `job_id` referencia `jobs.id` con `ON DELETE CASCADE`.
- Una misma `Idempotency-Key` puede utilizarse por propietarios distintos sin colisionar.
- Las keys son case-sensitive y no son credenciales de autenticación.
- No existe expiración automática de Idempotency-Keys en esta fase.
- Los Jobs históricos anteriores a esta migración no reciben un registro de idempotencia inventado.

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

### Jobs

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/jobs` | Crear un Job para procesamiento asíncrono |
| `GET` | `/api/v1/jobs` | Listar los Jobs del usuario autenticado |
| `GET` | `/api/v1/jobs/{job_id}` | Consultar un Job del usuario autenticado |

---

## Versionado de la API

Los endpoints de negocio se publican bajo un prefijo de versión:

```text
/api/v1
```

Por ejemplo:

```text
GET  /api/v1/users
POST /api/v1/users
GET  /api/v1/tasks/{task_id}
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
202 Accepted
    La solicitud fue aceptada para procesamiento asíncrono, pero el procesamiento todavía no ha finalizado.
204 No Content
    El recurso fue eliminado correctamente.
401 Unauthorized
    La solicitud no incluye una credencial válida para acceder al recurso protegido.
403 Forbidden
    La credencial es válida, pero no posee los scopes requeridos para la operación.
404 Not Found
    El recurso solicitado no existe.
405 Method Not Allowed
    El método HTTP no está permitido para la ruta solicitada.
409 Conflict
    La operación entra en conflicto con el estado actual de los datos.
422 Unprocessable Entity
    Los datos enviados no cumplen las validaciones esperadas.
```

Por ejemplo, intentar eliminar un usuario que todavía tiene tareas asociadas devuelve `409 Conflict`. También se utiliza `409` cuando una `Idempotency-Key` ya fue empleada por el mismo propietario con una solicitud diferente.

PostgreSQL protege las invariantes mediante constraints y la aplicación traduce los conflictos esperados a respuestas HTTP estables.

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
JOB_NOT_FOUND
IDEMPOTENCY_KEY_CONFLICT
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
INSUFFICIENT_SCOPE
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
DB_ECHO=false
```

`DB_ECHO` controla el logging SQL de SQLAlchemy.

El valor predeterminado es `false` para evitar generar logs SQL detallados innecesariamente. Puede activarse temporalmente durante desarrollo:

```env
DB_ECHO=true
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
API_KEY_PEPPER=<secret>
API_KEY_MAX_ACTIVE_PER_USER=10
```

> [!WARNING]

> `API_KEY_PEPPER` debe tratarse como un secreto y generarse mediante una fuente criptográficamente segura. Nunca debe versionarse. Cambiarlo invalida las credenciales existentes, porque los HMAC almacenados dejan de coincidir con las credenciales presentadas.

La API Key completa tampoco se almacena en PostgreSQL. La base de datos conserva únicamente su identificador público y un digest HMAC utilizado para verificarla.

### Provisionar una API Key

```powershell
uv run python -m scripts.provision_api_key `
    --user-id 1 `
    --name "Local administration" `
    --scope api-keys:read `
    --scope api-keys:write
```

También puede establecerse una expiración:

```bash
uv run python -m scripts.provision_api_key \
    --user-id 1 \
    --name "Temporary integration" \
    --expires-in-days 90
```

La credencial completa se muestra únicamente durante el provisionamiento y debe tratarse como un secreto.

---

## Autenticación mediante API Key

Los endpoints protegidos utilizan una API Key enviada mediante el header:

```http
X-API-Key: <api-key>
```

Las API Keys se validan mediante:

1. extracción del identificador público `key_id`;
2. búsqueda de la credencial en PostgreSQL;
3. verificación criptográfica del digest HMAC;
4. comprobación de revocación;
5. comprobación de expiración;
6. comprobación del estado del propietario.

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

Una API Key autenticada con los scopes requeridos puede crear, listar y revocar únicamente las credenciales pertenecientes a su propio usuario.

- La credencial completa solo se devuelve al crear una API Key.
- Los listados nunca incluyen la credencial completa ni su digest.
- El propietario se obtiene de la API Key autenticada; el cliente no puede enviar `user_id` para administrar credenciales de terceros.
- La revocación conserva la fila en PostgreSQL mediante `revoked_at` para mantener información de auditoría.

### Hardening de API Keys

La implementación aplica medidas adicionales de seguridad y consistencia:

- Existe un límite configurable de API Keys activas por usuario.
- Las credenciales revocadas o expiradas no cuentan para ese límite.
- La creación concurrente se serializa por propietario mediante bloqueo de fila en PostgreSQL.
- Las respuestas que muestran una API Key completa utilizan `Cache-Control: no-store`.
- La raw API Key solamente se muestra durante la creación.
- Los listados nunca contienen la raw key ni su digest.
- Los errores para `key_id` inexistente y secret incorrecto utilizan el mismo contrato público.
- Los scopes siguen el principio de mínimo privilegio.
- Una credencial no puede delegar permisos que ella misma no posee.

El valor `API_KEY_PEPPER` debe tratarse como un secreto. Cambiarlo invalida las credenciales existentes.

---

## Scopes y autorización

Las API Keys pueden tener permisos granulares denominados scopes.

Actualmente existen:

```text
api-keys:read
api-keys:write
jobs:read
jobs:write
```

`api-keys:read` permite listar las credenciales del propietario.

`api-keys:write` permite crear y revocar credenciales.

`jobs:read` permite listar y consultar los Jobs del usuario autenticado.

`jobs:write` permite crear Jobs para el usuario autenticado.

Una API Key autenticada que no posee el scope requerido recibe:

```text
403 Forbidden
```

```json
{
  "error": {
    "code": "INSUFFICIENT_SCOPE",
    "message": "La API Key no tiene los scopes requeridos",
    "details": [
      {
        "missing_scopes": [
          "api-keys:write"
        ]
      }
    ]
  }
}
```

Las credenciales nuevas no reciben scopes implícitamente.

Además, una API Key no puede crear otra credencial con permisos que ella misma no posea. Esto evita escalamiento de privilegios.

---

## Procesamiento de Jobs

El dominio principal del proyecto evoluciona hacia procesamiento asíncrono mediante Jobs.

Un Job representa una unidad de trabajo cuyo ciclo de vida se controla mediante una máquina de estados.

```text
pending
   |
   v
queued
   |
   v
running
 /     \
v       v
succeeded
failed
```

Las transiciones permitidas inicialmente son:

```text
pending -> queued
queued -> running
running -> succeeded
running -> failed
```

`succeeded` y `failed` son estados terminales en esta primera versión.

Las transiciones se validan en una capa de dominio independiente de FastAPI, PostgreSQL y el sistema de colas.

### Contratos de payload

Cada `JobType` posee un contrato de payload explícito.

Actualmente `generate_report` requiere:

```json
{
  "title": "Monthly sales",
  "content": "Report content",
  "format": "pdf"
}
```

Los campos desconocidos son rechazados.

Los Jobs inválidos se rechazan con `422 VALIDATION_ERROR` antes de persistir el `Job`, su `OutboxEvent` o un registro de idempotencia.

El contrato se valida tanto en la frontera HTTP como en el caso de uso `submit_job()`, evitando que callers internos puedan persistir Jobs semánticamente inválidos.

### Crear un Job

```http
POST /api/v1/jobs
X-API-Key: <api-key>
Idempotency-Key: <unique-key>
Content-Type: application/json
```

Requiere:

```text
jobs:write
```

`Idempotency-Key` es obligatoria para `POST /api/v1/jobs`. Admite entre 1 y 128 caracteres y únicamente:

```text
A-Z
a-z
0-9
.
_
:
-
```

Las keys son case-sensitive. Se recomienda utilizar identificadores únicos por intención lógica, por ejemplo UUIDs.

Ejemplo:

```json
{
  "job_type": "generate_report",
  "payload": {
    "title": "Monthly sales",
    "content": "Report content",
    "format": "pdf"
  }
}
```

Primera respuesta:

```http
202 Accepted
Location: /api/v1/jobs/{job_id}
Cache-Control: no-store
Idempotency-Replayed: false
```

```json
{
  "id": "4a973290-14d6-4daf-b564-986203494ceb",
  "job_type": "generate_report",
  "status": "pending",
  "created_at": "..."
}
```

`202 Accepted` indica que el Job fue aceptado para procesamiento, no que dicho procesamiento haya terminado. El header `Location` apunta al recurso que permite consultar su estado.

El propietario del Job se obtiene de la API Key autenticada. Campos como `user_id`, `status`, `attempts`, `result` y los timestamps del ciclo de vida son administrados exclusivamente por el servidor.

### Idempotencia al crear Jobs

El backend calcula un fingerprint SHA-256 sobre una representación canónica de:

```text
job_type
+
payload validado y normalizado
```

El fingerprint se calcula después de aplicar el contrato del payload. Por ejemplo, valores equivalentes tras normalización, como `" Monthly sales "` y `"Monthly sales"`, representan la misma intención.

La key se evalúa dentro del namespace del propietario autenticado:

```text
misma key + mismo usuario + mismo request
    -> 202, mismo Job
       Idempotency-Replayed: true
misma key + mismo usuario + request diferente
    -> 409 IDEMPOTENCY_KEY_CONFLICT
misma key + usuario diferente
    -> operación independiente
```

Un replay devuelve el mismo recurso lógico y el mismo `Location`. No se mantiene un cache byte-for-byte de la respuesta HTTP histórica: si el Job ya avanzó de estado, el replay puede reflejar el estado actual del mismo Job.

La protección ante concurrencia no depende del `SELECT` previo. La garantía final proviene de PostgreSQL mediante:

```text
UNIQUE(user_id, idempotency_key)
```

`Job`, `OutboxEvent` y `JobIdempotencyKey` se crean dentro de la misma transacción. Si dos requests concurrentes compiten por la misma key, uno confirma la transacción y el otro hace rollback, recupera el registro ganador y devuelve el mismo Job.

`Idempotency-Key` es un identificador opaco de operación. No es una API Key, no sustituye autenticación y no se trata como secreto.

En esta fase no existe TTL ni limpieza automática de Idempotency-Keys. Los clientes deben utilizar una nueva key para cada nueva intención lógica.

### Consultar Jobs

Los Jobs pueden consultarse mediante una API Key con el scope:

```text
jobs:read
```

Endpoints:

```http
GET /api/v1/jobs
GET /api/v1/jobs/{job_id}
```

El listado admite paginación mediante los parámetros `limit` y `offset`:

```text
limit=20
offset=0
```

`limit` debe estar entre `1` y `100`.

Los Jobs están aislados por propietario: cada API Key solo puede consultar los Jobs de su propio usuario. Un Job inexistente y un Job perteneciente a otro usuario producen la misma respuesta para evitar revelar la existencia de recursos ajenos:

```http
404 Not Found
```

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job no encontrado",
    "details": null
  }
}
```

Las respuestas de seguimiento utilizan `Cache-Control: no-store` porque el estado del Job puede cambiar durante su procesamiento.

---

## Transactional Outbox

El submit de un Job utiliza el patrón Transactional Outbox para evitar inconsistencias entre PostgreSQL y el sistema de mensajería.

Con idempotencia habilitada, las tres piezas de la intención se persisten dentro de una única transacción PostgreSQL:

```text
BEGIN
INSERT Job
INSERT OutboxEvent(job.submitted)
INSERT JobIdempotencyKey
COMMIT
```

Si cualquiera de las escrituras falla, toda la transacción se revierte. De esta forma:

- no puede persistirse un Job sin su evento de salida;
- no puede persistirse un evento huérfano sin el Job asociado;
- no puede quedar registrada una `Idempotency-Key` que apunte a un Job cuya transacción no fue confirmada.

La constraint `UNIQUE(user_id, idempotency_key)` complementa la atomicidad y protege la creación de Jobs ante carreras concurrentes.

Los eventos pendientes se identifican mediante:

```text
published_at IS NULL
```

La consulta de eventos pendientes se apoya en un índice parcial para evitar recorrer eventos que ya fueron publicados.

Un evento `job.submitted` contiene únicamente información mínima sobre el Job. El payload completo del procesamiento permanece en la tabla `jobs`.

El contrato de eventos parte de un versionado inicial para permitir su evolución de forma explícita.

Crear el `OutboxEvent` no significa que el Job ya se encuentre en una cola. Mientras no exista confirmación de publicación, el estado del Job continúa siendo `pending`.

La idempotencia HTTP de `POST /jobs` es independiente de la idempotencia que deberán implementar los futuros consumidores de SQS para tolerar mensajes duplicados bajo semántica at-least-once.

---

## Outbox Publisher

Los eventos persistidos mediante Transactional Outbox son procesados por un publisher independiente del proveedor de mensajería.

La aplicación define un `MessageBroker` como port:

```text
Outbox Publisher
       |
       v
MessageBroker
       |
       +-- Fake adapter (tests)
       |
       +-- SQSMessageBroker -> Amazon SQS Standard Queue
```

El publisher selecciona eventos pendientes utilizando PostgreSQL:

```sql
FOR UPDATE SKIP LOCKED
```

Esto permite que múltiples publishers trabajen concurrentemente sin seleccionar simultáneamente la misma fila.

Cuando `job.submitted` se publica correctamente:

```text
OutboxEvent.published_at = timestamp
Job.status = queued
Job.queued_at = timestamp
```

Si el broker falla:

```text
OutboxEvent.attempts += 1
OutboxEvent.last_error = ...
OutboxEvent.published_at = NULL
Job.status = pending
```

La arquitectura utiliza semántica **at-least-once**. Existe una pequeña ventana entre la confirmación del broker y el commit de PostgreSQL en la que un evento podría publicarse nuevamente después de un fallo.

Por esta razón cada mensaje incluye un `event_id` estable y los consumidores deberán ser idempotentes.

Esto documenta justamente la garantía real de la fase: **at-least-once**, no exactly-once.

---

## Amazon SQS

El proyecto utiliza un adapter de Amazon SQS que implementa el port `MessageBroker`.

```text
Outbox Publisher
       |
       v
MessageBroker
       |
       v
SQSMessageBroker
       |
       v
Amazon SQS Standard Queue
```

Los eventos se serializan como JSON versionado e incluyen un `event_id` estable.

El cliente AWS utiliza:

```text
retry mode: standard
total attempts: 3
connect timeout: configurable
read timeout: configurable
```

Las credenciales AWS no se almacenan en el código ni forman parte de la configuración propia de la aplicación. Boto3 utiliza la cadena estándar de proveedores de credenciales y, en AWS, deben preferirse IAM Roles con permisos mínimos.

Variables de configuración:

```env
AWS_REGION=<region>
SQS_JOBS_QUEUE_URL=<queue-url>
AWS_CONNECT_TIMEOUT_SECONDS=2
AWS_READ_TIMEOUT_SECONDS=5
AWS_TOTAL_MAX_ATTEMPTS=3
```

Ejecutar el publisher:

```bash
uv run python -m scripts.publish_outbox --max-events 100
```

Cuando SQS confirma `job.submitted`, el Outbox se marca como publicado y el Job transiciona de `pending` a `queued`.

Amazon SQS Standard ofrece entrega at-least-once, por lo que los consumidores deben diseñarse para tolerar mensajes duplicados.

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

El archivo generado debe revisarse manualmente antes de aplicarlo. `--autogenerate` puede proponer alteraciones no relacionadas con el cambio actual, por lo que la migración nunca se acepta sin inspección.

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

### Migración de idempotencia de Jobs

La FASE 4A incorpora:

```text
e13e045eeb8b_add_job_idempotency_keys.py
```

Cadena:

```text
dd68f1425146
    |
    v
e13e045eeb8b
```

La migración crea exclusivamente la tabla:

```text
job_idempotency_keys
```

con sus `CHECK constraints`, foreign keys y:

```text
UNIQUE(user_id, idempotency_key)
```

No modifica retrospectivamente `jobs`, `outbox_events`, `api_keys`, `users` ni `tasks`.

No se realiza backfill para Jobs históricos. La garantía de idempotencia comienza con los nuevos `POST /api/v1/jobs` posteriores a la incorporación de esta fase.

Una migración aplicada y versionada no se edita retrospectivamente; cualquier ajuste posterior debe realizarse mediante una nueva migración hacia adelante.

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
JobSubmit
JobAcceptedResponse
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

La suite combina distintos niveles de testing:

- Tests unitarios para reglas de dominio y seguridad.
- Tests HTTP mediante FastAPI `TestClient`.
- Tests de integración contra PostgreSQL.
- Tests de constraints e integridad referencial.
- Tests de autenticación y autorización mediante API Keys.
- Tests de Jobs, contratos de payload y máquina de estados.
- Tests de idempotencia HTTP y persistente.
- Tests de Transactional Outbox.
- Tests de concurrencia utilizando sesiones PostgreSQL independientes.
- Tests del adapter SQS mediante fakes, sin depender de una cuenta AWS real.

La suite normal no requiere acceso a servicios AWS.

La estructura actual contiene **19 módulos `test_*.py`**, además de `conftest.py`. La FASE 4A añade `tests/test_job_idempotency.py` y amplía `tests/test_jobs.py`, `tests/test_job_service.py` y `tests/test_outbox_publisher.py`.

La cobertura de idempotencia verifica, entre otros casos:

```text
fingerprint determinista
fingerprint cambia si cambia el request
Idempotency-Key obligatoria
header inválido -> 422
primer submit -> replayed=false
misma key + mismo request -> mismo Job
misma key + request diferente -> 409
normalización semántica del payload
namespace por usuario
una sola fila ante submit concurrente
OpenAPI documenta el header y 409
```

El test concurrente utiliza dos `Session` independientes y conexiones reales a PostgreSQL. La protección se valida contra la `UNIQUE(user_id, idempotency_key)`, no mediante mocks.

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

### Ejecutar los tests de idempotencia

```bash
uv run pytest tests/test_job_idempotency.py -v
uv run pytest tests/test_jobs.py -v
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

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=app --cov-report=term-missing
uv run alembic current
uv run alembic heads
git diff --check
```

Este conjunto valida linting, formato, tests y cobertura, estado de migraciones y errores de whitespace en el diff antes de integrar cambios.

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

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=app --cov-report=term-missing
uv run alembic current
uv run alembic heads
git diff --check
```

El resultado esperado es conceptualmente:

```text
Ruff lint          ✅
Ruff format        ✅
Tests + coverage   ✅
Alembic current    ✅
Alembic heads      ✅
Git diff check     ✅
```

Este conjunto de comandos define el **contrato de calidad local** del proyecto.

GitHub Actions ejecuta automáticamente las comprobaciones de calidad en integración continua para reducir diferencias entre el entorno local y CI.

---

## Integración continua

El repositorio utiliza GitHub Actions como quality gate automático.

El workflow ejecuta el proyecto sobre Linux con Python 3.11 y un servicio PostgreSQL aislado.

En cada Pull Request hacia `main` y cada actualización de `main` se verifican:

```text
uv sync --locked --dev
Ruff lint
Ruff format
Alembic migrations
pytest
branch coverage >= 90 %
```

La suite de CI no necesita acceso a AWS. Los adapters externos se prueban mediante fakes.

PostgreSQL utiliza bases efímeras exclusivas del workflow y las credenciales de CI se almacenan mediante GitHub Actions Secrets.

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
- Contratos de payload separados y normalización antes de persistencia.
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
- Scopes persistentes para API Keys y autorización granular por operación.
- Prevención de escalamiento de privilegios al delegar scopes.
- Aislamiento de Jobs por propietario y respuesta uniforme `404 JOB_NOT_FOUND` para recursos inexistentes o ajenos.
- Respuestas de seguimiento de Jobs con `Cache-Control: no-store`.
- `Idempotency-Key` obligatoria y validada para creación de Jobs.
- Fingerprint SHA-256 calculado sobre payload validado y normalizado.
- Namespace idempotente por propietario mediante `(user_id, idempotency_key)`.
- Protección de carreras mediante `UNIQUE(user_id, idempotency_key)` en PostgreSQL.
- `Job`, `OutboxEvent` y registro de idempotencia persistidos atómicamente.
- Conflictos de reutilización expresados como `409 IDEMPOTENCY_KEY_CONFLICT`.
- Integración de `Idempotency-Key` y `409` en OpenAPI.
- Tests concurrentes con sesiones PostgreSQL independientes.

`Idempotency-Key` no es una credencial y no sustituye `X-API-Key`. Tampoco se almacena la API Key raw dentro de la tabla de idempotencia.

Todavía faltan mecanismos importantes como rate limiting, observabilidad, expiración/limpieza de Idempotency-Keys y hardening adicional del Outbox.

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
git add <archivos>
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
feat      nueva funcionalidad o capacidad
fix       corrección de un bug
refactor  cambio interno sin modificar el comportamiento esperado
test      tests o infraestructura de testing
docs      documentación
ci        integración continua o pipelines
perf      mejoras de rendimiento
chore     mantenimiento general
build     dependencias, packaging o build
style     cambios de formato sin alterar lógica
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
- [x] Contratos de payload en `app/contracts/`.
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
- [x] Scopes persistentes para API Keys.
- [x] Autorización granular por scope.
- [x] `403 INSUFFICIENT_SCOPE`.
- [x] Prevención de escalamiento de privilegios al delegar scopes.
- [x] Límite de API Keys activas por propietario.
- [x] Protección ante creación concurrente de API Keys.
- [x] Respuestas sensibles con `Cache-Control: no-store`.
- [x] Regression tests contra exposición de secretos.
- [x] Hardening completo del ciclo de vida de API Keys.
- [x] Dominio inicial de Jobs.
- [x] Máquina de estados de Jobs.
- [x] Validación de transiciones de estado.
- [x] Tests unitarios de reglas de transición.
- [x] Persistencia PostgreSQL para Jobs.
- [x] Identificadores UUID para Jobs.
- [x] Payload y resultado mediante PostgreSQL JSONB.
- [x] Constraint persistente para estados de Job.
- [x] Métrica de intentos de procesamiento.
- [x] Timestamps del ciclo de vida de Jobs.
- [x] Integridad `User 1:N Job`.
- [x] Submit autenticado de Jobs.
- [x] Scope `jobs:write`.
- [x] Scope `jobs:read`.
- [x] `202 Accepted` para procesamiento asíncrono.
- [x] Ownership derivado de API Key.
- [x] Validación de tipos de Job.
- [x] Payloads tipados, validados y normalizados.
- [x] Protección de campos administrados por servidor.
- [x] GET individual de Jobs.
- [x] Listado paginado de Jobs.
- [x] Aislamiento de Jobs por propietario.
- [x] `404` uniforme para Jobs inexistentes o ajenos.
- [x] Status resource para Jobs asíncronos.
- [x] Header `Location` en `202 Accepted`.
- [x] Idempotencia en `POST /api/v1/jobs`.
- [x] Header obligatorio `Idempotency-Key`.
- [x] Validación de formato y longitud de `Idempotency-Key`.
- [x] Fingerprint SHA-256 determinista sobre request normalizado.
- [x] Namespace de idempotencia por propietario.
- [x] Replay de la misma intención devuelve el mismo Job.
- [x] Header `Idempotency-Replayed`.
- [x] `409 IDEMPOTENCY_KEY_CONFLICT` para reutilización incompatible.
- [x] Persistencia `job_idempotency_keys`.
- [x] Constraint `UNIQUE(user_id, idempotency_key)`.
- [x] Protección ante submits concurrentes con la misma key.
- [x] Test concurrente con sesiones PostgreSQL independientes.
- [x] Migración `e13e045eeb8b_add_job_idempotency_keys`.
- [x] Transactional Outbox.
- [x] Evento `job.submitted`.
- [x] `Job` + `OutboxEvent` + `JobIdempotencyKey` en una transacción PostgreSQL.
- [x] Rollback atómico ante errores.
- [x] Índice parcial para eventos pendientes.
- [x] Versionado inicial de eventos.
- [x] Message broker port.
- [x] Message envelope versionado.
- [x] Outbox publisher.
- [x] Transición `pending -> queued` tras publicación.
- [x] Persistencia de errores de publicación.
- [x] Retry de eventos no publicados.
- [x] `FOR UPDATE SKIP LOCKED`.
- [x] Protección ante publishers concurrentes.
- [x] Semántica at-least-once documentada.
- [x] AWS SQS adapter.
- [x] Serialización JSON de MessageEnvelope.
- [x] Standard retry mode del AWS SDK.
- [x] Timeouts configurables.
- [x] Límite de tamaño SQS.
- [x] Publisher ejecutable.
- [x] Tests sin dependencia de AWS.
- [x] Integración Outbox → SQS.
- [x] GitHub Actions — implementado.

### Próximos pasos

- [ ] Hardening del Outbox: errores permanentes, backoff y poison events.
- [ ] Implementar workers y estrategia de reintentos.
- [ ] Añadir Dead Letter Queue.
- [ ] Diseñar idempotencia de consumidores para mensajes duplicados de SQS.
- [ ] Implementar webhooks firmados con HMAC.
- [ ] Añadir retry y backoff para webhooks.
- [ ] Implementar rate limiting.
- [ ] Añadir logging estructurado y correlation IDs.
- [ ] Añadir métricas y observabilidad.
- [ ] Definir retención/TTL y cleanup de Idempotency-Keys cuando corresponda.
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

Este repositorio forma parte de un proyecto de aprendizaje y evoluciona progresivamente.
