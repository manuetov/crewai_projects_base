# app_gradio.py - Version 3 con terminal HTML real
import gradio as gr
from datetime import datetime
import os
import sys
import threading
import queue
import time
import re
import html

# Añadir el path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from stock_price.crew import StockPicker


def strip_ansi_to_html(text: str) -> str:
    """Convierte códigos ANSI a HTML con colores"""
    import html as html_module
    
    # Mapeo de colores ANSI a CSS (paleta similar a VS Code terminal)
    ansi_colors = {
        '30': '#000000',  # negro
        '31': '#cd3131',  # rojo
        '32': '#0dbc79',  # verde
        '33': '#e5e510',  # amarillo
        '34': '#2472c8',  # azul
        '35': '#bc3fbc',  # magenta
        '36': '#11a8cd',  # cyan
        '37': '#e5e5e5',  # blanco
        '90': '#666666',  # gris brillante
        '91': '#f14c4c',  # rojo brillante
        '92': '#23d18b',  # verde brillante
        '93': '#f5f543',  # amarillo brillante
        '94': '#3b8eea',  # azul brillante
        '95': '#d670d6',  # magenta brillante
        '96': '#29b8db',  # cyan brillante
        '97': '#ffffff',  # blanco brillante
    }
    
    # Escapar HTML primero
    text = html_module.escape(text)
    
    # Eliminar secuencias de escape reales (\x1B)
    text = re.sub(r'\x1B', '', text)
    
    # Ahora procesar los códigos [XXm que quedaron como texto
    result = []
    i = 0
    open_spans = 0
    is_bold = False
    
    while i < len(text):
        # Buscar patrón [XXm o [X;XXm
        match = re.match(r'\[(\d+(?:;\d+)*)m', text[i:])
        if match:
            codes = match.group(1).split(';')
            
            for code in codes:
                if code == '0':
                    # Reset - cerrar todos los spans
                    result.append('</span>' * open_spans)
                    open_spans = 0
                    is_bold = False
                elif code == '1':
                    # Bold
                    result.append('<span style="font-weight:bold;">')
                    open_spans += 1
                    is_bold = True
                elif code in ansi_colors:
                    result.append(f'<span style="color:{ansi_colors[code]};">')
                    open_spans += 1
            
            i += match.end()
        else:
            result.append(text[i])
            i += 1
    
    # Cerrar spans que quedaron abiertos
    result.append('</span>' * open_spans)
    
    return ''.join(result)


def clean_for_display(text: str) -> str:
    """Limpia el texto y convierte ANSI a HTML con colores"""
    # Usar la conversión ANSI a HTML
    return strip_ansi_to_html(text)


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


def format_terminal_html(text: str) -> str:
    """Convierte texto de terminal a HTML con estilo VS Code y colores"""
    # Convertir ANSI a HTML con colores
    colored_text = clean_for_display(text)
    
    # Convertir newlines a <br>
    html_text = colored_text.replace('\n', '<br>')
    
    return f'''<div class="terminal-content" style="
        font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.3;
        white-space: pre-wrap;
        word-wrap: break-word;
        background-color: #1e1e1e;
        color: #cccccc;
        padding: 15px;
        border-radius: 8px;
        height: 500px;
        overflow-y: auto;
        border: 1px solid #3c3c3c;
    ">{html_text}</div>'''


def format_result_html(text: str) -> str:
    """Formatea el resultado final"""
    clean_text = clean_for_display(str(text))
    html_text = clean_text.replace('\n', '<br>')
    
    return f'''<div style="
        font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.4;
        white-space: pre-wrap;
        background-color: #0d1117;
        color: #58a6ff;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #238636;
    ">{html_text}</div>'''


