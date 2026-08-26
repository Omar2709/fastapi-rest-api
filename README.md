# FastAPI REST API

API REST construida desde cero con Python como proyecto de aprendizaje de desarrollo backend.

El objetivo principal de este proyecto no es solamente crear una API funcional, sino comprender cómo encaja cada pieza del backend: HTTP, validación de datos, acceso a base de datos, ORM, migraciones, relaciones entre tablas, manejo de errores, gestión de dependencias y control de versiones.

> Este proyecto está en desarrollo y este README se actualizará a medida que se incorporen nuevas funcionalidades y conceptos.

---

## Objetivos de aprendizaje

Este proyecto busca aprender de forma práctica:

* Cómo funciona una API REST.
* Métodos HTTP: `GET`, `POST`, `PATCH` y `DELETE`.
* Códigos de estado HTTP como `200`, `201`, `204`, `404`, `409` y `422`.
* Path parameters, query parameters y request bodies.
* Validación de datos con Pydantic.
* Separación entre modelos de entrada, salida y persistencia.
* Persistencia de datos con PostgreSQL.
* Uso de SQL y conceptos relacionales.
* ORM con SQLAlchemy 2.x.
* Gestión de sesiones y transacciones.
* Migraciones de base de datos con Alembic.
* Relaciones `1:N` y claves foráneas.
* Manejo de errores de integridad.
* Arquitectura por capas.
* Gestión de dependencias y entornos con `uv`.
* Uso de `pyproject.toml` y `uv.lock`.
* Control de versiones con Git y GitHub.

---

## Tecnologías

| Tecnología        | Uso                                                 |
| ----------------- | --------------------------------------------------- |
| Python            | Lenguaje principal                                  |
| FastAPI           | Framework para construir la API                     |
| Pydantic          | Validación y serialización de datos                 |
| Pydantic Settings | Configuración mediante variables de entorno         |
| SQLAlchemy 2.x    | ORM y acceso a la base de datos                     |
| Psycopg 3         | Driver de PostgreSQL para Python                    |
| PostgreSQL        | Base de datos relacional                            |
| Alembic           | Migraciones y versionado del esquema                |
| Uvicorn           | Servidor ASGI                                       |
| uv                | Gestión de dependencias, entorno virtual y lockfile |
| Git               | Control de versiones                                |
| GitHub            | Repositorio remoto                                  |

---

## Arquitectura actual

El proyecto utiliza una separación sencilla por responsabilidades:

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
    rutas, parámetros, status codes y HTTPException.

services/
    Lógica de aplicación y operaciones con SQLAlchemy.

schemas.py
    Modelos Pydantic para datos de entrada y salida.

models.py
    Modelos ORM que representan las tablas PostgreSQL.

database.py
    Engine, Session y conexión con la base de datos.

config.py
    Configuración cargada desde variables de entorno.

migrations/
    Historial de cambios del esquema administrado por Alembic.
```

---

## Estructura del proyecto

Actualmente el proyecto tiene una estructura similar a:

```text
fastapi-rest-api/
│
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

Las dependencias directas del proyecto se declaran en:

```text
pyproject.toml
```

Las versiones exactas resueltas, incluyendo dependencias transitivas, quedan registradas en:

```text
uv.lock
```

`uv.lock` forma parte del código fuente del proyecto y debe versionarse con Git.

---

## Modelo de datos actual

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

Un usuario puede tener muchas tareas, mientras que cada tarea pertenece a un único usuario.

### `users`

Campos principales:

```text
id
name
email
created_at
is_active
```

Características importantes:

* `id` es la clave primaria.
* PostgreSQL genera automáticamente el `id`.
* `email` es obligatorio y único.
* `name` tiene restricciones de longitud.
* `is_active` permite desactivar usuarios sin eliminarlos físicamente.
* `created_at` se genera automáticamente.

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

Características importantes:

* `id` es la clave primaria.
* `user_id` es una clave foránea hacia `users.id`.
* `user_id` tiene un índice para acelerar consultas por usuario.
* Una tarea no puede existir sin usuario.
* `is_completed` comienza en `false`.
* `description` puede ser `NULL`.
* La relación utiliza `ON DELETE RESTRICT`.

Esto significa que PostgreSQL impide eliminar un usuario mientras tenga tareas asociadas.

---

## Endpoints actuales

### General

