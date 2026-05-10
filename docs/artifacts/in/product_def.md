# 🛠️ Documento de Ingeniería: Centinela Agent (MVP Telegram)

## 1. Introducción y Contexto del Sector (Caso de Uso Real)

El sector de instalación y mantenimiento de sistemas de seguridad electrónica (CCTV, alarmas) y protección contra incendios en Perú opera bajo un modelo de cumplimiento riguroso dictado por gigantes del retail como **Cencosud** y **Metro**. Estas corporaciones no pagan por el servicio realizado hasta que se presenta un reporte técnico formal que certifique, con evidencia visual, que cada dispositivo en el local está operativo.

### Contexto Específico del MVP:

Tras entrevistar a la asistente de un ingeniero en jefe, hemos identificado que el flujo de trabajo real no se basa en grupos temporales, sino en **grupos de WhatsApp persistentes por cada local físico**.

* 
**Persistencia del Canal:** Debido a que el cliente solicita mantenimientos periódicos (preventivos anuales, bianuales o correctivos puntuales), es más eficiente mantener un grupo activo por cada sede.


* 
**Gestión de Miembros:** El ingeniero jefe actúa como administrador y custodio del historial del chat. Él agrega o retira técnicos según la disponibilidad para cada proyecto específico, pero el grupo y su historial permanecen como un registro histórico del local.


* 
**Necesidad de Delimitación Lógica:** Dado que en un mismo chat de grupo pueden convivir datos de mantenimientos de hace dos años con los actuales, el bot no puede simplemente "leer todo". Es imperativo que el ingeniero jefe tenga comandos de control como `/iniciar_proyecto` y `/finalizar_proyecto`. Estos actúan como **delimitadores lógicos** que indican a la IA exactamente qué ventana de mensajes y fotos debe procesar para generar el informe actual, ignorando el historial previo irrelevante.



## 2. Definición de la Problemática Técnica y de Negocio

La ineficiencia administrativa actual genera un costo de oportunidad masivo para la empresa:

* 
**La "Deuda de Reportes" (12+ horas):** Actualmente, un asistente debe invertir más de 12 horas de trabajo manual por cada local para recolectar fotos de chats desordenados, emparejar evidencias y redactar observaciones. El objetivo técnico es reducir este tiempo de revisión humana a menos de 15 minutos mediante automatización con IA.


* 
**Gestión de la No-secuencialidad:** Aunque el mantenimiento se planea por secciones (ej. primero cámaras, luego incendios), la realidad del campo es errática. Si falta un repuesto, el técnico deja una revisión parcialmente completada, salta a otra área y reanuda la primera días después. Para un desarrollador, esto significa que el sistema debe ser capaz de **agrupar evidencias por equipo (Point of Inspection)** y no por orden cronológico de llegada, manteniendo el estado de cada ítem (pendiente, en proceso, completado) a lo largo de varias madrugadas.


* 
**La Brecha de Evidencia (Durante/Después):** El cliente exige pruebas de que el equipo fue realmente intervenido (foto del sensor abierto, "Durante") y que quedó funcionando (foto del equipo cerrado con LED operativo, "Después"). La IA debe clasificar visualmente estas etapas para evitar que el reporte se llene de fotos redundantes o mal etiquetadas.


* 
**Limitaciones de Hardware y Conectividad:** Los técnicos utilizan celulares de gama baja que pierden contexto en navegadores pesados y operan en zonas con nula señal (sótanos de centros comerciales). Esto justifica el uso de **Telegram** como capa de transporte, ya que maneja colas de mensajes offline de forma nativa y eficiente.


## 3. Propuesta de Solución: Agente de Ingeniería Multimodal

La solución es un **Bot de Telegram** que actúa como colector de datos, procesado de forma asíncrona en una infraestructura **AMD Instinct™ MI300X (192GB)**.

### Arquitectura y Racional Técnico para Desarrolladores:

