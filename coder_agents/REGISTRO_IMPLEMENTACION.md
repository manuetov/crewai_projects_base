# Registro de Implementación — Fábrica de Apps (coder_agents)

> **Propósito:** Documento de control y aprendizaje. Detalla cada cambio realizado, explica *qué* se hizo, *por qué* y *para qué*, y sirve como bitácora del progreso.

---

## Índice

1. [Resumen del estado](#resumen-del-estado)
2. [Prioridad 1 — Output en carpeta externa](#prioridad-1--output-en-carpeta-externa)
3. [Prioridad 2 — Agente Arquitecto + CrewStrategy](#prioridad-2--agente-arquitecto--crewstrategy)
4. [Prioridad 3 — Gradio UI](#prioridad-3--gradio-ui-para-prompts)
5. [Prioridad 4 — CrewAI Flows con HITL](#prioridad-4--crewai-flows-con-hitl)
6. [Prioridad 5 — McpFilesystemTool](#prioridad-5--mcpfilesystemtool)
7. [Prioridad 8 — INSTRUCTIONS.md](#prioridad-8--instructionsmd)
8. [Problemas detectados en test](#problemas-detectados-en-test)
9. [Error Deepseek + LiteLLM](#error-deepseek--litellm-400-bad-request)
10. [Error schema mcp_filesystem](#error-schema-mcp_filesystem-additionalproperties-required)
11. [Error 404 modelo Claude](#error-404-modelo-claude-claude-3-7-sonnet-latest)
12. [Cambios recientes (feat/using-claude)](#cambios-recientes-featusing-claude)
13. [Glosario](#glosario)

---

## Resumen del estado

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| Config inicial | Copilot Instructions, MCP, Tools | ✅ Completado |
| 1 | Output en `generated-apps/` | ✅ Completado |
| 2 | Agente Arquitecto + CrewStrategy | ✅ Completado |
| 3 | Gradio UI para prompts | ✅ Completado |
| 4 | CrewAI Flows con HITL | ✅ Completado |
| 5 | MCP Filesystem (McpFilesystemTool) | ✅ Completado |
| 8 | INSTRUCTIONS.md (docs_engineer) | ✅ Completado |
| 7 | QA con Docker | Pendiente |
| — | Correcciones test (77e1e42) | ✅ Aplicadas (timeout, arguments opcional, pip gradio) |
| — | Error Deepseek (b8d3be4: quitar allow_code_execution de test_engineer) | ⚠️ Supersedido por ba617f8 (ver nota) |
| — | Restaurar allow_code_execution en test_engineer (ba617f8, para Claude) | ✅ Aplicado |
| — | Error schema mcp_filesystem (additionalProperties) | ✅ Corregido |
| — | Error 404 modelo Claude (→ claude-haiku-4-5) | ✅ Corregido |

---

## Prioridad 1 — Output en carpeta externa

**Objetivo:** Aislar el output de los agentes para que nunca modifiquen el código base de la Fábrica.

### Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `tasks.yaml` | Los 4 `output_file` apuntan a `generated-apps/` en lugar de `output/` |
| `main.py` | `makedirs('generated-apps')` — crea la carpeta en cada ejecución si no existe |
| `.gitignore` | `generated-apps/` añadido — las apps generadas no se versionan |
| — | Directorio `generated-apps/` creado en disco |

---

### Explicación detallada

#### ¿Qué se hizo?

Se cambió el destino de todos los archivos generados por los agentes (diseño, código backend, frontend, tests) de la carpeta `output/` a `generated-apps/`.

#### ¿Por qué?

- **Seguridad:** Si un agente intenta borrar o sobrescribir archivos, solo puede afectar lo que hay dentro de `generated-apps/`, nunca el código de la Fábrica.
- **Separación:** El código base (`crew.py`, `main.py`, `agents.yaml`, etc.) queda intacto. Las apps del usuario viven en una carpeta aparte.
- **Reutilización:** La base puede generar muchas apps distintas sin contaminarse.

#### ¿Para qué?

- Garantizar que la Fábrica sea una herramienta reutilizable y no un proyecto que se ensucia con cada ejecución.
- Preparar el terreno para Prioridad 5 (MCP Filesystem restringido a `generated-apps/`).
- Cumplir el criterio del `analisis.md`: *"La base genera apps en `./generated-apps/` sin modificar sus propios archivos"*.

---

### Conceptos para aprender

- **Output file en CrewAI:** En `tasks.yaml`, `output_file` define dónde se guarda el resultado de cada tarea. Los agentes escriben ahí en lugar de solo devolver texto.
- **`os.makedirs(..., exist_ok=True)`:** Crea el directorio si no existe; si ya existe, no falla.
- **`.gitignore`:** Evita que Git trackee la carpeta. Las apps generadas son productos efímeros; no forman parte del código fuente del proyecto.

---

## Prioridad 2 — Agente Arquitecto + CrewStrategy

**Objetivo:** Un agente que analice el prompt del usuario y decida qué agentes y flujo usar antes de construir.

### Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `models.py` | **Nuevo.** `AgentRole` (enum) + `CrewStrategy` (Pydantic): contrato de salida del Arquitecto |
| `agents.yaml` | Agente `architect` añadido. `test_engineer` ahora usa `deepseek/deepseek-chat` |
| `tasks.yaml` | `strategy_task` añadido al inicio (antes de `design_task`), con `output_pydantic` vía crew.py |
| `crew.py` | `ArchitectCrew` (clase simple) + `EngineeringTeam.set_strategy()` + `@crew` filtra agentes/tareas por `strategy.agents_needed` |
| `main.py` | Flujo en 2 fases: Arquitecto → estrategia → equipo filtrado. `module_name`/`class_name` ya no hardcodeados |

---

### Flujo de ejecución

```
crewai run
  └─ ArchitectCrew.run(USER_PROMPT)     → CrewStrategy (module_name, class_name, agents_needed)
       └─ EngineeringTeam
            .set_strategy(strategy)
            .crew()                      → Crew solo con agentes indicados
            .kickoff(inputs)              → archivos en generated-apps/
```

---

### Explicación detallada

#### ¿Qué se hizo?

1. **`models.py`:** Se definió el contrato de salida del Arquitecto con Pydantic: `module_name`, `class_name`, `agents_needed` (lista de roles), `rationale`. El enum `AgentRole` normaliza los nombres de agentes.

2. **Agente Arquitecto:** Un agente que analiza el prompt del usuario y devuelve un `CrewStrategy` estructurado. Usa `output_pydantic=CrewStrategy` para garantizar salida válida.

3. **Crew dinámica:** `EngineeringTeam.crew()` filtra agentes y tareas según `strategy.agents_needed`. Si hay estrategia, solo se activan esos agentes; si no, se usa el equipo completo (retrocompatibilidad).

4. **`main.py`:** Deja de tener `module_name` y `class_name` fijos. El Arquitecto los define a partir del prompt.

#### ¿Por qué?

- **Planificación antes de ejecución:** El Arquitecto actúa como Planificador (no Manager en tiempo real): decide qué lista secuencial ejecutar según el prompt.
- **Salidas estructuradas:** Pydantic obliga al LLM a devolver datos válidos, evitando JSON malformados.
- **Ejecución eficiente:** Si el usuario pide "solo API", se ejecutan [Backend, QA]; si pide "Fullstack", [Backend, Frontend, QA]. No se desperdician tokens en agentes innecesarios.

#### ¿Para qué?

- Cumplir el criterio del `analisis.md`: *"El Arquitecto determina dinámicamente qué agentes y flujo usar"*.
- Preparar el terreno para Prioridad 3 (Gradio): el `USER_PROMPT` llegará desde la UI.
- Base para Prioridad 4 (Flows): el `CrewStrategy` puede guardarse en `self.state` del Flow.

---

### Conceptos para aprender

- **`output_pydantic`:** Parámetro de CrewAI que fuerza a la tarea a devolver un objeto Pydantic. El LLM genera JSON compatible con el modelo.
- **`set_strategy()`:** Patrón de inyección de dependencias: la estrategia se pasa antes de construir la Crew, y `@crew` la usa para filtrar.
- **`_AGENT_METHOD_MAP` / `_TASK_METHOD_MAP`:** Mapean roles (enum) a los métodos decorados con `@agent` y `@task`. Permite selección dinámica sin hardcodear strings.
- **ArchitectCrew sin @CrewBase:** Es una Crew "manual" (un agente, una tarea). No necesita la estructura completa de `@CrewBase`; se instancia y se llama a `.run()`.

---

### Nota de revisión

- **`agents.yaml`:** El agente `architect` tiene dos entradas `llm:` (líneas 67-68). La segunda sobreescribe la primera; si se quiso usar `deepseek`, está bien. Si no, conviene dejar solo una.

---

## Prioridad 3 — Gradio UI para prompts

**Objetivo:** Interfaz para que el usuario introduzca el prompt en lugar de editarlo en `main.py`.

### Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `app_gradio.py` | **Nuevo.** UI Gradio: Textbox "Describe tu app", botón "Construir", log de construcción, lista de archivos generados con botón "Actualizar" |
| `main.py` | `run(requirements=None)` — acepta prompt como argumento; si es `None`, usa `_DEFAULT_PROMPT` |

---

### Cómo ejecutar

```bash
cd crewai-framework/coder_agents
.\.venv\Scripts\activate   # o: source .venv/bin/activate en Linux/Mac
python app_gradio.py
```

Con el venv activado, Gradio abre la interfaz en el navegador (`inbrowser=True`).

---

### Explicación detallada

#### ¿Qué se hizo?

1. **`app_gradio.py`:** Interfaz con título "Fábrica de Apps con CrewAI", Textbox para descripción, botón Construir, área de log y lista de archivos en `generated-apps/` con botón para actualizar.

2. **`run(requirements)`:** `main.run()` ahora acepta el prompt como parámetro. Si se llama sin argumentos (ej. `crewai run`), usa el prompt por defecto.

3. **Flujo:** Usuario escribe en el Textbox → clic en Construir → `run(prompt)` ejecuta el pipeline → los archivos aparecen en la lista.

#### ¿Por qué?

- **Usabilidad:** El usuario no necesita editar código para cambiar el prompt.
- **Feedback visual:** Muestra qué archivos se generaron y un log básico de la construcción.

#### ¿Para qué?

- Cumplir Prioridad 3 del `analisis.md`.
- Punto de entrada amigable para la Fábrica.

---

### Corrección aplicada: Import path

| Problema | `app_gradio.py` importaba vía `src.coder_agents.main`, pero `main.py` usa el paquete instalado `coder_agents`. Inconsistencia. |
| Solución | Usar `from coder_agents.main import run` con el **venv activado**. Con `uv sync` o `crewai install`, el paquete está instalado y el import resuelve correctamente. |
| Aprendizaje | En desarrollo con paquetes editable-install, hay dos contextos: (a) ruta de desarrollo `src.xxx` cuando el código no está instalado, (b) nombre del paquete `coder_agents` cuando está instalado en el venv. Ejecutar con venv activo garantiza que el import use el paquete instalado. |

---

## Glosario

| Término | Significado |
|---------|-------------|
| **CrewStrategy** | Modelo Pydantic que define qué agentes y proceso usar: `module_name`, `class_name`, `agents_needed`, `rationale`. |
| **AgentRole** | Enum que lista los roles disponibles: `engineering_lead`, `backend_engineer`, `frontend_engineer`, `test_engineer`, `docs_engineer`. |
| **output_file** | Parámetro en CrewAI que indica dónde guardar el resultado de una tarea. Variables como `{base_name}` (módulo sin `.py`) se sustituyen desde los `inputs`. |
| **output_pydantic** | Parámetro en CrewAI que fuerza la salida de una tarea a ser un objeto Pydantic válido. |
| **MCP** | Model Context Protocol — estándar para conectar agentes con datos y herramientas externas. |
| **McpFilesystemTool** | CustomTool CrewAI que conecta con el servidor MCP Filesystem, restringido a `generated-apps/`. Opera read_file, write_file, list_directory, create_directory. |
| **HITL** | Human-in-the-Loop — aprobación humana entre fases (ej. antes de construir). |
| **FlowState** | Clase base en CrewAI Flows para definir el estado persistente del flujo. Se accede con `self.state`. |
| **gr.State** | Componente Gradio que guarda datos entre eventos sin mostrarlos. Usado para pasar estrategia entre pasos HITL. |
| **Context Injection** | Inyectar instrucciones críticas en `backstory` o `description` del agente en lugar de RAG. |
| **Gradio** | Framework Python para crear interfaces web rápidas. Usado como UI de la Fábrica y como output de las apps generadas. |

---

## Prioridad 4 — CrewAI Flows con HITL

**Objetivo:** Orquestar el flujo con CrewAI Flows y añadir Human-in-the-Loop (aprobación humana) entre el Arquitecto y el Constructor.

### Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `flow.py` | **Nuevo.** `AppBuilderFlow` con `AppBuilderState`; `@start` run_architect; `@listen` request_approval (HITL terminal); `@listen` run_engineering_team |
| `main.py` | Delega totalmente a `AppBuilderFlow`; HITL por `input()` en terminal |
| `app_gradio.py` | Refactorizado a flujo HITL en 2 pasos: "Analizar" → tabla estrategia → "Aprobar y Construir" o "Cancelar"; usa `gr.State`; no usa Flow (evita bloquear servidor) |

---

### Arquitectura: dos modos de HITL

| Modo | HITL | Cómo |
|------|------|------|
| **CLI** (`crewai run`, `python main.py`) | Terminal | `AppBuilderFlow` → `input("¿Aprobar? [s/n]")` bloquea hasta respuesta |
| **Gradio UI** | Web | `app_gradio.py` llama a `ArchitectCrew` y `EngineeringTeam` directamente; HITL son botones "Aprobar y Construir" / "Cancelar" |

**Por qué Gradio no usa el Flow:** `input()` bloquearía el servidor web. La UI maneja el HITL con botones y `gr.State` para guardar la estrategia entre pasos.

---

### Flujo de ejecución

#### CLI
```
crewai run
  └─ AppBuilderFlow.kickoff()
       └─ run_architect (@start)        → CrewStrategy en state
       └─ request_approval (@listen)    → input() [s/n]
       └─ run_engineering_team (@listen) → construye si approved
```

#### Gradio UI
```
Usuario → "Analizar"  → ArchitectCrew().run() → tabla Markdown + gr.State
       → "Aprobar y Construir" → EngineeringTeam().set_strategy().crew().kickoff()
       → "Cancelar" → limpia state, sin construir
```

---

### Explicación detallada

#### ¿Qué se hizo?

1. **`flow.py`:** Flow con estado (`AppBuilderState`) que guarda `requirements`, `strategy`, `approved`. Tres métodos encadenados con `@start` y `@listen`. El HITL es `input()` en terminal.

2. **`main.py`:** Crea `AppBuilderFlow`, asigna `state.requirements`, llama `kickoff()`. Todo el flujo pasa por el Flow.

3. **`app_gradio.py`:** Botón "Analizar" ejecuta `ArchitectCrew().run()`, muestra la estrategia en Markdown, guarda en `gr.State`. Botones "Aprobar y Construir" y "Cancelar" controlan si se construye o no. La visibilidad de los botones se usa para obligar el orden: primero Analizar, luego decidir.

#### ¿Por qué?

- **HITL según `analisis.md`:** Revisar la estrategia antes de construir evita sorpresas y permite corregir sin ejecutar.
- **Flows como "columna vertebral":** El paso de `CrewStrategy` por `self.state` es nativo y claro (Iteración 3 del analisis.md).
- **Separación CLI vs UI:** El Flow es idóneo para CLI; Gradio necesita una implementación asíncrona basada en eventos.

#### ¿Para qué?

- Cumplir Prioridad 4 del `analisis.md`.
- Permitir aprobar o cancelar la construcción tras ver la estrategia.
- Dejar base para ampliar el Flow (ej. más fases, HITL intermedio).

---

### Corrección de bug: KeyError('architect')

| Problema | Al hacer clic en "Aprobar y Construir", fallaba con `Error durante la construcción: 'architect'`. |
| Causa | `CrewBase` resuelve agentes leyendo todo `tasks_config`. `strategy_task` tiene `agent: architect`, pero `EngineeringTeam` no define ese agente (solo lo usa `ArchitectCrew`). |
| Solución | Crear `agents_engineering.yaml` y `tasks_engineering.yaml` solo con agentes/tareas de ingeniería. `EngineeringTeam` usa esos archivos; `ArchitectCrew` sigue usando `agents.yaml` y `tasks.yaml`. |

---

### Mejoras post-P4 (commit 98ac67f)

| Mejora | Cambios |
|--------|---------|
| **1. Nombre del archivo de diseño** | `tasks_engineering.yaml`: `output_file` pasó de `{module_name}_design.md` a `{base_name}_design.md`. `flow.py` y `app_gradio.py`: los `inputs` ahora incluyen `base_name`: `strategy.module_name.removesuffix(".py")`. Resultado: `temperature_converter.py` → `base_name = "temperature_converter"` → archivo `temperature_converter_design.md` (en lugar de `temperature_converter.py_design.md`). |
| **2. Arquitecto incluye test_engineer por defecto** | `agents.yaml`: regla de `test_engineer` pasó de opt-in a opt-out. Incluye siempre; omite solo si el usuario indica explícitamente que no quiere pruebas o el módulo es trivialmente simple (≤ 2 funciones). `backstory` del architect: *"Valoras la calidad del software: un módulo sin tests no está terminado"*. |

---

### Conceptos para aprender

- **`@start()` / `@listen()`:** Decoradores de CrewAI Flows. `@start` marca el punto de entrada; `@listen(método)` ejecuta tras completar ese método.
- **`FlowState`:** Subclase que define el estado persistente del Flow. Se accede con `self.state`.
- **`gr.State`:** En Gradio, guarda datos entre eventos sin mostrarlos. Ideal para pasar la estrategia del paso "Analizar" al paso "Aprobar".
- **HITL en web vs terminal:** En terminal se puede usar `input()`; en web hay que usar botones o formularios que actúen como "aprobar/rechazar".

---

## Prioridad 5 — McpFilesystemTool

**Objetivo:** Conectar agentes CrewAI con el servidor MCP Filesystem, restringido a `generated-apps/`, para que lean/escriban archivos sin acceso al código base.

### Cambios realizados (commit 4c7ef92)

| Archivo | Cambio |
|---------|--------|
| `tools/mcp_tool.py` | **Nuevo.** `McpFilesystemTool` — puente CrewAI ↔ MCP @modelcontextprotocol/server-filesystem |
| `tools/__init__.py` | Exporta `McpFilesystemTool` |
| `crew.py` | `backend_engineer` y `test_engineer` reciben `tools=[McpFilesystemTool()]` |

---

### Operaciones soportadas

| Operación | Argumentos |
|-----------|------------|
| `read_file` | `{"path": "archivo.py"}` |
| `write_file` | `{"path": "archivo.py", "content": "..."}` |
| `list_directory` | `{"path": "."}` |
| `create_directory` | `{"path": "subdir/"}` |

Todas las rutas son relativas a `generated-apps/`.

---

### Seguridad (sandbox)

- **`_sandbox_path()`:** Resuelve rutas dentro de `GENERATED_APPS_DIR`. Si la ruta intenta escapar (ej. `../../src`), lanza `ValueError` y devuelve mensaje de acceso denegado.
- **MCP server:** Se lanza con `npx` y `generated-apps/` como raíz permitida (segunda capa de contención).

---

### Agentes con la herramienta

| Agente | McpFilesystemTool |
|--------|-------------------|
| engineering_lead | No (usa `output_file` en tasks) |
| backend_engineer | Sí |
| frontend_engineer | No |
| test_engineer | Sí |

### Estado actual (post-merge feat/using-claude)

**Nota:** En la versión actual de `crew.py` (tras merge con `develop`), los agentes **no reciben** `McpFilesystemTool`. La escritura de archivos se hace mediante `output_file` en las tareas (`tasks_engineering.yaml`), usando la variable `{app_dir}` inyectada en los `inputs` del `kickoff`. El archivo `tools/mcp_tool.py` sigue existiendo por si se quiere reintroducir la herramienta para operaciones adicionales (lectura de contexto, listado de archivos). Si se detectan fallos al generar apps, valorar restaurar `tools=[McpFilesystemTool()]` en `backend_engineer`, `test_engineer` y `docs_engineer` según la documentación de Prioridad 5.

---

### Conceptos para aprender

- **MCP stdio client:** El SDK `mcp` usa `stdio_client` para comunicarse con el servidor por stdin/stdout. `ClientSession` permite `call_tool()`.
- **Async en tool síncrona:** CrewAI espera `_run()` síncrono; el cliente MCP es async. Se usa `asyncio.run(self._call_mcp(...))` para envolver la llamada async.

---

### Corrección: ruta `_PROJECT_ROOT` (commit aace5dc)

| Problema | 4 niveles `".."` apuntaba a `crewai-framework/`; `generated-apps/` está en `coder_agents/`. |
| Solución | Cambiar a **3 niveles** en `mcp_tool.py`. `GENERATED_APPS_DIR` resuelve correctamente a `coder_agents/generated-apps`. |

---

## Prioridad 8 — INSTRUCTIONS.md (docs_engineer)

**Objetivo:** Generar un archivo `INSTRUCTIONS.md` en cada app construida para que Cursor/Copilot u otro agente sepa cómo trabajar con el proyecto (AI-ready).

### Cambios realizados (commit 226c126)

| Archivo | Cambio |
|---------|--------|
| `models.py` | Nuevo enum `AgentRole.DOCS_ENGINEER = "docs_engineer"` |
| `agents_engineering.yaml` | Nuevo agente `docs_engineer` con McpFilesystemTool; LLM openai/gpt-4o |
| `tasks_engineering.yaml` | Nueva tarea `docs_task` con 8 secciones obligatorias; context: code_task; output: generated-apps/INSTRUCTIONS.md |
| `crew.py` | docs_engineer en maps; `@crew` separa docs del resto y lo añade siempre al final |
| `agents.yaml` | Regla architect: "Incluye siempre docs_engineer al final de la lista" |

---

### Secciones del INSTRUCTIONS.md

1. **Propósito** — qué hace el proyecto y clase principal
2. **Stack tecnológico** — Python, librerías, Gradio si existe
3. **Estructura de archivos** — archivos en generated-apps/ y rol de cada uno
4. **Instalación** — dependencias
5. **Ejecución** — módulo y frontend
6. **Tests** — cómo correrlos
7. **Convenciones** — nomenclatura, estilo
8. **Notas para IA** — entry points, qué no modificar, cómo extender

---

### Orden de ejecución

`docs_engineer` se ejecuta siempre al final: el `@crew` filtra `DOCS_ENGINEER` del flujo principal y lo añade al final, independientemente de su posición en `agents_needed`.

---

### Resultado tras un build completo

En `generated-apps/`: `{module}.py`, `{base_name}_design.md`, `app.py` (si frontend), `test_{module}.py` (si tests) e **INSTRUCTIONS.md**.

---

## Problemas detectados en test

**Fecha:** Prueba con prompt 3 (to-do list completo: backend + Gradio + tests).

### 1. Timeout en code_task

| Campo | Valor |
|-------|-------|
| **Error** | `execution timed out after 240 seconds` |
| **Causa** | Apps complejas (to-do + Gradio + tests) pueden superar 240 s |
| **Solución** | Aumentar `max_execution_time` en `crew.py` para `backend_engineer` y `test_engineer` (ej. 480 o 600 s) |

### 2. McpFilesystemTool — argumento `arguments` faltante

| Campo | Valor |
|-------|-------|
| **Error** | `McpFilesystemTool._run() missing 1 required positional argument: 'arguments'` |
| **Causa** | El agente llama al tool con `{'tool_name': 'write_file'}` y no envía `arguments` |
| **Solución** | Hacer `arguments` opcional con default `{}` en `McpFilesystemInput` y en `_run` de `mcp_tool.py` |

### 3. Pip instalando paquetes erróneos

| Campo | Valor |
|-------|-------|
| **Observación** | El code_interpreter ejecutó algo como `pip install gradio` y terminó instalando `g`, `r`, `a`, `d`, `i`, `o` (letras sueltas) en lugar del paquete completo |
| **Solución** | Revisar instrucciones del agente o descripción de la tarea para que use `pip install gradio` completo |

### Resumen para Copilot/Claude

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `crew.py` | Aumentar `max_execution_time` en backend_engineer y test_engineer (ej. 480 o 600) |
| 2 | `tools/mcp_tool.py` | `arguments` opcional con default `{}` en schema y en `_run` |
| 3 | `agents_engineering.yaml` o `tasks_engineering.yaml` | Instrucción explícita para pip: "Si necesitas Gradio, ejecuta: pip install gradio" |

---

### Implementación (commit 77e1e42)

| Fix | Archivo | Cambio aplicado |
|-----|---------|-----------------|
| **1** | `tools/mcp_tool.py` | `arguments: dict[str, Any]` → `arguments: dict[str, Any] \| None = None` con `if arguments is None: arguments = {}`. El agente llamaba `write_file` sin pasar `arguments`; ahora el parámetro es opcional y hace fallback a `{}`. |
| **2** | `crew.py` | `max_execution_time` 240 → 600 s en `backend_engineer` y `test_engineer`. 4 minutos era insuficiente para módulos complejos; 10 minutos da margen para código + instalación de dependencias. |
| **3** | `tasks_engineering.yaml` + `agents_engineering.yaml` | **code_task:** instrucción de instalar con `subprocess.run(["pip", "install", "gradio"], check=True)` (lista explícita de argumentos). **backend_engineer backstory:** explicación de por qué usar lista y no string — evita que el agente separe `gradio` en letras (`g`, `r`, `a`, `d`, `i`, `o`) al iterar sobre el string. El error original `pip install g r a d i o` sucedía porque el code_interpreter iteraba carácter a carácter sobre una cadena; con lista de argumentos no se repite. |

---

## Error Deepseek + LiteLLM (400 Bad Request)

**Fecha:** Durante ejecución de `test_engineer`.

### Síntomas

```
litellm.BadRequestError: DeepseekException - {"error":{"message":"An object with no properties is not allowed.","type":"invalid_request_error","param":null,"code":"invalid_request_error"}}
URL: https://api.deepseek.com/beta/chat/completions
```

### Causa raíz (commit b8d3be4)

`allow_code_execution=True` en `test_engineer` hace que CrewAI inyecte **CodeInterpreterTool**. Ese componente realiza llamadas internas a `https://api.deepseek.com/beta/chat/completions` (endpoint `/beta/` distinto al estándar). La API de DeepSeek rechaza el schema del tool con *"An object with no properties is not allowed"*.

Esto ocurre aunque el YAML del agente use `openai/gpt-4o`: el subcomponente de code execution enruta a DeepSeek de forma independiente.

### Fix aplicado (commit b8d3be4)

| Archivo | Cambio |
|---------|--------|
| `crew.py` | Se **eliminan** de `test_engineer`: `allow_code_execution`, `code_execution_mode`, `max_execution_time`. Se mantienen `tools=[McpFilesystemTool()]` y `max_retry_limit=5`. |

**Motivo:** `test_engineer` solo debe **escribir** archivos de tests (via McpFilesystemTool), no ejecutar código. No necesita CodeInterpreterTool. `backend_engineer` sí mantiene `allow_code_execution=True` porque instala dependencias y valida el módulo en tiempo de ejecución.

### Cambios adicionales (anteriores)

| Archivo | Cambio |
|---------|--------|
| `agents_engineering.yaml` | `test_engineer`: `llm: deepseek/deepseek-chat` → `llm: openai/gpt-4o` (puede revertirse si se prefiere Deepseek para el LLM principal; el fix definitivo es quitar code execution) |
| `pyproject.toml` | `apscheduler>=3.10.0` añadido (evita `ModuleNotFoundError` durante logging de LiteLLM) |

---

*Última actualización:* Causa raíz documentada — CodeInterpreterTool + DeepSeek /beta/. Fix b8d3be4: quitar allow_code_execution de test_engineer.

### Restauración con Claude (commit ba617f8)

**Contexto:** El fix b8d3be4 quitaba `allow_code_execution` de `test_engineer` porque DeepSeek rechazaba el CodeInterpreterTool. En la rama `feat/using-claude`, al usar Claude como LLM, ese error no ocurre.

| Archivo | Cambio |
|---------|--------|
| `crew.py` | Se **restauran** en `test_engineer`: `allow_code_execution=True`, `code_execution_mode="unsafe"`, `max_execution_time=600`. |

**Motivo:** La tarea `test_task` en `tasks_engineering.yaml` incluye una **PARTE 2** que valida el código ejecutando: verificación de sintaxis con `py_compile`, ejecución de `pytest` o `unittest`, y reporte de resultados. Para hacerlo, el agente necesita `allow_code_execution=True`.

**Cuándo aplicar cada fix:**
- **DeepSeek como LLM:** Mantener b8d3be4 (sin `allow_code_execution` en `test_engineer`). El agente solo escribe tests, no los ejecuta.
- **Claude como LLM:** Usar ba617f8. El agente puede ejecutar los tests y reportar fallos.

---

## Error schema mcp_filesystem (additionalProperties required)

**Fecha:** Durante `test_task` (y también en UI al construir).

### Síntomas

```
Error code: 400 - Invalid schema for function 'mcp_filesystem': 
In context=('properties', 'arguments'), 'additionalProperties' is required to be supplied and to be false.
```

Además, el agente a veces llamaba con `Args: {'tool_name': 'write_file'}` sin `arguments`, provocando MCP error "expected string, received undefined" para path/content.

### Causa

El campo `arguments: dict[str, Any]` generaba un JSON Schema sin `additionalProperties: false`. La API OpenAI (y otras) exigen ese valor explícito para objetos anidados en tool schemas.

### Fix aplicado

| Archivo | Cambio |
|---------|--------|
| `tools/mcp_tool.py` | Nuevo modelo `McpArguments(BaseModel)` con `path: str`, `content: str \| None`, `model_config = {"extra": "forbid"}` — genera `additionalProperties: false`. `arguments` pasa a ser `McpArguments \| None` en vez de `dict[str, Any]`. `_run` convierte McpArguments a dict con `model_dump(exclude_none=True)`. |

---

## Error 404 modelo Claude (claude-3-7-sonnet-latest)

**Fecha:** Durante la construcción (backend_engineer, frontend_engineer).

### Síntomas

```
Error code: 404 - not_found_error - model: claude-3-7-sonnet-latest
```

### Causa

`claude-3-7-sonnet-latest` no es un ID válido en la API de Anthropic. Esta usa IDs con fecha (ej. `claude-3-7-sonnet-20250219`) o los modelos actuales (ej. `claude-sonnet-4-6`).

### Fix aplicado

| Archivo | Cambio |
|---------|--------|
| `agents_engineering.yaml` | `anthropic/claude-3-7-sonnet-latest` → `anthropic/claude-sonnet-4-6` (posteriormente → `anthropic/claude-haiku-4-5` por costo) |
| `agents.yaml` | Igual |

**Modelo actual:** `anthropic/claude-haiku-4-5` — más barato ($1 input / $5 output MTok vs Sonnet $3/$15). Alternativas: `claude-sonnet-4-5` (equilibrio coste/calidad), `claude-sonnet-4-6` (más capaz).

---

## Cambios recientes (feat/using-claude)

### Merge develop → feat/using-claude (b2f5540)

El merge con `origin/develop` introdujo cambios en `crew.py`. Resolución recomendada para conflictos en `max_execution_time` de `test_engineer`: mantener **600 s** (alineado con 77e1e42 y con la PARTE 2 de `test_task`, que ejecuta pytest).