| Método | Endpoint  | Descripción                              |
| ------ | --------- | ---------------------------------------- |
| `GET`  | `/`       | Mensaje principal                        |
| `GET`  | `/health` | Comprobación básica del estado de la API |

### Users

| Método   | Endpoint           | Descripción                        |
| -------- | ------------------ | ---------------------------------- |
| `GET`    | `/users`           | Obtener usuarios                   |
| `GET`    | `/users/{user_id}` | Obtener un usuario                 |
| `POST`   | `/users`           | Crear un usuario                   |
| `PATCH`  | `/users/{user_id}` | Actualizar parcialmente un usuario |
| `DELETE` | `/users/{user_id}` | Eliminar un usuario                |

El listado admite:

```http
GET /users?limit=10
```

con un límite validado entre `1` y `100`.

### Tasks

| Método   | Endpoint                 | Descripción                       |
| -------- | ------------------------ | --------------------------------- |
| `POST`   | `/users/{user_id}/tasks` | Crear una tarea para un usuario   |
| `GET`    | `/users/{user_id}/tasks` | Obtener las tareas de un usuario  |
| `GET`    | `/tasks/{task_id}`       | Obtener una tarea por ID          |
| `PATCH`  | `/tasks/{task_id}`       | Actualizar parcialmente una tarea |
| `DELETE` | `/tasks/{task_id}`       | Eliminar una tarea                |

El CRUD básico de `Task` está completo.

El endpoint `PATCH` permite modificar únicamente los campos enviados. Campos controlados por la aplicación como `id`, `created_at` y `user_id` no forman parte del esquema de actualización.

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

PostgreSQL bloquea primero la eliminación mediante la clave foránea y la aplicación convierte ese error en una respuesta HTTP comprensible.

---

## Requisitos

Antes de ejecutar el proyecto necesitas:

* Python 3.11 o superior.
* PostgreSQL instalado y ejecutándose.
* Git.
* `uv`.

El proyecto utiliza actualmente Python 3.11+ debido a los requisitos de compatibilidad del conjunto de dependencias bloqueado.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd fastapi-rest-api
```

### 2. Verificar `uv`

```bash
uv --version
```

En Windows también puede instalarse mediante WinGet:

```powershell
winget install --id=astral-sh.uv -e
```

### 3. Instalar las dependencias

Desde la raíz del proyecto:

```bash
uv sync
```

`uv` utiliza `pyproject.toml` y `uv.lock` para crear y sincronizar automáticamente el entorno virtual `.venv`.

No es necesario crear manualmente el entorno con `python -m venv` ni instalar las dependencias mediante `pip install -r requirements.txt`.

### 4. Ejecutar comandos dentro del entorno

No es necesario activar manualmente `.venv` si se utiliza:

```bash
uv run
```

Por ejemplo:

```bash
uv run python --version
```

`uv run` ejecuta el comando dentro del entorno del proyecto.

---

## Gestión de dependencias con uv

### Agregar una dependencia

```bash
uv add nombre-paquete
```

Por ejemplo:

```bash
uv add redis
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

Las dependencias directas deben declararse mediante `pyproject.toml`.

No se deben agregar manualmente como dependencias directas paquetes transitivos que solamente son requeridos por otras librerías.

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

La base de datos utilizada durante el desarrollo es:

```text
fastapi_learning
```

Puedes crearla con PostgreSQL:

```bash
createdb fastapi_learning
```

Dependiendo de tu configuración local puede ser necesario especificar un usuario:

```bash
createdb -U postgres fastapi_learning
```

También puedes utilizar:

```sql
CREATE DATABASE fastapi_learning;
```

desde `psql`.

---

## Migraciones con Alembic

El esquema de la base de datos se administra mediante Alembic.

Todos los comandos se ejecutan dentro del entorno administrado por `uv`.

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

### Aplicar todas las migraciones pendientes

```bash
uv run alembic upgrade head
```

### Crear una migración automáticamente

Después de modificar los modelos SQLAlchemy:

```bash
uv run alembic revision --autogenerate -m "descripcion del cambio"
```

Siempre se debe revisar manualmente el archivo generado antes de ejecutar:

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

---

## Documentación interactiva

Con la API ejecutándose:

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

Swagger permite probar directamente los endpoints desde el navegador.

---

## Ejemplos

### Crear usuario

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

Respuesta aproximada:

