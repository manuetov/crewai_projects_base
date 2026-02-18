#!/usr/bin/env python
"""
Gradio UI — Fábrica de Apps con CrewAI
Permite al usuario describir su app y lanzar el pipeline Arquitecto → Equipo.
"""
import os
import threading
import gradio as gr

from src.coder_agents.main import run

# ---------------------------------------------------------------------------
# Placeholder de ejemplo visible en el textbox al iniciar
# ---------------------------------------------------------------------------
EXAMPLE_PROMPT = """\
Un sistema de gestión de tareas (to-do list) con:
- Crear, completar y eliminar tareas
- Categorías y prioridades
- Informe de resumen
Necesita interfaz Gradio y pruebas unitarias.
"""

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated-apps")


def list_generated_files() -> str:
    """Devuelve una lista de los archivos generados en generated-apps/."""
    if not os.path.isdir(OUTPUT_DIR):
        return "_Sin archivos generados aún._"
    files = sorted(os.listdir(OUTPUT_DIR))
    if not files:
        return "_Sin archivos generados aún._"
    return "\n".join(f"- `{f}`" for f in files)


def build_app(prompt: str):
    """
    Callback del botón "Construir".
    Ejecuta el pipeline CrewAI y hace streaming de logs hacia el textbox de salida.
    """
    if not prompt or not prompt.strip():
        yield "⚠️ Por favor, describe tu app antes de construir.", ""
        return

    log_lines: list[str] = []

    def log(msg: str):
        log_lines.append(msg)

    log("🔍 Iniciando Agente Arquitecto…")
    yield "\n".join(log_lines), ""

    try:
        # Ejecutar el pipeline (bloqueante; corre en el hilo de Gradio)
        run(prompt.strip())
        log("✅ Construcción completada.")
    except Exception as exc:
        log(f"❌ Error durante la construcción: {exc}")

    files_md = list_generated_files()
    yield "\n".join(log_lines), files_md


# ---------------------------------------------------------------------------
# Interfaz Gradio
# ---------------------------------------------------------------------------

with gr.Blocks(title="Fábrica de Apps — CrewAI", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏭 Fábrica de Apps con CrewAI
        Describe tu aplicación y el equipo de agentes la construirá automáticamente.
        Los archivos generados aparecerán en `generated-apps/`.
        """
    )

    with gr.Row():
        with gr.Column(scale=2):
            prompt_box = gr.Textbox(
                label="Describe tu app",
                placeholder=EXAMPLE_PROMPT,
                lines=10,
                value="",
            )
            build_btn = gr.Button("🚀 Construir", variant="primary")

        with gr.Column(scale=1):
            files_box = gr.Markdown(
                label="Archivos generados",
                value=list_generated_files(),
            )
            refresh_btn = gr.Button("🔄 Actualizar lista", variant="secondary")

    log_box = gr.Textbox(
        label="Log de construcción",
        lines=20,
        interactive=False,
        show_copy_button=True,
    )

    # Eventos
    build_btn.click(
        fn=build_app,
        inputs=[prompt_box],
        outputs=[log_box, files_box],
    )

    refresh_btn.click(
        fn=list_generated_files,
        inputs=[],
        outputs=[files_box],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
