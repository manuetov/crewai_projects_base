---
name: crewai-workflow
description: Flujo del proyecto CoderAgents. Usar cuando se pregunte cómo funciona el pipeline, cuál es el flujo de ejecución, Architect vs EngineeringTeam, o AppBuilderFlow.
---

# Flujo CoderAgents (CrewAI)

## Resumen del pipeline

1. **ArchitectCrew** → Analiza requisitos y produce `CrewStrategy` (JSON: `module_name`, `class_name`, `agents_needed`, `rationale`)
2. **HITL** (Human-in-the-Loop) → El usuario aprueba o rechaza la estrategia por terminal (`s/n`)
3. **EngineeringTeam** → Construye la app solo si fue aprobada (diseño → código → frontend → tests → docs)

## Archivos clave

- `main.py` → `run()` llama a `AppBuilderFlow().kickoff()`
- `flow.py` → Define `AppBuilderFlow` con `@start` (run_architect) y `@listen` (request_approval, run_engineering_team)
- `crew.py` → `ArchitectCrew` (1 agente) y `EngineeringTeam` (5 agentes, filtrados por estrategia)

## Ejecución

```bash
crewai run
# o
python -m coder_agents.main
```

En modo Gradio (`app_gradio.py`), el HITL se omite: se llama `run_architect` y `run_engineering_team` directamente desde la UI.

## Salida

Los artefactos se generan en `generated-apps/{base_name}/` (subcarpeta por app):
- `{base_name}_design.md` (diseño)
- `{module_name}` (código Python)
- `app.py` (Gradio, si hubo frontend_engineer)
- `test_{module_name}` (tests)
- `INSTRUCTIONS.md` (docs)

El directorio `{app_dir}` se inyecta en los `inputs` del `kickoff` como `generated-apps/{base_name}`.

## Conceptos CrewAI (referencia)

- **Process.sequential**: Las tareas del EngineeringTeam se ejecutan en orden (diseño → código → frontend → tests → docs). Es el modo usado.
- **Process.hierarchical**: Alternativa con un "manager" que delega; no se usa en CoderAgents.
- **Flow**: `@start()` marca el punto de entrada; `@listen(metodo)` define pasos encadenados. `AppBuilderFlow` usa `@start` (run_architect) y `@listen` (request_approval → run_engineering_team).
- **HITL (Human-in-the-Loop)**: En CrewAI las tareas pueden tener `human_input=True` para pausar y pedir feedback. Aquí el HITL está en el Flow (`request_approval`), no en una Task.

## Recursos

- [Documentación CrewAI](https://docs.crewai.com/)
- [API Reference](https://docs.crewai.com/api-reference)
- [GitHub CrewAI](https://github.com/joaomdmoura/crewAI)
