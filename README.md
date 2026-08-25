# FastAPI REST API

API REST construida desde cero con Python como proyecto de aprendizaje de desarrollo backend.

El objetivo principal de este proyecto no es solamente crear una API funcional, sino comprender cómo encaja cada pieza del backend: HTTP, validación de datos, acceso a base de datos, ORM, migraciones, relaciones entre tablas, manejo de errores y control de versiones.

> Este proyecto está en desarrollo y este README se actualizará a medida que se incorporen nuevas funcionalidades y conceptos.

---

## Objetivos de aprendizaje

Este proyecto busca aprender de forma práctica:

- Cómo funciona una API REST.
- Métodos HTTP: `GET`, `POST`, `PATCH` y `DELETE`.
- Códigos de estado HTTP como `200`, `201`, `204`, `404` y `409`.
- Path parameters, query parameters y request bodies.
- Validación de datos con Pydantic.
- Separación entre modelos de entrada, salida y persistencia.
- Persistencia de datos con PostgreSQL.
- Uso de SQL y conceptos relacionales.
- ORM con SQLAlchemy 2.x.
- Gestión de sesiones y transacciones.
- Migraciones de base de datos con Alembic.
- Relaciones `1:N` y claves foráneas.
- Manejo de errores de integridad.
- Arquitectura por capas.
- Control de versiones con Git y GitHub.

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
| Git | Control de versiones |
| GitHub | Repositorio remoto |

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
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── README.md
└── requirements.txt
```

> `.env` contiene configuración local sensible y no debe subirse al repositorio.

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

Características importantes:

- `id` es la clave primaria.
- `user_id` es una clave foránea hacia `users.id`.
- `user_id` tiene un índice para acelerar consultas por usuario.
- Una tarea no puede existir sin usuario.
- `is_completed` comienza en `false`.
- La relación utiliza `ON DELETE RESTRICT`.

Esto significa que PostgreSQL impide eliminar un usuario mientras tenga tareas asociadas.

---

## Endpoints actuales

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

El listado admite:

```text
GET /users?limit=10
```

con un límite validado entre `1` y `100`.

### Tasks

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `POST` | `/users/{user_id}/tasks` | Crear una tarea para un usuario |
| `GET` | `/users/{user_id}/tasks` | Obtener las tareas de un usuario |
| `GET` | `/tasks/{task_id}` | Obtener una tarea por ID |

El CRUD completo de `Task` todavía está en desarrollo.

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
```

Por ejemplo, intentar eliminar un usuario que todavía tiene tareas asociadas devuelve `409 Conflict`.

PostgreSQL bloquea primero la eliminación mediante la clave foránea y la aplicación convierte ese error en una respuesta HTTP comprensible.

---

## Requisitos

Antes de ejecutar el proyecto necesitas:

- Python 3.10 o superior.
- PostgreSQL instalado y ejecutándose.
- Git.
- Un entorno virtual de Python.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd fastapi-rest-api
```

### 2. Crear el entorno virtual

Windows:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
python3 -m venv .venv
```

### 3. Activar el entorno virtual

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

CMD:

```cmd
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

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

### Ver la versión actual

```bash
alembic current
```

### Ver el historial

```bash
alembic history
```

### Aplicar todas las migraciones pendientes

```bash
alembic upgrade head
```

### Crear una migración automáticamente

Después de modificar los modelos SQLAlchemy:

```bash
alembic revision --autogenerate -m "descripcion del cambio"
```

Siempre se debe revisar manualmente el archivo generado antes de ejecutar:

```bash
alembic upgrade head
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
uvicorn app.main:app --reload
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
```

```json
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
```

```json
{
  "is_active": false
}
```

Solo los campos enviados son modificados.

### Crear una tarea

```http
POST /users/1/tasks
Content-Type: application/json
```

```json
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

---

## Validación de datos

Pydantic se utiliza para validar los datos que entran y salen de la API.

Actualmente existen esquemas como:

```text
UserCreate
UserUpdate
UserResponse

TaskCreate
TaskResponse
```

Esta separación permite controlar qué campos puede enviar un cliente y qué campos puede devolver la aplicación.

Ejemplo conceptual:

```text
JSON
 |
 v
UserCreate
 |
 v
Service
 |
 v
SQLAlchemy User
 |
 v
PostgreSQL
```

En la respuesta:

```text
PostgreSQL
 |
 v
SQLAlchemy User
 |
 v
UserResponse
 |
 v
JSON
```

---

## Seguridad y buenas prácticas actuales

El proyecto ya aplica algunas buenas prácticas:

- Variables sensibles fuera del código mediante `.env`.
- `.env` ignorado por Git.
- Validación de request bodies con Pydantic.
- Restricciones también a nivel PostgreSQL.
- Emails únicos mediante una constraint `UNIQUE`.
- Foreign keys para garantizar integridad referencial.
- `rollback()` después de errores de transacción.
- Modelos de entrada y salida separados.
- Manejo de errores HTTP como `404` y `409`.
- Migraciones de base de datos versionadas.
- Separación entre routers y services.

Todavía faltan mecanismos importantes como autenticación, autorización y tests automatizados.

---

## Flujo de desarrollo

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

Las migraciones de Alembic también forman parte del código fuente y deben incluirse en Git.

Nunca se debe incluir `.env`.

---

## Estado actual

### Implementado

- [x] Proyecto Python y entorno virtual.
- [x] FastAPI.
- [x] Uvicorn.
- [x] Documentación OpenAPI / Swagger.
- [x] Validación con Pydantic.
- [x] PostgreSQL.
- [x] SQLAlchemy ORM.
- [x] Psycopg 3.
- [x] Configuración mediante `.env`.
- [x] CRUD de usuarios.
- [x] Manejo de errores `404` y `409`.
- [x] Alembic.
- [x] Migraciones.
- [x] Arquitectura con routers y services.
- [x] Relación `User 1:N Task`.
- [x] Foreign keys.
- [x] Creación y consulta de tareas.

### Próximos pasos

- [ ] Completar `PATCH /tasks/{task_id}`.
- [ ] Completar `DELETE /tasks/{task_id}`.
- [ ] Añadir tests con `pytest`.
- [ ] Probar la API con `TestClient`.
- [ ] Crear una base de datos separada para testing.
- [ ] Añadir paginación más completa.
- [ ] Autenticación de usuarios.
- [ ] Hash seguro de contraseñas.
- [ ] Autorización y permisos.
- [ ] Mejorar manejo global de errores.
- [ ] Logging.
- [ ] Docker.
- [ ] Preparar configuración para producción.

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

SQLAlchemy facilita trabajar con bases de datos desde Python, pero no elimina la necesidad de comprender SQL y el modelo relacional.

---

## Licencia

Por definir.

---

## Nota

Este repositorio forma parte de un proyecto de aprendizaje y evoluciona progresivamente. Algunas decisiones arquitectónicas pueden cambiar a medida que se incorporen nuevos conceptos y necesidades.
