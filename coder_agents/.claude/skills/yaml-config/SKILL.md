---
name: yaml-config
description: Convenciones de agents.yaml y tasks.yaml en CoderAgents. Usar al modificar o crear agentes, tareas o configuraciones YAML en el proyecto.
---

# Configuración YAML

## Dos conjuntos de configs

| Archivo | Uso |
|---------|-----|
| `config/agents.yaml` + `config/tasks.yaml` | **ArchitectCrew** (architect, strategy_task) |
| `config/agents_engineering.yaml` + `config/tasks_engineering.yaml` | **EngineeringTeam** (engineering_lead, backend, frontend, test, docs) |

## Estructura de agentes (agents.yaml / agents_engineering.yaml)

```yaml
nombre_agente:
  role: >      # Rol breve
  goal: >      # Objetivo (puede usar {requirements}, {module_name}, {class_name})
  backstory: > # Contexto de personalidad
  llm: openai/gpt-4o   # o anthropic/claude-*, deepseek/deepseek-chat
```

Placeholders en `goal`: `{requirements}`, `{module_name}`, `{class_name}` — se rellenan en `crew.kickoff(inputs=...)`.

## Estructura de tareas (tasks.yaml / tasks_engineering.yaml)

```yaml
nombre_task:
  description: >   # Qué hace la tarea
  expected_output: >
  agent: nombre_agente
  context: [otro_task]   # Dependencia de contexto
  output_file: "{app_dir}/{module_name}"   # app_dir inyectado en inputs
```

`output_file` puede usar `{app_dir}`, `{module_name}`, `{base_name}`. `{app_dir}` es la subcarpeta por app (ej. `generated-apps/accounts`). El formato `test_{module_name}` genera `test_accounts.py` cuando `module_name=accounts.py`.

## inputs del kickoff

```python
inputs = {
    "requirements": str,
    "module_name": "accounts.py",
    "base_name": "accounts",   # module_name sin .py
    "class_name": "Account",
    "app_dir": "generated-apps/accounts",   # subcarpeta por app (obligatorio para output_file)
}
```

`app_dir` se calcula como `generated-apps/{base_name}`. El flow y app_gradio lo inyectan en cada `kickoff`.

## Mapeo en crew.py

- `_AGENT_METHOD_MAP`: `AgentRole` → nombre del método `@agent`
- `_TASK_METHOD_MAP`: `AgentRole` → nombre del método `@task`
- Si añades un rol nuevo, actualiza `models.AgentRole`, los YAMLs y los maps en `crew.py`.

## Propiedades adicionales (CrewAI)

**Agentes** (algunas usadas en el proyecto):
- `allow_delegation`: ¿Puede delegar tareas a otros agentes?
- `verbose`: Log detallado
- `tools`: Herramientas (ej. McpFilesystemTool)
- `llm`: Modelo (openai/gpt-4o, anthropic/claude-*, deepseek/deepseek-chat)

**Tareas**:
- `output_pydantic`: Clase Pydantic para salida estructurada (ej. Architect usa `CrewStrategy`)
- `context`: Lista de tareas previas de las que depende
- `output_file`: Ruta donde guardar la salida

## Buenas prácticas (CrewAI)

✅ **Agentes**: Roles claros y específicos, backstory detallada, herramientas limitadas a lo necesario.
❌ **Evitar**: Roles vagos o solapados, demasiadas herramientas, goals ambiguos.

✅ **Tareas**: Descripciones concretas, `expected_output` definido, dependencias correctas con `context`.
❌ **Evitar**: Descripciones ambiguas, `context` circular, tareas demasiado complejas.
