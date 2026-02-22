#!/usr/bin/env python
"""
Gradio UI — Fábrica de Apps con CrewAI
Implementa el HITL en la interfaz:
  Paso 1 ("Analizar")    → ArchitectCrew → muestra CrewStrategy para revisión
  Paso 2 ("Aprobar y Construir" o "Cancelar") → lanza la EngineeringTeam o aborta
"""
import os
import sys
import re
import html as html_module
import threading
import queue
import time
import gradio as gr

from coder_agents.crew import ArchitectCrew, EngineeringTeam, _GENERATED_APPS_DIR
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
# Terminal HTML helpers (portados de stock_price/app_gradio_v3.py)
# ---------------------------------------------------------------------------

ANSI_COLORS = {
    '30': '#000000', '31': '#cd3131', '32': '#0dbc79', '33': '#e5e510',
    '34': '#2472c8', '35': '#bc3fbc', '36': '#11a8cd', '37': '#e5e5e5',
    '90': '#666666', '91': '#f14c4c', '92': '#23d18b', '93': '#f5f543',
    '94': '#3b8eea', '95': '#d670d6', '96': '#29b8db', '97': '#ffffff',
}


def strip_ansi_to_html(text: str) -> str:
    """Convierte códigos ANSI a HTML con colores (paleta VS Code)."""
    text = html_module.escape(text)
    text = re.sub(r'\x1B', '', text)

    result = []
    i = 0
    open_spans = 0

    while i < len(text):
        match = re.match(r'\[(\d+(?:;\d+)*)m', text[i:])
        if match:
            codes = match.group(1).split(';')
            for code in codes:
                if code == '0':
                    result.append('</span>' * open_spans)
                    open_spans = 0
                elif code == '1':
                    result.append('<span style="font-weight:bold;">')
                    open_spans += 1
                elif code in ANSI_COLORS:
                    result.append(f'<span style="color:{ANSI_COLORS[code]};">')
                    open_spans += 1
            i += match.end()
        else:
            result.append(text[i])
            i += 1

    result.append('</span>' * open_spans)
    return ''.join(result)


def format_terminal_html(text: str) -> str:
    """Renderiza texto de terminal con estilo VS Code dark."""
    colored = strip_ansi_to_html(text).replace('\n', '<br>')
    return f'''<div class="terminal-content" style="
        font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
        background-color: #1e1e1e;
        color: #cccccc;
        padding: 15px;
        border-radius: 8px;
        height: 520px;
        overflow-y: auto;
        border: 1px solid #3c3c3c;
    ">{colored}</div>'''


def format_strategy_html(s: CrewStrategy) -> str:
    """Renderiza la estrategia del Arquitecto como panel HTML estilizado."""
    agents = " · ".join(
        f'<span style="background:#2472c8;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">{r.value}</span>'
        for r in s.agents_needed
    )
    return f'''<div style="
        font-family: 'Segoe UI', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #238636;
        font-size: 14px;
        line-height: 1.6;
    ">
        <div style="color:#58a6ff;font-size:16px;font-weight:bold;margin-bottom:12px;">
            🏗️ Estrategia propuesta por el Arquitecto
        </div>
        <table style="border-collapse:collapse;width:100%;margin-bottom:14px;">
            <tr>
                <td style="color:#8b949e;padding:4px 12px 4px 0;width:120px;">Módulo</td>
                <td><code style="background:#161b22;padding:2px 8px;border-radius:4px;color:#79c0ff;">{s.module_name}</code></td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:4px 12px 4px 0;">Clase principal</td>
                <td><code style="background:#161b22;padding:2px 8px;border-radius:4px;color:#79c0ff;">{s.class_name}</code></td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:4px 12px 4px 0;vertical-align:top;">Agentes</td>
                <td style="padding-top:4px;">{agents}</td>
            </tr>
        </table>
        <div style="color:#8b949e;margin-bottom:4px;">Justificación</div>
        <div style="background:#161b22;padding:10px 14px;border-radius:6px;color:#e6edf3;font-style:italic;">
            {html_module.escape(s.rationale)}
        </div>
        <div style="color:#3fb950;margin-top:16px;font-size:13px;">
            ✅ Revisa la estrategia y aprueba para iniciar la construcción.
        </div>
    </div>'''


def format_result_html(text: str) -> str:
    """Renderiza el resultado/estado final en panel HTML."""
    colored = strip_ansi_to_html(str(text)).replace('\n', '<br>')
    return f'''<div style="
        font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
        white-space: pre-wrap;
        background-color: #0d1117;
        color: #58a6ff;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #238636;
    ">{colored}</div>'''


def format_error_html(text: str) -> str:
    colored = strip_ansi_to_html(str(text)).replace('\n', '<br>')
    return f'''<div style="
        font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        white-space: pre-wrap;
        background-color: #0d1117;
        color: #f14c4c;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #cd3131;
    ">{colored}</div>'''


# ---------------------------------------------------------------------------
# OutputCapture (captura stdout/stderr en tiempo real)
# ---------------------------------------------------------------------------

