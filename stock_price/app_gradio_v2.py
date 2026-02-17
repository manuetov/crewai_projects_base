# app_gradio.py - Version 2 con terminal real y auto-scroll
import gradio as gr
from datetime import datetime
import os
import sys
import threading
import queue
import time
import re

# Añadir el path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from stock_price.crew import StockPicker


def strip_ansi_codes(text: str) -> str:
    """Elimina códigos de escape ANSI del texto pero mantiene el formato"""
    # Eliminar secuencias ANSI de escape
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Limpiar variantes que aparecen como texto plano [36m, [0m, etc.
    text = re.sub(r'\[[\d;]*m', '', text)
    # Limpiar caracteres de control excepto newline y tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text


class OutputCapture:
    """Captura stdout/stderr en tiempo real"""
    
    def __init__(self):
        self.output_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        if text:
            self.output_queue.put(text)
        self.original_stdout.write(text)
        
    def flush(self):
        self.original_stdout.flush()
        
    def start(self):
        sys.stdout = self
        sys.stderr = self
        
    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def get_output(self):
        lines = []
        while not self.output_queue.empty():
            try:
                lines.append(self.output_queue.get_nowait())
            except queue.Empty:
                break
        return ''.join(lines)


def run_analysis(sector: str):
    """Ejecuta el análisis de CrewAI mostrando la salida en tiempo real"""
    
    if not sector.strip():
        yield "⚠️ Por favor, ingresa un sector para analizar.", ""
        return
    
    inputs = {
        'sector': sector.strip(),
        'current_year': str(datetime.now().year)
    }
    
    result_holder = {'result': None, 'error': None, 'done': False}
    captured_output = []
    capture = OutputCapture()
    
    def run_crew():
        try:
            capture.start()
            result = StockPicker().crew().kickoff(inputs=inputs)
            result_holder['result'] = result
        except Exception as e:
            result_holder['error'] = str(e)
        finally:
            capture.stop()
            result_holder['done'] = True
    
    thread = threading.Thread(target=run_crew)
    thread.start()
    
    # Mensaje inicial
    yield f"🚀 Iniciando análisis del sector: {sector}\n" + "="*50 + "\n", ""
    
    while not result_holder['done']:
        time.sleep(0.2)  # Actualizar cada 200ms
        
        new_output = capture.get_output()
        if new_output:
            captured_output.append(new_output)
            # Limpiar códigos ANSI pero mantener formato
            clean_output = strip_ansi_codes(''.join(captured_output))
            yield clean_output, ""
    
    thread.join()
    
    # Output final
    final_new_output = capture.get_output()
    if final_new_output:
        captured_output.append(final_new_output)
    
    clean_output = strip_ansi_codes(''.join(captured_output))
    
    # Resultado
    if result_holder['error']:
        final_result = f"""❌ ERROR EN EL ANÁLISIS
{'='*40}
{result_holder['error']}

Posibles causas:
• API key no configurada
• Error de conexión  
• Formato de respuesta inválido
"""
    else:
        final_result = f"""✅ RESULTADO DEL ANÁLISIS
{'='*40}

{result_holder['result']}

📁 Archivos generados:
• output/trending_companies.json
• output/research_report.json
• output/decision.md

⏱️ Completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    yield clean_output, final_result


def load_output_file(filename: str):
    """Carga contenido de archivo"""
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return f"⚠️ Archivo {filename} no encontrado"


# CSS personalizado para terminal
custom_css = """
#terminal-output {
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    background-color: #0c0c0c !important;
    color: #cccccc !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 6px !important;
}

#terminal-output textarea {
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace !important;
    background-color: #0c0c0c !important;
    color: #cccccc !important;
}

#result-output {
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace !important;
    font-size: 13px !important;
    background-color: #001a00 !important;
    color: #00ff00 !important;
    border: 2px solid #00aa00 !important;
    border-radius: 6px !important;
}

#result-output textarea {
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace !important;
    background-color: #001a00 !important;
    color: #00ff00 !important;
}

