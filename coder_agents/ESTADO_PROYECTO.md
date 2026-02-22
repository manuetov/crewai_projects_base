# Estado actual: Fábrica de Apps (coder_agents)

## ¿Qué es esto?

Una **Fábrica de Apps** que genera aplicaciones completas con CrewAI a partir de una descripción en texto:

- Módulo Python backend
- Diseño en Markdown
- Frontend Gradio (si se pide)
- Tests unitarios
- INSTRUCTIONS.md para que Cursor/Copilot sepa cómo trabajar con el proyecto

---

## Flujo actual (lo que hace hoy)

```
1. Usuario entra en la UI Gradio (app_gradio.py)
2. Escribe: "Quiero un conversor de temperaturas con tests"
3. Clic en "Analizar" → el Arquitecto define la estrategia (módulo, clase, agentes)
4. Revisa la estrategia (HITL) y decide:
   - "Aprobar y Construir" → construye la app
   - "Cancelar" → no hace nada
5. Si aprueba:
   - Engineering Lead diseña
   - Backend Engineer escribe código
   - Frontend Engineer (si aplica) crea la UI
   - Test Engineer (si aplica) genera tests
   - Docs Engineer genera INSTRUCTIONS.md
6. Todo se guarda en generated-apps/
```

---

## Qué está hecho

| # | Componente | Estado |
|---|------------|--------|
| Config | Copilot Instructions, MCP (filesystem, GitHub, Brave), tools | ✅ |
| 1 | Output en `generated-apps/` (separado de la base) | ✅ |
| 2 | Agente Arquitecto + CrewStrategy (elige agentes) | ✅ |
| 3 | Gradio UI para prompts | ✅ |
| 4 | CrewAI Flows + HITL (aprobación antes de construir) | ✅ |
| 5 | McpFilesystemTool (agentes leen/escriben en sandbox) | ✅ |
| 8 | docs_engineer → INSTRUCTIONS.md en cada app | ✅ |

---

## Qué falta

| # | Tarea | Descripción |
|---|-------|-------------|
| **7** | QA con Docker | Pasar `code_execution_mode` de `"unsafe"` a `"safe"` en backend_engineer y test_engineer. Requiere Docker instalado. |

---

## Cómo probar la app

```bash
cd crewai-framework/coder_agents
.\.venv\Scripts\activate
python app_gradio.py
```

En el navegador puedes describir una app, revisar la estrategia y construir. Los archivos se generan en `generated-apps/`.

---

## En resumen

Tienes una **Fábrica de Apps funcional** que genera apps completas con diseño, código, tests y documentación. Lo único pendiente es la **Prioridad 7** (ejecución en Docker para mayor seguridad).
