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
**Razón:** Para no desperdiciar recursos de GPU, se utiliza una capa con **Numpy y Pillow** para realizar una deduplicación vectorial rápida y detección de desenfoque. Si una imagen es idéntica a una anterior o no contiene información útil, se descarta antes de entrar a la cola.




2. **Onboarding de Contexto (Admin Privado):**
* 
**Razón:** El administrador carga el **Plano del Local** e instrucciones específicas en un chat privado con el bot. Esto evita el ruido en el grupo de técnicos y proporciona a la IA una "fuente de verdad" espacial para mapear las fotos.




3. **Cerebro Multimodal (Gemma 4 31B en AMD Cloud):**
* 
**Razón:** Se utiliza el modelo **Gemma 4 31B Dense** por su capacidad nativa para razonar sobre imágenes y texto de forma simultánea. Su gran tamaño permite identificar equipos y ubicarlos en el plano con un margen de error mínimo, algo que los modelos de 7B no logran en entornos técnicos complejos.




4. **Human-in-the-Loop (Detección de Anomalías):**
* 
**Razón:** Para mitigar la falta de secuencialidad, si la IA detecta que un técnico envía una cámara después de procesar diez sensores de incendio, marca la imagen como **"sospechosa"**. El sistema consulta automáticamente al jefe de equipo mediante botones de opción rápida en Telegram para validar el cambio de etapa.





---

## 🧠 Prompt Maestro para Gemma 4 (31B Dense)

Este prompt se ejecuta durante el procesamiento por lotes (Batch) para cada imagen válida.

**Configuración del Sistema:**

> Actúa como un Ingeniero de Seguridad Electrónica Senior. Tu misión es transformar evidencia visual y mensajes de campo en datos estructurados para un informe de mantenimiento profesional.

**Inputs del Modelo:**

1. **[Imagen Actual]:** Foto técnica enviada por el operario.
2. **[Imagen Plano]:** Mapa del local cargado por el administrador.
3. **[Ventana de Chat]:** Lista de los últimos 5 mensajes de texto, incluyendo `nombre_usuario` y `rol` (Técnico, Asistente, Administrador).
4. **[Metadata de Contexto]:** Resumen textual de las últimas 5 categorías procesadas (ej: "Sistema de Alarma contra Incendios").

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
  "system_observation": "string",
  "is_suspicious": boolean,
  "anomaly_reason": "string"
}

```

---

## 🗄️ Modelo de Datos (SQLite para el MVP)

### 1. Tabla: `ProcessingQueue`

Gestiona el flujo de trabajo asíncrono para la instancia de AMD.

* `id`: INTEGER PRIMARY KEY
* `file_id`: TEXT (ID de Telegram para recuperar el archivo)
* `chat_id`: TEXT
* `status`: TEXT (PENDING, PROCESSING, COMPLETED, FAILED)
* `received_at`: DATETIME

### 2. Tabla: `ProcessedHistory`

Historial de mensajes para el refinamiento final del informe.

* `id`: INTEGER PRIMARY KEY
* `session_id`: TEXT
* `sender_name`: TEXT
* `sender_role`: TEXT (TECNICO, ASISTENTE, ADMIN)
* `message_text`: TEXT
* `timestamp`: DATETIME

### 3. Tabla: `StructuredInspectionData`

Salida final procesada para cada punto de inspección.

* `id`: INTEGER PRIMARY KEY
* `item_id`: TEXT
* `category`: TEXT
* `inspection_status`: TEXT (DURANTE / DESPUES)
* `location_on_map`: TEXT
* `ocr_data`: TEXT
* `tech_observation`: TEXT
* `ai_system_observation`: TEXT
* `is_suspicious`: BOOLEAN

---

## 🚀 Generación Final del Informe

Cuando el usuario solicita el cierre del proyecto, **Gemma 4** lee únicamente el contenido de la tabla `ProcessedHistory` (solo texto procesado). El modelo analiza la narrativa de toda la semana para redactar un resumen ejecutivo y conclusiones técnicas, consolidando las observaciones individuales en un reporte final coherente.