.main-header {
    text-align: center;
    margin-bottom: 20px;
}
"""

# JavaScript para auto-scroll
auto_scroll_js = """
function() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.id === 'terminal-output' || 
                mutation.target.closest('#terminal-output')) {
                const textarea = document.querySelector('#terminal-output textarea');
                if (textarea) {
                    textarea.scrollTop = textarea.scrollHeight;
                }
            }
        });
    });
    
    const config = { childList: true, subtree: true, characterData: true };
    const targetNode = document.body;
    observer.observe(targetNode, config);
    
    // También hacer scroll periódico
    setInterval(function() {
        const textarea = document.querySelector('#terminal-output textarea');
        if (textarea) {
            textarea.scrollTop = textarea.scrollHeight;
        }
    }, 300);
    
    return "Auto-scroll activado";
}
"""


with gr.Blocks(
    title="Stock Picker AI - CrewAI",
    theme=gr.themes.Base(),
    css=custom_css
) as demo:
    
    # Header
    gr.Markdown(
        """
        # 📈 Stock Picker AI
        ### Encuentra las mejores empresas para invertir usando agentes de IA
        
        **CrewAI** con agentes especializados: 🔍 Buscador | 📊 Investigador | 🎯 Selector
        """,
        elem_classes=["main-header"]
    )
    
    with gr.Tabs():
        # Tab 1: Análisis
        with gr.TabItem("🚀 Ejecutar Análisis"):
            with gr.Row():
                with gr.Column(scale=1):
                    sector_input = gr.Textbox(
                        label="Sector a analizar",
                        placeholder="Ej: tecnología, salud, energía...",
                        value="tecnología",
                        info="Ingresa el sector del mercado"
                    )
                    
                    gr.Examples(
                        examples=["tecnología", "inteligencia artificial", "energía renovable", "salud", "fintech"],
                        inputs=sector_input,
                        label="Ejemplos"
                    )
                    
                    run_btn = gr.Button("🚀 Iniciar Análisis", variant="primary", size="lg")
                    
                    gr.Markdown(
                        """
                        ### ℹ️ Info
                        - Proceso en tiempo real
                        - Auto-scroll activado
                        - Archivos en `output/`
                        """
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 🖥️ Terminal - Proceso en tiempo real")
                    console_output = gr.Textbox(
                        value="Esperando inicio del análisis...",
                        lines=20,
                        max_lines=20,
                        interactive=False,
                        show_label=False,
                        elem_id="terminal-output",
                        autoscroll=True
                    )
                    
                    gr.Markdown("### 📊 Resultado Final")
                    result_output = gr.Textbox(
                        value="El resultado aparecerá aquí cuando termine el análisis",
                        lines=10,
                        max_lines=15,
                        interactive=False,
                        show_label=False,
                        elem_id="result-output"
                    )
            
            run_btn.click(
                fn=run_analysis,
                inputs=[sector_input],
                outputs=[console_output, result_output]
            )
        
        # Tab 2: Ver Resultados
        with gr.TabItem("📁 Ver Resultados"):
            gr.Markdown("### Archivos de salida")
            
            with gr.Row():
                btn_trending = gr.Button("📊 Empresas Tendencia")
                btn_research = gr.Button("📋 Investigación")
                btn_decision = gr.Button("🎯 Decisión")
            
            file_output = gr.Textbox(
                lines=15,
                interactive=False,
                show_label=False,
                elem_id="terminal-output"
            )
            
            btn_trending.click(fn=lambda: load_output_file("trending_companies.json"), outputs=[file_output])
            btn_research.click(fn=lambda: load_output_file("research_report.json"), outputs=[file_output])
            btn_decision.click(fn=lambda: load_output_file("decision.md"), outputs=[file_output])
        
        # Tab 3: Configuración
        with gr.TabItem("⚙️ Configuración"):
            gr.Markdown(
                """
                ### Variables de entorno requeridas
                
                | Variable | Descripción |
                |----------|-------------|
                | `OPENAI_API_KEY` | API key de OpenAI |
                | `SERPER_API_KEY` | API key de Serper |
                | `PUSHOVER_USER` | Usuario Pushover |
                | `PUSHOVER_TOKEN` | Token Pushover |
                """
            )
    
    # Activar auto-scroll al cargar
    demo.load(fn=None, js=auto_scroll_js)
    
    gr.Markdown("---\n*Powered by CrewAI + Gradio | ⚠️ Solo informativo, no es consejo de inversión*")


if __name__ == "__main__":
    demo.launch()