def run_analysis(sector: str):
    """Ejecuta el análisis de CrewAI mostrando la salida en tiempo real"""
    
    if not sector.strip():
        yield format_terminal_html("⚠️ Por favor, ingresa un sector para analizar."), ""
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
    init_msg = f"🚀 Iniciando análisis del sector: {sector}\n{'='*60}\n\n"
    yield format_terminal_html(init_msg), ""
    
    while not result_holder['done']:
        time.sleep(0.15)  # Actualizar cada 150ms
        
        new_output = capture.get_output()
        if new_output:
            captured_output.append(new_output)
            full_output = init_msg + ''.join(captured_output)
            yield format_terminal_html(full_output), ""
    
    thread.join()
    
    # Output final
    final_new_output = capture.get_output()
    if final_new_output:
        captured_output.append(final_new_output)
    
    full_output = init_msg + ''.join(captured_output)
    
    # Resultado
    if result_holder['error']:
        final_result = f"""❌ ERROR
{'='*40}
{result_holder['error']}
"""
    else:
        final_result = f"""✅ ANÁLISIS COMPLETADO
{'='*40}

{result_holder['result']}

📁 Archivos: output/trending_companies.json, research_report.json, decision.md
⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    yield format_terminal_html(full_output + "\n\n✅ PROCESO COMPLETADO"), format_result_html(final_result)


def load_output_file(filename: str):
    """Carga contenido de archivo"""
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return format_terminal_html(content)
    return format_terminal_html(f"⚠️ Archivo {filename} no encontrado")


with gr.Blocks(
    title="Stock Picker AI",
    theme=gr.themes.Base(),
    css=".main-header { text-align: center; }"
) as demo:
    
    gr.Markdown(
        """
        # 📈 Stock Picker AI
        **CrewAI** con agentes: 🔍 Buscador | 📊 Investigador | 🎯 Selector
        """,
        elem_classes=["main-header"]
    )
    
    with gr.Tabs():
        with gr.TabItem("🚀 Análisis"):
            with gr.Row():
                with gr.Column(scale=1):
                    sector_input = gr.Textbox(
                        label="Sector",
                        placeholder="tecnología, salud, energía...",
                        value="tecnología"
                    )
                    
                    gr.Examples(
                        examples=["tecnología", "inteligencia artificial", "energía renovable", "salud", "fintech"],
                        inputs=sector_input
                    )
                    
                    run_btn = gr.Button("🚀 Iniciar", variant="primary", size="lg")
                
                with gr.Column(scale=3):
                    gr.Markdown("### 🖥️ Terminal")
                    console_output = gr.HTML(
                        value=format_terminal_html("Esperando inicio del análisis...")
                    )
                    
                    gr.Markdown("### 📊 Resultado")
                    result_output = gr.HTML(
                        value=format_result_html("El resultado aparecerá aquí")
                    )
            
            run_btn.click(
                fn=run_analysis,
                inputs=[sector_input],
                outputs=[console_output, result_output]
            )
        
        with gr.TabItem("📁 Resultados"):
            with gr.Row():
                btn_trending = gr.Button("📊 Empresas")
                btn_research = gr.Button("📋 Investigación")
                btn_decision = gr.Button("🎯 Decisión")
            
            file_output = gr.HTML()
            
            btn_trending.click(fn=lambda: load_output_file("trending_companies.json"), outputs=[file_output])
            btn_research.click(fn=lambda: load_output_file("research_report.json"), outputs=[file_output])
            btn_decision.click(fn=lambda: load_output_file("decision.md"), outputs=[file_output])
        
        with gr.TabItem("⚙️ Config"):
            gr.Markdown(
                """
                ### Variables requeridas (.env)
                - `OPENAI_API_KEY` - OpenAI
                - `SERPER_API_KEY` - Búsquedas
                - `PUSHOVER_USER/TOKEN` - Notificaciones
                """
            )
    
    # JavaScript para auto-scroll del terminal HTML
    auto_scroll_js = """
    function() {
        // MutationObserver para detectar cambios en el DOM
        const observer = new MutationObserver(function(mutations) {
            const terminals = document.querySelectorAll('.terminal-content');
            terminals.forEach(function(terminal) {
                terminal.scrollTop = terminal.scrollHeight;
            });
        });
        
        observer.observe(document.body, { 
            childList: true, 
            subtree: true, 
            characterData: true 
        });
        
        // También scroll periódico cada 200ms
        setInterval(function() {
            const terminals = document.querySelectorAll('.terminal-content');
            terminals.forEach(function(terminal) {
                terminal.scrollTop = terminal.scrollHeight;
            });
        }, 200);
        
        return "Auto-scroll activado";
    }
    """
    
    demo.load(fn=None, js=auto_scroll_js)
    
    gr.Markdown("---\n*CrewAI + Gradio | ⚠️ Solo informativo*")


if __name__ == "__main__":
    demo.launch()
