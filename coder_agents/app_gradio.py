#!/usr/bin/env python
"""
Gradio UI — Fábrica de Apps con CrewAI
Implementa el HITL en la interfaz:
  Paso 1 ("Analizar")    → ArchitectCrew → muestra CrewStrategy para revisión
  Paso 2 ("Aprobar y Construir" o "Cancelar") → lanza la EngineeringTeam o aborta
"""
import os
import gradio as gr

from coder_agents.crew import ArchitectCrew, EngineeringTeam
from coder_agents.models import CrewStrategy

# ---------------------------------------------------------------------------
EXAMPLE_PROMPT = """\
Un sistema de gestión de tareas (to-do list) con:
- Crear, completar y eliminar tareas
- Categorías y prioridades
- Informe de resumen
Necesita interfaz Gradio y pruebas unitarias.
"""

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated-apps")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def list_generated_files() -> str:
    files = sorted(os.listdir(OUTPUT_DIR)) if os.path.isdir(OUTPUT_DIR) else []
    return "\n".join(f"- `{f}`" for f in files) if files else "_Sin archivos generados aún._"


def _strategy_markdown(s: CrewStrategy) -> str:
    agents = ", ".join(f"`{r.value}`" for r in s.agents_needed)
    return (
        f"### Estrategia propuesta por el Arquitecto\n"
        f"| Campo | Valor |\n"
        f"|---|---|\n"
        f"| Módulo | `{s.module_name}` |\n"
        f"| Clase | `{s.class_name}` |\n"
        f"| Agentes | {agents} |\n\n"
        f"**Justificación:** {s.rationale}"
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def analyze(prompt: str, _state: dict):
    """
    Fase 1 (HITL Paso 1): ejecuta el Arquitecto y devuelve la estrategia
    para que el usuario la revise antes de aprobar la construcción.
    """
    if not prompt or not prompt.strip():
        yield (
            "⚠️ Por favor, describe tu app antes de analizar.",
            _state,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            "",
        )
        return

    yield (
        "🔍 Analizando requisitos con el Agente Arquitecto…",
        _state,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        "",
    )

    try:
        strategy = ArchitectCrew().run(prompt.strip())
        _state["strategy"] = strategy.model_dump()
        _state["requirements"] = prompt.strip()

        yield (
            _strategy_markdown(strategy),
            _state,
            gr.update(visible=True),   # approve btn
            gr.update(visible=True),   # cancel btn
            gr.update(visible=False),  # analyze btn hidden while awaiting decision
            "",
        )
    except Exception as exc:
        yield (
            f"❌ Error en el Arquitecto: {exc}",
            _state,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            "",
        )


def approve_and_build(prompt: str, _state: dict):
    """
    Fase 2 (HITL Paso 2 — aprobado): construye la app con la estrategia guardada.
    """
    strategy = CrewStrategy.model_validate(_state.get("strategy", {}))
    requirements = _state.get("requirements", prompt)

    log_lines = [f"✅ Estrategia aprobada. Construyendo `{strategy.module_name}`…"]
    yield (
        "\n".join(log_lines),
        list_generated_files(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

    try:
        inputs = {
            "requirements": requirements,
            "module_name": strategy.module_name,
            "base_name": strategy.module_name.removesuffix(".py"),
            "class_name": strategy.class_name,
        }
        EngineeringTeam().set_strategy(strategy).crew().kickoff(inputs=inputs)
        log_lines.append("✅ Construcción completada. Archivos en `generated-apps/`.")
    except Exception as exc:
        log_lines.append(f"❌ Error durante la construcción: {exc}")

    yield (
        "\n".join(log_lines),
        list_generated_files(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def cancel_build(_state: dict):
    """Fase 2 (HITL Paso 2 — cancelado): descarta la estrategia sin construir."""
    _state.clear()
    return (
        "❌ Construcción cancelada por el usuario.",
        _state,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


# ---------------------------------------------------------------------------
# Interfaz Gradio
# ---------------------------------------------------------------------------

with gr.Blocks(title="Fábrica de Apps — CrewAI") as demo:
    gr.Markdown(
        """
        # 🏭 Fábrica de Apps con CrewAI
        **Flujo HITL:** Describe tu app → revisa la estrategia del Arquitecto → aprueba o cancela.
        """
    )

    flow_state = gr.State({})

    with gr.Row():
        with gr.Column(scale=2):
            prompt_box = gr.Textbox(
                label="Describe tu app",
                placeholder=EXAMPLE_PROMPT,
                lines=10,
            )

            with gr.Row():
                analyze_btn = gr.Button("🔍 Analizar", variant="primary")
                approve_btn = gr.Button("✅ Aprobar y Construir", variant="primary", visible=False)
                cancel_btn  = gr.Button("❌ Cancelar", variant="stop", visible=False)

        with gr.Column(scale=1):
            files_box = gr.Markdown(label="Archivos generados", value=list_generated_files())
            refresh_btn = gr.Button("🔄 Actualizar lista", variant="secondary")

    output_box = gr.Markdown(label="Resultado")

    # ── Eventos ──────────────────────────────────────────────────────────────

    analyze_btn.click(
        fn=analyze,
        inputs=[prompt_box, flow_state],
        outputs=[output_box, flow_state, approve_btn, cancel_btn, analyze_btn, files_box],
    )

    approve_btn.click(
        fn=approve_and_build,
        inputs=[prompt_box, flow_state],
        outputs=[output_box, files_box, approve_btn, cancel_btn, analyze_btn],
    )

    cancel_btn.click(
        fn=cancel_build,
        inputs=[flow_state],
        outputs=[output_box, flow_state, approve_btn, cancel_btn, analyze_btn],
    )

    refresh_btn.click(
        fn=list_generated_files,
        inputs=[],
        outputs=[files_box],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True, theme=gr.themes.Soft())