1. **Ingesta y Pre-procesamiento Ligero (Tier 1 - CPU):**
* 
**Razón:** Para no desperdiciar recursos de GPU, los lotes de imágenes se procesan en CPU con un pipeline de cinco pasos antes de entrar a la cola. **Ninguna imagen se persiste en disco del servidor**: se descarga desde la API de Telegram a memoria, se mantiene viva mientras dure el procesamiento y se libera. Solo se persiste el `file_id` de Telegram (la propia CDN actúa como almacenamiento).
  1. **Descarga in-memory** del binario vía `getFile` de Telegram (bytes en `BytesIO`).
  2. **Compresión / normalización** con Pillow para estandarizar calidad (ej. recodificar a JPEG ~75 de calidad y redimensionar el lado mayor a ~1280 px). El pre-procesamiento y la identificación por parte de Gemma no requieren calidad máxima; esto reduce el costo de embedding, el payload hacia vLLM y la latencia general.
  3. **Embedding ligero** por imagen (ej. CLIP pequeño, MobileNet o `imagehash` perceptual) sobre la versión comprimida.
  4. **Clustering por similitud vectorial** (umbral de distancia coseno / `DBSCAN`) para agrupar fotos casi-duplicadas del mismo equipo o ángulo, y **score de nitidez** por imagen mediante varianza del Laplaciano (OpenCV/Pillow).
  5. **Colapso del cluster** conservando como representante la imagen con mayor nitidez (desempate por mayor resolución).
  Solo el representante de cada cluster entra a `ProcessingQueue`. Los miembros descartados se referencian por `file_id` con su `cluster_id` y `is_representative=false` para trazabilidad/auditoría, sin almacenar el binario. Si un cluster (incluso de una sola imagen) no supera el umbral mínimo absoluto de nitidez, se marca como **evidencia insuficiente** y dispara un Human-in-the-Loop pidiendo al técnico repetir la foto.




2. **Onboarding de Contexto (Admin Privado):**
* 
**Razón:** El administrador carga el **Plano del Local** e instrucciones específicas en un chat privado con el bot. Esto evita el ruido en el grupo de técnicos y proporciona a la IA una "fuente de verdad" espacial para mapear las fotos.




3. **Cerebro Multimodal (Gemma 4 31B en AMD Cloud):**
* 
**Razón:** Se utiliza el modelo **`google/gemma-4-31B-it`** (Image-Text-to-Text, 33B parámetros, instruction-tuned) por su capacidad nativa para razonar sobre imágenes y texto de forma simultánea. Su gran tamaño permite identificar equipos y ubicarlos en el plano con un margen de error mínimo, algo que los modelos de 7B no logran en entornos técnicos complejos.




4. **Human-in-the-Loop (Detección de Anomalías):**
* 
**Razón:** Para mitigar la falta de secuencialidad, si la IA detecta que un técnico envía una cámara después de procesar diez sensores de incendio, marca la imagen como **"sospechosa"**. El sistema consulta automáticamente al jefe de equipo mediante botones de opción rápida en Telegram para validar el cambio de etapa.





---

## 🧠 Prompt Maestro para Gemma 4 (`google/gemma-4-31B-it`)

Este prompt se ejecuta durante el procesamiento por lotes (Batch) para cada imagen válida.

**Configuración del Sistema:**

> Actúa como un Ingeniero de Seguridad Electrónica Senior. Tu misión es transformar evidencia visual y mensajes de campo en datos estructurados para un informe de mantenimiento profesional.

**Inputs del Modelo:**

