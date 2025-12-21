# Kavak Commercial Bot

Bot comercial de Kavak con integración WhatsApp, LangChain Agents, y sistema RAG con pgvector.

## Características

- **LangChain Agent**: Orquestación dinámica de interacciones usando LLM con herramientas
- **3 Capacidades principales:**
  1. Responder información básica sobre la propuesta de valor de Kavak (usando RAG)
  2. Brindar recomendaciones de autos del catálogo
  3. Otorgar planes de financiamiento (10% interés, plazos 3-6 años)

- **Gestión de memoria**: Contexto conversacional por número de teléfono usando LangChain Memory
- **RAG (Retrieval Augmented Generation)**: Búsqueda semántica con embeddings
- **Fuzzy matching**: Manejo de errores de tipeo en marcas/modelos
- **Integración WhatsApp**: Vía Twilio webhooks con procesamiento asíncrono
- **Autenticación**: AWS Cognito para proteger endpoints de la API
- **Procesamiento asíncrono**: Cola de mensajes en memoria con worker que procesa cada 2 segundos

## Arquitectura



## Requisitos

- Python 3.12+
- Docker y Docker Compose
- Cuenta de OpenAI (API key)
- Cuenta de Twilio (para WhatsApp)
- AWS Cognito (para autenticación)

## Instalación

1. Clonar el repositorio
2. Copiar `.env.example` a `.env` y configurar las variables:
   ```bash
   cp .env.example .env
   ```

3. Configurar variables de entorno en `.env`:
   - `DATABASE_URL`: URL de conexión a PostgreSQL (formato: `postgresql+asyncpg://user:password@host:port/dbname`)
   - `OPENAI_API_KEY`: Tu API key de OpenAI
   - `OPENAI_MODEL`: Modelo de OpenAI a usar (default: `gpt-5-mini`)
   - `OPENAI_EMBEDDING_MODEL`: Modelo de embeddings (default: `text-embedding-3-small`)
   - `TWILIO_ACCOUNT_SID`: Account SID de Twilio
   - `TWILIO_AUTH_TOKEN`: Auth Token de Twilio
   - `TWILIO_PHONE_NUMBER`: Número de WhatsApp de Twilio
   - `TWILIO_WEBHOOK_SECRET`: (Opcional) Secret para validar webhooks de Twilio
   - `COGNITO_TOKEN_ENDPOINT`: Endpoint de token de AWS Cognito (para autenticación)
   - `COGNITO_USER_POOL_ID`: ID del User Pool de AWS Cognito
   - `COGNITO_CLIENT_ID`: Client ID de la aplicación en Cognito
   - `COGNITO_CLIENT_SECRET`: Client Secret de la aplicación en Cognito
   - `COGNITO_SCOPE`: (Opcional) Scope para el token (default: `default-m2m-resource-server-lke1a1/read`)
   - `COGNITO_REGION`: (Opcional) Región de AWS para Cognito (default: `us-east-1`)
   - `KAVAK_URL`: (Opcional) URL para scraping de información de Kavak

4. Iniciar con Docker Compose:
   ```bash
   docker-compose up -d
   ```

   Esto iniciará:
   - PostgreSQL con pgvector
   - La aplicación FastAPI

5. Cargar el catálogo de autos:
   ```bash
   docker compose exec app python scripts/load_catalog.py
   ```

6. Scrapear y generar embeddings de la página de Kavak:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/embeddings/scrape" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico", "force_update": false}'
   ```

## Uso

### API Endpoints

La api está disponible localmente en

 http://localhost:8000/docs

o en linea

   https://106y3amtxj.execute-api.us-east-1.amazonaws.com/docs


#### Autenticación
- `POST /auth/login` - Obtener token de acceso usando client credentials (requiere `client_id` y `client_secret`)

#### Chat/WhatsApp
- `POST /api/v1/chat/message` - Procesar mensaje (requiere autenticación)
- `POST /api/v1/chat/webhooks/twilio` - Webhook de Twilio (sin autenticación, usa validación de firma)

#### Catálogo de Autos (requiere autenticación)
- `GET /api/v1/cars` - Listar autos (con filtros)
- `GET /api/v1/cars/{car_id}` - Obtener auto por ID
- `POST /api/v1/cars` - Crear auto
- `PUT /api/v1/cars/{car_id}` - Actualizar auto
- `DELETE /api/v1/cars/{car_id}` - Eliminar auto

#### Financiamiento (requiere autenticación)
- `POST /api/v1/financing/calculate` - Calcular planes

#### Embeddings (requiere autenticación)
- `POST /api/v1/embeddings/scrape` - Scrapear URL y generar embeddings
- `GET /api/v1/embeddings` - Listar embeddings
- `DELETE /api/v1/embeddings/{embedding_id}` - Eliminar embedding

Para darle contexto al bot se puede hacer mendiante el endpoint de `POST /api/v1/embeddings/scrape`
Puedes darle la siguiente url de Kavak para que el bot tenga contexto de la empresa
https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico

### Autenticación

La API utiliza AWS Cognito para autenticación mediante client credentials flow:

Disponible tambien mediante el endpoint de login en la API

1. Obtener token de acceso:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "tu-client-id",
       "client_secret": "tu-client-secret"
     }'
   ```

