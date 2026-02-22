---
name: agent-roles
description: Referencia rápida de los agentes de CoderAgents. Usar al preguntar quién hace qué, qué agente usar, o cómo funciona cada rol.
---

# Roles de agentes

## Architect (solo en ArchitectCrew)

- **Rol**: Arquitecto de Software y Estratega de Proyectos
- **Entrada**: requisitos del usuario
- **Salida**: `CrewStrategy` (JSON con `module_name`, `class_name`, `agents_needed`, `rationale`)
- **Reglas**: Siempre incluye `engineering_lead`, `backend_engineer`; añade `frontend_engineer` si hay UI/Gradio; `test_engineer` por defecto; `docs_engineer` siempre al final

## EngineeringTeam (5 agentes)

| Agente | Responsabilidad | LLM |
|--------|-----------------|-----|
| **engineering_lead** | Diseño detallado del módulo (clases, métodos) → `*_design.md` | gpt-4o |
| **backend_engineer** | Código Python del módulo → `{module_name}` | claude-3-7-sonnet |
| **frontend_engineer** | UI Gradio en `app.py` que demuestra el backend | claude-3-7-sonnet |
| **test_engineer** | Pruebas unitarias → `test_{module_name}` | deepseek / gpt-4o |
| **docs_engineer** | `INSTRUCTIONS.md` para desarrolladores/IA | gpt-4o |

## Orden de ejecución

1. design_task (engineering_lead)
2. code_task (backend_engineer) — usa contexto de design_task
3. frontend_task (frontend_engineer) — opcional, usa contexto de code_task
4. test_task (test_engineer) — usa contexto de code_task
5. docs_task (docs_engineer) — al final, revisa todos los artefactos

## Herramientas especiales

- `backend_engineer` y `test_engineer` tienen `allow_code_execution=True` y `McpFilesystemTool()` para escribir archivos.
- `docs_engineer` usa `McpFilesystemTool()` para leer/generar INSTRUCTIONS.md.

## Propiedades clave de Agent (CrewAI)

Cada agente puede configurarse con: `role`, `goal`, `backstory`, `llm`, `verbose`, `allow_delegation`, `tools`, `max_iter`, `max_rpm`. En CoderAgents los YAMLs definen role/goal/backstory/llm; `crew.py` añade `verbose`, `tools` y `allow_code_execution` donde aplica.

## Ejecución de tests generados

Los tests van en `generated-apps/test_{module_name}`. Para ejecutarlos:
```bash
cd generated-apps
pytest test_{module_name} -v
# o todos
pytest -v
```