1. **[Imagen Actual]:** Foto técnica enviada por el operario (representante del cluster tras el pre-procesamiento).
2. **[Imagen Plano]:** Mapa del local cargado por el administrador, usado solo como referencia secundaria de ubicación.
3. **[Ventana de Chat]:** Mensajes de texto del grupo desde la última imagen procesada del **mismo técnico**, con tope de **5 mensajes o 30 minutos** (lo que ocurra primero). Las imágenes no cuentan como mensaje. Cada mensaje incluye `nombre_usuario` y `rol` (Técnico, Asistente, Administrador).
4. **[Metadata de Contexto]:** Resumen textual derivado de los **JSON de salida** de las últimas N inspecciones procesadas en el mismo proyecto (Gemma **no** vuelve a consumir imágenes previas, solo sus salidas estructuradas). Esto implica que los grupos de imágenes se procesan de forma **secuencial temporal** en la cola para preservar el contexto narrativo.

**Instrucciones de Razonamiento:**

1. **Clasificación y Estado:** Identifica el equipo y determina si la foto es "Durante" (abierto/intervenido) o "Después" (operativo).
2. **Extracción de Texto (OCR):** Extrae IDs, marcas o números de serie. Si el texto es borroso, descríbelo lo mejor posible en el campo `ocr`.
3. **Análisis Espacial:** Ubica el equipo en el **Plano** usando las referencias visuales de la foto y los mensajes del chat.
4. **Detección de Anomalías:** Si la categoría de la imagen rompe el patrón de la **Metadata de Contexto**, marca `is_suspicious: true` y detalla la razón.
5. **Generación de Observaciones:**
* `observation`: Solo si hay un comentario explícito de un humano en el chat relacionado con esta imagen.
* `system_observation`: Si detectas una falla visual evidente (ej: cables sueltos, corrosión) que el humano no mencionó, o si el texto en la foto está borroso.



**Salida Estructurada (JSON):**

```json
{
  "category": "string",
  "status": "DURANTE | DESPUES",
  "location_ref": "string",
  "ocr": "string",
  "observation": "string",
  "system_observation": "string (also used for anomaly reason when is_suspicious=true)",
  "is_suspicious": boolean
}

```

---

## 🗄️ Modelo de Datos (SQLite para el MVP)

> Convención: `project_id` es la clave de negocio principal en todo el sistema. Reemplaza al antiguo `session_id` y se propaga a todas las tablas.

### 1. Tabla: `Project`

Entidad raíz creada al ejecutar `/iniciar_proyecto` y cerrada con `/finalizar_proyecto`.

* `project_id`: TEXT PRIMARY KEY
* `chat_id`: TEXT (grupo de Telegram del local)
* `local_name`: TEXT
* `floor_plan_file_id`: TEXT (referencia al plano cargado por el admin en chat privado)
* `admin_user_id`: TEXT
* `status`: TEXT (ACTIVE, CLOSED, AUTO_CLOSED)
* `started_at`: DATETIME
* `finished_at`: DATETIME
* `closure_reason`: TEXT (manual / timeout)

### 2. Tabla: `User`

Catálogo de miembros conocidos del chat (evita repetir `sender_role` como texto en cada mensaje).

* `telegram_user_id`: TEXT PRIMARY KEY
* `display_name`: TEXT
* `role`: TEXT (TECNICO, ASISTENTE, ADMIN)

### 3. Tabla: `ProcessingQueue`

Gestiona el flujo de trabajo asíncrono para la instancia de AMD.

* `id`: INTEGER PRIMARY KEY
* `project_id`: TEXT (FK → Project)
* `file_id`: TEXT (ID de Telegram para recuperar el archivo)
* `chat_id`: TEXT
* `cluster_id`: TEXT (agrupamiento del pre-procesamiento)
* `is_representative`: BOOLEAN (true = entra a inferencia; false = archivada por trazabilidad)
* `sharpness_score`: REAL
* `status`: TEXT (PENDING, PROCESSING, COMPLETED, FAILED, INSUFFICIENT_EVIDENCE)
* `attempts`: INTEGER
* `last_error`: TEXT
* `worker_id`: TEXT
* `received_at`: DATETIME
* `processed_at`: DATETIME
* UNIQUE(`project_id`, `file_id`) — idempotencia ante reentregas de Telegram.

### 4. Tabla: `ProcessedHistory`

