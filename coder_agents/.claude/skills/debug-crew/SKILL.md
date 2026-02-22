---
name: debug-crew
description: Troubleshooting de crewai run y CoderAgents. Usar cuando falle la ejecución, haya errores de configuración, dependencias o API keys.
---

# Troubleshooting CoderAgents

## Pre-requisitos

- **Python**: 3.10–3.13 (compatible con CrewAI)
- **UV**: `pip install uv` — gestión de dependencias
- **`.env`**: Debe contener `OPENAI_API_KEY` (y otras keys si usas Anthropic, DeepSeek)

## Comandos habituales

```bash
crewai install    # Lock e instalar dependencias
crewai run       # Ejecutar el flujo completo
python -m coder_agents.main   # Alternativa
```

## Errores frecuentes

| Error | Solución |
|-------|----------|
| `OPENAI_API_KEY` no definida | Añadir a `.env` en la raíz del proyecto |
| `ModuleNotFoundError: coder_agents` | Ejecutar desde la raíz donde está `pyproject.toml`; o `uv run python -m coder_agents.main` |
| `KeyError` en agents/tasks | Verificar que el nombre en YAML coincida con el usado en `crew.py` (agents_config, tasks_config) |
| `CrewStrategy` validation error | El architect devolvió JSON inválido; revisar que `agents_needed` use valores del enum (`AgentRole`) |
| MCP / McpFilesystemTool error | Comprobar que el servidor MCP de filesystem esté disponible si se usa |

## Estructura esperada

```
coder_agents/
├── .env                    # OPENAI_API_KEY
├── pyproject.toml
├── src/coder_agents/
│   ├── main.py
│   ├── flow.py
│   ├── crew.py
│   ├── models.py
│   └── config/
│       ├── agents.yaml
│       ├── tasks.yaml
│       ├── agents_engineering.yaml
│       └── tasks_engineering.yaml
└── generated-apps/         # Salida (se crea al ejecutar)
```

## Si la app generada falla

- Revisar `generated-apps/INSTRUCTIONS.md` para instrucciones de instalación y ejecución.
- Las apps Gradio pueden requerir `pip install gradio`; el backend_engineer tiene instrucciones para instalarlo vía subprocess si es necesario.

## Comandos CLI CrewAI

```bash
crewai create crew <nombre>   # Crear proyecto nuevo
crewai create flow <nombre>   # Crear flow nuevo
crewai install               # Lock e instalar dependencias
crewai run                   # Ejecutar (CoderAgents)
crewai train                 # Entrenar crew (si aplica)
crewai test                  # Ejecutar tests del proyecto
crewai replay <task_id>      # Re-ejecutar tarea
```

## Variables de entorno

```bash
OPENAI_API_KEY=...          # Requerida para gpt-4o
ANTHROPIC_API_KEY=...       # Si usas claude-*
# Serper, LangSmith, etc. según herramientas usadas
```

## Recursos externos

- [docs.crewai.com](https://docs.crewai.com/)
- [GitHub CrewAI](https://github.com/joaomdmoura/crewAI)
