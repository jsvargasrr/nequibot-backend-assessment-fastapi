# NequiBot Chat Message API (Evaluación Técnica – Backend con FastAPI)

API RESTful simple para procesar mensajes de chat. Implementa validación, filtrado básico de palabras prohibidas, metadatos, persistencia en SQLite y endpoints de creación y consulta con paginación y filtrado por remitente.

> **Stack**: Python 3.10+, FastAPI, SQLAlchemy 2.x, SQLite, Pytest

---

## Cómo ejecutar

1) **Clonar** este repo (o descomprimir el ZIP de entrega).  
2) Crear y activar un **virtualenv**.  
3) Instalar dependencias:

```bash
pip install -r requirements.txt
```

4) Copiar variables de entorno base:

```bash
cp .env
```

5) Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

- Healthcheck: `GET http://localhost:8000/health`  
- API Docs: `http://localhost:8000/docs` y `http://localhost:8000/redoc`  
- Prefijo de API: `/api`

> La base de datos SQLite por defecto es `./app.db`. Se crea automáticamente al iniciar si no existe.

---

## Organización del código (Arquitectura limpia – separando capas)

```
app/
├─ api/                 # capa de transporte (controladores / routers / deps)
│  ├─ deps.py
│  └─ routes/
│     └─ messages.py
├─ domain/              # contratos de entrada/salida (Pydantic) y entidades ORM
│  ├─ entities.py       # SQLAlchemy (Message)
│  └─ schemas.py        # Pydantic (MessageIn, MessageOut, ErrorResponse, etc.)
├─ repositories/        # acceso a datos (SQLAlchemy + Session)
│  └─ message_repository.py
├─ services/            # lógica de negocio (pipeline de validación/procesamiento)
│  └─ message_service.py
├─ config.py            # configuración (pydantic-settings)
├─ db.py                # engine/Session/Base e inicialización
└─ main.py              # creación de FastAPI app, handlers de error, rutas
```

- **Controladores** (FastAPI routers) dependen de **servicios** vía inyección (`Depends`).
- **Servicios** dependen de **repositorios** (patrón repository) y **config** de procesamiento.
- **Repositorios** encapsulan SQLAlchemy.  
- **Domino** define **entidades** (SQLAlchemy) y **esquemas** (Pydantic).

---

## Pruebas

Ejecutar la suite con cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

- **Unitarias**: `tests/test_service.py` (pipeline de procesamiento).  
- **Integración**: `tests/test_messages_api.py` (endpoints con DB temporal).  
- La meta es ≥ **80%** de cobertura (ver `--cov-report`).

---

## Extras / bonus

- **API Key** simple: establece `NEQUI_API_KEY` y envía el header `X-API-Key` en cada request.  
- **Rate limiting** básico en memoria: establece `NEQUI_RATE_LIMIT_PER_MIN` (>0).  
  - Clave por `X-API-Key` o IP si no hay API key.
- **Docker**: imagen ligera para despliegue

```bash
docker build -t nequibot-api .
docker run -p 8000:8000 --env-file .env nequibot-api
```

---

## Documentación de la API

### Crear mensaje
`POST /api/messages`

**Body (JSON)**:
```json
{
  "message_id": "msg-123456",
  "session_id": "session-abcdef",
  "content": "Hola, ¿cómo puedo ayudarte hoy?",
  "timestamp": "2023-06-15T14:30:00Z",
  "sender": "system"
}
```

**200 – OK**
```json
{
  "status": "success",
  "data": {
    "message_id": "msg-123456",
    "session_id": "session-abcdef",
    "content": "Hola, **** puedo ayudarte hoy?",
    "timestamp": "2023-06-15T14:30:00Z",
    "sender": "system",
    "metadata": {
      "word_count": 6,
      "character_count": 32,
      "processed_at": "2023-06-15T14:30:01Z"
    }
  }
}
```

**400 – INVALID_FORMAT / VALIDATION_ERROR**  
**409 – DUPLICATE_MESSAGE_ID**  
**500 – SERVER_ERROR**

---

### Listar mensajes por sesión
`GET /api/messages/{session_id}`

**Query params**:
- `limit` (1..100, por defecto 50)  
- `offset` (>=0, por defecto 0)  
- `sender` (opcional: `user` o `system`)

**200 – OK**
```json
{
  "status": "success",
  "data": [
    {
      "message_id": "msg-123456",
      "session_id": "session-abcdef",
      "content": "Hola, **** puedo ayudarte hoy?",
      "timestamp": "2023-06-15T14:30:00Z",
      "sender": "system",
      "metadata": {
        "word_count": 6,
        "character_count": 32,
        "processed_at": "2023-06-15T14:30:01Z"
      }
    }
  ]
}
```

---

## Consideraciones de diseño

- **Validación** exhaustiva con Pydantic v2 (esquemas `MessageIn/Out`).  
- **Normalización** de `timestamp` → UTC si llega sin zona.  
- **Filtrado simple** de palabras prohibidas por **regex** (case-insensitive, límites de palabra).  
- **Metadatos** calculados: `word_count`, `character_count`, `processed_at`.  
- **Persistencia**: SQLite + SQLAlchemy 2.x (ORM moderno).  
- **Errores**: respuesta estándar `{status:"error", error:{code,message,details}}`.  
- **SOLID / Clean**: separación clara (controlador/servicio/repositorio) y DI con `Depends`.

---

## Variables de entorno

- `NEQUI_DATABASE_URL` – (default: `sqlite:///./app.db`)  
- `NEQUI_API_KEY` – habilita auth por header `X-API-Key` (si está vacío, no se exige).  
- `NEQUI_BANNED_WORDS` – lista separada por comas (`foo,bar,baz`).  
- `NEQUI_RATE_LIMIT_PER_MIN` – 0 deshabilita; número >0 habilita límite por minuto.  

---

## Notas de entrega

- Incluye este `README`, `requirements.txt`, pruebas bajo `tests/` y el código en `app/`.  
- Ejecuta `pytest --cov` para validar cobertura.  
- La documentación está disponible automáticamente en `/docs`.