Historial de mensajes de texto para el refinamiento final del informe.

* `id`: INTEGER PRIMARY KEY
* `project_id`: TEXT (FK → Project)
* `telegram_user_id`: TEXT (FK → User)
* `message_text`: TEXT
* `timestamp`: DATETIME

### 5. Tabla: `StructuredInspectionData`

Salida final procesada para cada punto de inspección.

* `id`: INTEGER PRIMARY KEY
* `project_id`: TEXT (FK → Project)
* `queue_id`: INTEGER (FK → ProcessingQueue)
* `image_file_id`: TEXT
* `item_id`: TEXT
* `category`: TEXT
* `inspection_status`: TEXT (DURANTE / DESPUES)
* `location_on_map`: TEXT
* `ocr_data`: TEXT
* `tech_observation`: TEXT
* `ai_system_observation`: TEXT
* `is_suspicious`: BOOLEAN
* `validated_by_admin`: BOOLEAN
* `created_at`: DATETIME

### 6. Tabla: `HumanReview`

Persistencia de las consultas Human-in-the-Loop disparadas por anomalías o evidencia insuficiente.

* `id`: INTEGER PRIMARY KEY
* `project_id`: TEXT (FK → Project)
* `queue_id`: INTEGER (FK → ProcessingQueue, nullable)
* `trigger`: TEXT (SUSPICIOUS_CATEGORY, INSUFFICIENT_EVIDENCE, INVALID_JSON, etc.)
* `question`: TEXT
* `answer`: TEXT
* `reviewer_user_id`: TEXT (FK → User)
* `asked_at`: DATETIME
* `answered_at`: DATETIME

### 7. Tabla: `AdminWhitelist`

Lista de usuarios autorizados como administradores del bot. Solo los usuarios en esta tabla pueden: ejecutar `/iniciar` (exclusivamente en chats grupales), interactuar con el bot en chats privados (1-a-1), y ejecutar `/finalizar`. El registro inicial se realiza mediante la variable de entorno `ADMIN_TELEGRAM_USER_IDS` (lista separada por comas). Se persiste en SQLite para permitir futuros comandos de gestión de admins sin reiniciar el bot.

* `telegram_user_id`: TEXT PRIMARY KEY
* `added_at`: DATETIME

### 8. Tabla: `Assistants`

Lista de asistentes autorizados para revisar alertas de proyectos creados por sus admins asociados. Un asistente puede estar vinculado a uno o más administradores. El registro inicial se realiza mediante la variable de entorno `ASSISTANT_TELEGRAM_USER_IDS` (formato: `assistant_id:admin_id,assistant_id:admin_id`). Se persiste en SQLite para gestión dinámica.

* `telegram_user_id`: TEXT PRIMARY KEY
* `admin_user_id`: TEXT NOT NULL
* `added_at`: DATETIME

**Reglas de acceso:**

* `/iniciar` solo se permite en chats grupales y solo por un admin registrado.
* `/finalizar` solo por un admin registrado.
* `/plano` solo por un admin registrado.
* `/alertas` permitido para admins y asistentes. Un asistente solo puede ver alertas de proyectos creados por su admin asociado.
* Mensajes en chat privado (1-a-1) son ignorados si el remitente no es admin.
* Cuando un admin ejecuta `/iniciar <nombre>` en un grupo, el bot le envía un mensaje privado solicitando información complementaria del proyecto (plano del local, instrucciones especiales).
* Las alertas de categoría sospechosa **no se envían automáticamente al grupo**. En su lugar, un admin o asistente puede ejecutar `/alertas` para ver las últimas 5 alertas pendientes con fotos y botones de confirmación/rechazo.

---

## 🛡️ Manejo de Errores y Resiliencia

