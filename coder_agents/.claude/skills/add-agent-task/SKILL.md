---
name: add-agent-task
description: Cómo añadir un nuevo agente o tarea al crew CoderAgents. Usar cuando el usuario quiera extender el equipo con un rol nuevo o una tarea adicional.
---

# Añadir agente o tarea

## Pasos para un nuevo agente en EngineeringTeam

1. **`models.py`** — Añadir el rol al enum `AgentRole`:
   ```python
   class AgentRole(str, Enum):
       ...
       NUEVO_ROL = "nuevo_rol"
   ```

2. **`config/agents_engineering.yaml`** — Definir el agente:
   ```yaml
   nuevo_rol:
     role: ...
     goal: ...
     backstory: ...
     llm: openai/gpt-4o
   ```

3. **`config/tasks_engineering.yaml`** — Definir la tarea:
   ```yaml
   nueva_task:
     description: ...
     expected_output: ...
     agent: nuevo_rol
     context: [code_task]  # si depende de otra tarea
     output_file: "{app_dir}/..."
   ```

4. **`crew.py`** — Actualizar los maps y métodos:
   - Añadir entrada en `_AGENT_METHOD_MAP` y `_TASK_METHOD_MAP`
   - Crear método `@agent def nuevo_rol(self) -> Agent`
   - Crear método `@task def nueva_task(self) -> Task`

5. **`agents.yaml` (architect)** — Si el architect debe poder elegir este agente:
   - Actualizar el `goal` del architect con la regla para `nuevo_rol`
   - Actualizar `strategy_task` en `tasks.yaml` para incluir `nuevo_rol` en `agents_needed`

## Si es solo para ArchitectCrew

Editar solo `config/agents.yaml` y `config/tasks.yaml`; no hace falta tocar `crew.py` del EngineeringTeam.

## Validación

- Verificar que `CrewStrategy.agents_needed` en `models.py` acepte el nuevo rol (Pydantic usa el enum).
- Probar con `crewai run` y un prompt que requiera el nuevo agente.

## Buenas prácticas al diseñar agentes/tareas

**Agentes**: Dar roles claros y específicos; backstory que aporte contexto; limitar herramientas a lo necesario; usar `allow_delegation=True` solo si el agente coordina a otros.

**Tareas**: Descripciones concretas y accionables; `expected_output` explícito; usar `context` para encadenar tareas (evitar dependencias circulares); tareas grandes mejor dividirlas.

**Crew**: 3–5 agentes suele ser óptimo; demasiados agentes complica la coordinación.