class OutputCapture:
    def __init__(self):
        self.queue = queue.Queue()
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr

    def write(self, text):
        if text:
            self.queue.put(text)
        self._orig_stdout.write(text)

    def flush(self):
        self._orig_stdout.flush()

    def start(self):
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr

    def drain(self) -> str:
        chunks = []
        while True:
            try:
                chunks.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return ''.join(chunks)


# ---------------------------------------------------------------------------
# Helpers UI
# ---------------------------------------------------------------------------

def list_generated_files() -> str:
    if not os.path.isdir(OUTPUT_DIR):
        return "_Sin archivos generados aún._"
    entries = sorted(os.listdir(OUTPUT_DIR))
    lines = []
    for entry in entries:
        full = os.path.join(OUTPUT_DIR, entry)
        if os.path.isdir(full):
            lines.append(f"📁 **{entry}/**")
        else:
            lines.append(f"· `{entry}`")
    return "\n".join(lines) if lines else "_Sin archivos generados aún._"


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def analyze(prompt: str, _state: dict):
    if not prompt or not prompt.strip():
        yield (
            format_error_html("⚠️ Por favor, describe tu app antes de analizar."),
            _state,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            list_generated_files(),
        )
        return

    yield (
        format_terminal_html("🔍 Analizando requisitos con el Agente Arquitecto…\n"),
        _state,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        list_generated_files(),
    )

    try:
        strategy = ArchitectCrew().run(prompt.strip())
        _state["strategy"] = strategy.model_dump()
        _state["requirements"] = prompt.strip()

        yield (
            format_strategy_html(strategy),
            _state,
            gr.update(visible=True),   # approve btn
            gr.update(visible=True),   # cancel btn
            gr.update(visible=False),  # analyze btn oculto
            list_generated_files(),
        )
    except Exception as exc:
        yield (
            format_error_html(f"❌ Error en el Arquitecto:\n\n{exc}"),
            _state,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            list_generated_files(),
        )


def approve_and_build(prompt: str, _state: dict):
    strategy = CrewStrategy.model_validate(_state.get("strategy", {}))
    requirements = _state.get("requirements", prompt)

    header = f"✅ Estrategia aprobada — construyendo `{strategy.module_name}`\n{'='*62}\n\n"
    captured_chunks = []
    result_holder = {"error": None, "done": False}
    capture = OutputCapture()

    def run():
        try:
            capture.start()
            app_dir = os.path.join(_GENERATED_APPS_DIR, strategy.module_name.removesuffix(".py"))
            os.makedirs(app_dir, exist_ok=True)
            inputs = {
                "requirements": requirements,
                "module_name": strategy.module_name,
                "base_name": strategy.module_name.removesuffix(".py"),
                "class_name": strategy.class_name,
                "app_dir": app_dir,
            }
            EngineeringTeam().set_strategy(strategy).crew().kickoff(inputs=inputs)
        except Exception as exc:
            result_holder["error"] = str(exc)
        finally:
            capture.stop()
            result_holder["done"] = True

    thread = threading.Thread(target=run)
    thread.start()

    # Primer yield — ocultar botones
    yield (
        format_terminal_html(header),
        list_generated_files(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

    # Streaming en tiempo real
    while not result_holder["done"]:
        time.sleep(0.15)
        chunk = capture.drain()
        if chunk:
            captured_chunks.append(chunk)
            yield (
                format_terminal_html(header + ''.join(captured_chunks)),
                list_generated_files(),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

    thread.join()
    last = capture.drain()
    if last:
        captured_chunks.append(last)

    full_log = header + ''.join(captured_chunks)

    if result_holder["error"]:
        final_html = format_terminal_html(full_log) + format_error_html(
            f"\n❌ Error durante la construcción:\n\n{result_holder['error']}"
        )
    else:
        final_html = format_terminal_html(full_log) + format_result_html(
            f"\n✅ Construcción completada.\n"
            f"Archivos en: generated-apps/{strategy.module_name.removesuffix('.py')}/\n"
            f"⏱ {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    yield (
        final_html,
        list_generated_files(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def cancel_build(_state: dict):
    _state.clear()
    return (
        format_error_html("❌ Construcción cancelada por el usuario."),
        _state,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


# ---------------------------------------------------------------------------
# Interfaz Gradio
# ---------------------------------------------------------------------------

AUTO_SCROLL_JS = """
function() {
    const scroll = () => {
        document.querySelectorAll('.terminal-content').forEach(el => {
            el.scrollTop = el.scrollHeight;
        });
    };
    new MutationObserver(scroll).observe(document.body, {
        childList: true, subtree: true, characterData: true
    });
    setInterval(scroll, 200);
}
"""

with gr.Blocks(title="Fábrica de Apps — CrewAI", theme=gr.themes.Base()) as demo:
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

    output_box = gr.HTML(value=format_terminal_html("Esperando…"))

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
        outputs=[files_box],
    )

    demo.load(fn=None, js=AUTO_SCROLL_JS)

if __name__ == "__main__":
    demo.launch()


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
        app_dir = os.path.join(_GENERATED_APPS_DIR, strategy.module_name.removesuffix(".py"))
        os.makedirs(app_dir, exist_ok=True)
        inputs = {
            "requirements": requirements,
            "module_name": strategy.module_name,
            "base_name": strategy.module_name.removesuffix(".py"),
            "class_name": strategy.class_name,
            "app_dir": app_dir,
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