* **Errores transitorios (descarga desde CDN de Telegram, timeout de red, 5xx del backend de inferencia):** reintento con backoff exponencial; tras N intentos fallidos el item pasa a `status=FAILED`.
* **JSON inválido o no conforme al schema:** dado que `guided_json` de vLLM no se aplica en modelos multimodales (vision+text), el esquema se inyecta directamente en el prompt del usuario con instrucciones estrictas de campo. Un paso de normalización (`_normalize_response`) mapea alias comunes que el modelo puede usar (ej: `equipment_type` → `category`, `location` → `location_ref`, `ocr.text_detected` → `ocr`). Si la validación Pydantic falla tras normalización, el item se marca como `PARSE_ERROR` con `is_suspicious=True`.
* **Idempotencia:** `UNIQUE(project_id, file_id)` evita procesar dos veces el mismo update reentregado por Telegram.
* **Imágenes descartadas:** los miembros no representantes del cluster se conservan **solo como referencia** (`file_id` + `is_representative=false`); el binario nunca se persiste en el servidor.
* **Cierre por timeout:** si el admin no ejecuta `/finalizar_proyecto` tras un periodo configurable de inactividad, el proyecto pasa a `AUTO_CLOSED` y se genera el informe con lo disponible, marcando esta condición en `closure_reason`.

## 🔐 Privacidad y Retención

Los planos de locales (Cencosud, Metro) y las fotos de instalaciones de seguridad son información sensible del cliente. El MVP contempla:

* **Cero persistencia de imágenes en el servidor**: las fotos viven solo en memoria durante el procesamiento y luego en la CDN de Telegram (referenciadas por `file_id`).
* Cifrado en reposo del SQLite (que solo contiene metadatos, IDs y JSON estructurados, nunca binarios).
* Acceso restringido al chat privado del admin para la carga del plano.

## 🧰 Stack Técnico y Entorno de Desarrollo

* **Python**: 3.13.0 gestionado con **pyenv** + **venv** para pruebas locales.
* **Dependencias**: declaradas en `requirements.txt` (sin `pyproject.toml` para el MVP). Pinneado por versión exacta.
* **Inferencia LLM**: vLLM (ya instalado en la instancia AMD) sirviendo **`google/gemma-4-31B-it`** vía API OpenAI-compatible.
* **Cliente LLM**: `openai` (AsyncOpenAI) apuntando al endpoint vLLM, sin `guided_json` para modelos multimodales.
* **Internacionalización (i18n)**: todos los prompts del LLM y strings de la UI del bot están modularizados en `src/app/domain/prompts/` con un archivo por locale (`es.py`, `en.py`). El locale activo se configura con la variable de entorno `BOT_LOCALE` (`es` o `en`).
* **Telegram**: librería `python-telegram-bot` (async).
* **Procesamiento de imagen**: Pillow + OpenCV (varianza del Laplaciano) + un backend ligero de embeddings (CLIP pequeño, MobileNet o `imagehash`).
* **Persistencia**: SQLite vía `sqlite3` o un thin wrapper (sin ORM pesado para el MVP).
* **Configuración**: todas las claves, hosts, umbrales y parámetros se cargan desde `.env` (vía `python-dotenv`) y se exponen mediante un módulo `config.py` en la raíz del proyecto. **No hay valores por defecto** en firmas de funciones/clases; los parámetros se inyectan explícitamente desde `config.py`.

## 📊 Métrica de Éxito

El objetivo de "<15 minutos de revisión humana" debe ser medible. Se registra por proyecto:

* `report_generation_duration` (desde `/finalizar_proyecto` hasta informe entregado).
* Número de items que requirieron `HumanReview`.
* Número de imágenes ingresadas vs. procesadas tras el clustering (ratio de compresión del lote).

---

## 🚀 Generación Final del Informe

Cuando el usuario solicita el cierre del proyecto, **`google/gemma-4-31B-it`** lee únicamente el contenido de la tabla `ProcessedHistory` (solo texto procesado). El modelo analiza la narrativa de toda la semana para redactar un resumen ejecutivo y conclusiones técnicas, consolidando las observaciones individuales en un reporte final coherente.