2. Usar el token en las peticiones:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/cars" \
     -H "Authorization: Bearer <token>"
   ```

**Nota**: El webhook de Twilio (`/api/v1/chat/webhooks/twilio`) no requiere autenticación, ya que utiliza validación de firma de Twilio.

### Configurar Twilio Webhook

1. En el dashboard de Twilio, configurar el webhook de WhatsApp:
   - URL: `https://tu-dominio.com/api/v1/chat/webhooks/twilio`
   - Método: POST

2. El bot procesará mensajes de forma asíncrona:
   - El webhook responde inmediatamente con 200 OK
   - Los mensajes se encolan para procesamiento
   - Un worker en segundo plano procesa los mensajes cada 2 segundos
   - Las respuestas se envían automáticamente vía Twilio API

## Estructura del Proyecto

```
src/
├── main.py                 # Aplicación FastAPI con lifespan
├── config.py               # Configuración y variables de entorno
├── database/               # Modelos y conexión DB
│   ├── connection.py       # Conexión async a PostgreSQL
│   └── models.py           # Modelos SQLAlchemy
├── schemas/                # Schemas Pydantic
│   ├── auth.py             # Schemas de autenticación
│   ├── car.py              # Schemas de autos
│   ├── chat.py             # Schemas de chat
│   ├── embedding.py        # Schemas de embeddings
│   └── financing.py        # Schemas de financiamiento
├── repositories/           # Acceso a datos
│   ├── car_repository.py   # Repositorio de autos
│   └── embedding_repository.py # Repositorio de embeddings
├── services/
│   ├── agent/              # Servicios del LangChain Agent
│   │   ├── chat_service.py     # LangChain Agent principal
│   │   ├── llm_service.py      # Cliente LangChain OpenAI
│   │   ├── langchain_tools.py  # Tools para el Agent
│   │   └── memory_manager.py   # Gestor de LangChain Memory
│   ├── auth_service.py     # Servicio de autenticación (Cognito)
│   ├── car_service.py      # Lógica de negocio de autos
│   ├── financing_service.py # Cálculo de financiamiento
│   ├── embedding_service.py # Servicio de embeddings y RAG
│   ├── scraping_service.py  # Scraping de URLs
│   ├── message_queue.py     # Cola de mensajes en memoria
│   ├── message_processor.py # Procesador de mensajes (worker)
│   └── twilio_service.py    # Servicio de envío de mensajes Twilio
├── dependencies/           # Dependencias de FastAPI
│   └── auth.py             # Dependency de autenticación JWT
├── middleware/             # Middlewares de FastAPI
│   ├── logging_middleware.py # Middleware de logging
│   └── auth_middleware.py   # (Deprecated) Middleware de auth
├── routers/                # Endpoints API
│   ├── auth.py             # Endpoints de autenticación
│   ├── cars.py             # Endpoints de autos
│   ├── chat.py             # Endpoints de chat/WhatsApp
│   ├── embeddings.py       # Endpoints de embeddings
│   └── financing.py        # Endpoints de financiamiento
└── utils/                  # Utilidades
    ├── csv_loader.py       # Carga de CSV
    └── text_processing.py  # Procesamiento de texto

scripts/
├── init_db.sql            # Inicialización DB
└── load_catalog.py        # Carga de catálogo
```

## LangChain Tools

El bot usa 4 herramientas para responder a los usuarios:

1. **SearchCarsTool**: Busca autos en el catálogo por marca, modelo, año, precio
2. **CalculateFinancingTool**: Calcula planes de financiamiento (10% interés, 3-6 años)
3. **SearchKnowledgeBaseTool**: Busca información sobre Kavak usando RAG
4. **GetCarDetailsTool**: Obtiene detalles de un auto específico

El Agent decide dinámicamente qué herramientas usar basándose en el mensaje del usuario.
El agente usa gpt5-mini y tools de langchain para responder a los usuarios.

## Desarrollo

### Instalar dependencias localmente

```bash
pip install uv
uv pip install -e .
```

### Ejecutar localmente

```bash
# Iniciar solo PostgreSQL
docker-compose up -d postgres

# Ejecutar aplicación
uv run uvicorn src.main:app --reload --reload-dir src
```

### Ejecutar tests

```bash
uv run pytest
```

## Documentación API

Una vez iniciada la aplicación, acceder a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Notas

- Las memorias se almacenan en memoria (temporalmente) usando LangChain Memory
- Para producción, considerar migrar a Redis para memorias compartidas
   - Actualmente solo corre una sola instancia para evitar problemas de memoria compartida
- Los embeddings se almacenan en PostgreSQL con pgvector
- Compatible con Amazon Aurora PostgreSQL + pgvector
