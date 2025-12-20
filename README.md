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
- **Integración WhatsApp**: Vía Twilio webhooks

## Arquitectura

```
Usuario → ChatService (LangChain Agent) → Tools:
                                         - SearchCarsTool
                                         - CalculateFinancingTool
                                         - SearchKnowledgeBaseTool
                                         - GetCarDetailsTool
                                         → LLM (OpenAI via LangChain)
                                         → Memory (por teléfono)
```

## Requisitos

- Python 3.12+
- Docker y Docker Compose
- Cuenta de OpenAI (API key)
- Cuenta de Twilio (para WhatsApp)

## Instalación

1. Clonar el repositorio
2. Copiar `.env.example` a `.env` y configurar las variables:
   ```bash
   cp .env.example .env
   ```

3. Configurar variables de entorno en `.env`:
   - `OPENAI_API_KEY`: Tu API key de OpenAI
   - `TWILIO_ACCOUNT_SID`: Account SID de Twilio
   - `TWILIO_AUTH_TOKEN`: Auth Token de Twilio
   - `TWILIO_PHONE_NUMBER`: Número de WhatsApp de Twilio
   - `TWILIO_WEBHOOK_SECRET`: (Opcional) Secret para validar webhooks

4. Iniciar con Docker Compose:
   ```bash
   docker-compose up -d
   ```

   Esto iniciará:
   - PostgreSQL con pgvector
   - La aplicación FastAPI

5. Cargar el catálogo de autos:
   ```bash
   docker-compose exec app python scripts/load_catalog.py
   ```

6. Scrapear y generar embeddings de la página de Kavak:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/embeddings/scrape" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico", "force_update": false}'
   ```

## Uso

### API Endpoints

#### Chat/WhatsApp
- `POST /api/v1/chat/message` - Procesar mensaje
- `POST /api/v1/chat/webhooks/twilio` - Webhook de Twilio
- `GET /api/v1/chat/sessions/{phone_number}` - Obtener sesión/memoria
- `DELETE /api/v1/chat/sessions/{phone_number}` - Limpiar sesión

#### Catálogo de Autos
- `GET /api/v1/cars` - Listar autos (con filtros)
- `GET /api/v1/cars/{car_id}` - Obtener auto por ID
- `POST /api/v1/cars` - Crear auto
- `PUT /api/v1/cars/{car_id}` - Actualizar auto
- `DELETE /api/v1/cars/{car_id}` - Eliminar auto
- `POST /api/v1/cars/bulk` - Carga masiva

#### Financiamiento
- `POST /api/v1/financing/calculate` - Calcular planes

#### Embeddings
- `POST /api/v1/embeddings/scrape` - Scrapear URL y generar embeddings
- `GET /api/v1/embeddings` - Listar embeddings
- `DELETE /api/v1/embeddings/{embedding_id}` - Eliminar embedding

### Configurar Twilio Webhook

1. En el dashboard de Twilio, configurar el webhook de WhatsApp:
   - URL: `https://tu-dominio.com/api/v1/chat/webhooks/twilio`
   - Método: POST

2. El bot responderá automáticamente a mensajes de WhatsApp

## Estructura del Proyecto

```
src/
├── main.py                 # Aplicación FastAPI
├── config.py               # Configuración
├── database/               # Modelos y conexión DB
├── schemas/                # Schemas Pydantic
├── repositories/           # Acceso a datos
├── services/
│   ├── chat_service.py     # LangChain Agent
│   ├── llm_service.py      # Cliente LangChain OpenAI
│   ├── langchain_tools.py  # Tools para el Agent
│   ├── car_service.py      # Lógica de autos
│   ├── financing_service.py # Cálculo de financiamiento
│   └── embedding_service.py # Servicio de embeddings
├── memory/
│   └── memory_manager.py   # Gestor de LangChain Memory
├── routers/                # Endpoints API
└── utils/                  # Utilidades

scripts/
├── init_db.sql            # Inicialización DB
└── load_catalog.py        # Carga de catálogo
```

## LangChain Tools

El bot usa 4 herramientas:

1. **SearchCarsTool**: Busca autos en el catálogo por marca, modelo, año, precio
2. **CalculateFinancingTool**: Calcula planes de financiamiento (10% interés, 3-6 años)
3. **SearchKnowledgeBaseTool**: Busca información sobre Kavak usando RAG
4. **GetCarDetailsTool**: Obtiene detalles de un auto específico

El Agent decide dinámicamente qué herramientas usar basándose en el mensaje del usuario.

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
uvicorn src.main:app --reload
```

## Documentación API

Una vez iniciada la aplicación, acceder a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Notas

- Las memorias se almacenan en memoria (temporalmente) usando LangChain Memory
- Para producción, considerar migrar a Redis para memorias compartidas
- Los embeddings se almacenan en PostgreSQL con pgvector
- Compatible con Amazon Aurora PostgreSQL + pgvector