```json
{
  "id": 1,
  "title": "Aprender relaciones",
  "description": "Estudiar ForeignKey y relationship",
  "is_completed": false,
  "created_at": "2026-01-01T12:00:00Z",
  "user_id": 1
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

Solo se modifican los campos enviados.

Por ejemplo:

```json
{
  "description": null
}
```

permite eliminar la descripción de la tarea sin modificar el resto de campos.

### Eliminar una tarea

```http
DELETE /tasks/1
```

Si la tarea existe:

```text
204 No Content
```

Si no existe:

```text
404 Not Found
```

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

Ejemplo conceptual:

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
SQLAlchemy Task
 |
 v
PostgreSQL
```

Para actualizaciones parciales se utilizan únicamente los campos enviados por el cliente.

Esto evita modificar accidentalmente otros valores existentes.

En la respuesta:

```text
PostgreSQL
 |
 v
SQLAlchemy Model
 |
 v
Pydantic Response
 |
 v
JSON
```

---

## Seguridad y buenas prácticas actuales

El proyecto ya aplica algunas buenas prácticas:

* Variables sensibles fuera del código mediante `.env`.
* `.env` ignorado por Git.
* Validación de request bodies con Pydantic.
* Restricciones también a nivel PostgreSQL.
* Emails únicos mediante una constraint `UNIQUE`.
* Foreign keys para garantizar integridad referencial.
* `rollback()` después de errores de transacción.
* Modelos de entrada y salida separados.
* Campos modificables controlados mediante schemas específicos.
* Manejo de errores HTTP como `404`, `409` y `422`.
* Migraciones de base de datos versionadas.
* Separación entre routers y services.
* Dependencias directas declaradas explícitamente.
* Versiones reproducibles mediante `uv.lock`.

Todavía faltan mecanismos importantes como tests automatizados, autenticación y autorización.

---

## Flujo de desarrollo

El desarrollo se organiza en bloques funcionales.

Después de completar y comprobar cada bloque se realiza un commit independiente.

Flujo:

```text
Implementar
    |
    v
Probar
    |
    v
Revisar cambios
    |
    v
Commit
    |
    v
Siguiente bloque
```

Antes de realizar un commit:

```bash
git status
git diff
```

Después:

```bash
git add <archivos>
git commit -m "Descripcion clara del cambio"
git push
```

Los mensajes de commit buscan ser breves y descriptivos.

Las migraciones de Alembic y `uv.lock` forman parte del código fuente y deben incluirse en Git.

Nunca se debe incluir `.env`.

---

## Estado actual

### Implementado

* [x] Proyecto Python.
* [x] FastAPI.
* [x] Uvicorn.
* [x] Documentación OpenAPI / Swagger.
* [x] Validación con Pydantic.
* [x] PostgreSQL.
* [x] SQLAlchemy ORM.
* [x] Psycopg 3.
* [x] Configuración mediante `.env`.
* [x] CRUD de usuarios.
* [x] Manejo de errores `404`, `409` y `422`.
* [x] Alembic.
* [x] Migraciones.
* [x] Arquitectura con routers y services.
* [x] Relación `User 1:N Task`.
* [x] Foreign keys.
* [x] CRUD de tareas.
* [x] Actualizaciones parciales con `PATCH`.
* [x] Gestión de dependencias con `uv`.
* [x] `pyproject.toml`.
* [x] Lockfile reproducible con `uv.lock`.
* [x] Entorno virtual gestionado mediante `uv`.

### Próximos pasos

* [ ] Añadir tests con `pytest`.
* [ ] Probar la API con `TestClient`.
* [ ] Crear una base de datos separada para testing.
* [ ] Añadir paginación más completa.
* [ ] Autenticación de usuarios.
* [ ] Hash seguro de contraseñas.
* [ ] Autorización y permisos.
* [ ] Mejorar manejo global de errores.
* [ ] Logging.
* [ ] Docker.
* [ ] Preparar configuración para producción.

---

## Filosofía del proyecto

Este proyecto intenta evitar utilizar herramientas como cajas negras.

La intención es comprender qué sucede en cada capa.

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

SQLAlchemy, Pydantic, FastAPI y `uv` simplifican distintas partes del desarrollo, pero la intención del proyecto es comprender qué problema resuelve cada herramienta y qué sucede detrás de cada operación.

---

## Licencia

Por definir.

---

## Nota

Este repositorio forma parte de un proyecto de aprendizaje y evoluciona progresivamente. Algunas decisiones arquitectónicas pueden cambiar a medida que se incorporen nuevos conceptos y necesidades.
