# app_gradio.py
import gradio as gr
from datetime import datetime
import os
import sys
import io
import threading
import queue
import time
import re

# Añadir el path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from stock_price.crew import StockPicker


def strip_ansi_codes(text: str) -> str:
    """Elimina códigos de escape ANSI del texto"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # También limpiar secuencias como [36m, [0m, etc. que pueden aparecer como texto
    text = ansi_escape.sub('', text)
    # Limpiar variantes que aparecen como texto plano
    text = re.sub(r'\[[\d;]*m', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text


class OutputCapture:
    """Captura stdout/stderr en tiempo real para mostrar en Gradio"""
    
    def __init__(self):
        self.output_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.capturing = False
        
    def write(self, text):
        if text.strip():  # Solo añadir si hay contenido
            self.output_queue.put(text)
        # También escribir al stdout original para debug
        self.original_stdout.write(text)
        
    def flush(self):
        self.original_stdout.flush()
        
    def start(self):
        self.capturing = True
        sys.stdout = self
        sys.stderr = self
        
    def stop(self):
        self.capturing = False
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def get_output(self):
        """Obtiene todo el output acumulado"""
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
    
    # Variables para almacenar el resultado y estado
    result_holder = {'result': None, 'error': None, 'done': False}
    captured_output = []
    capture = OutputCapture()
    
    def run_crew():
        """Ejecuta CrewAI en un hilo separado"""
        try:
            capture.start()
            result = StockPicker().crew().kickoff(inputs=inputs)
            result_holder['result'] = result
        except Exception as e:
            result_holder['error'] = str(e)
        finally:
            capture.stop()
            result_holder['done'] = True
    
    # Iniciar el hilo de ejecución
    thread = threading.Thread(target=run_crew)
    thread.start()
    
    # Header inicial
    header = f"## 🚀 Análisis del sector: **{sector}**\n\n"
    console_output = ""
    
    yield header + "⏳ Iniciando...", ""
    
    # Actualizar la UI mientras CrewAI ejecuta
    while not result_holder['done']:
        time.sleep(0.3)  # Actualizar cada 300ms
        
        new_output = capture.get_output()
        if new_output:
            captured_output.append(new_output)
            console_output = ''.join(captured_output)
            
            # Formatear output para mostrar en markdown
            formatted_console = format_console_output(console_output)
            yield header + "⏳ Ejecutando...\n\n" + formatted_console, ""
    
    # Esperar a que termine el hilo
    thread.join()
    
    # Obtener cualquier output restante
    final_new_output = capture.get_output()
    if final_new_output:
        captured_output.append(final_new_output)
    
    console_output = ''.join(captured_output)
    formatted_console = format_console_output(console_output)
    
    # Mostrar resultado final
    if result_holder['error']:
        final_result = f"""## ❌ Error en el análisis

```
{result_holder['error']}
```

### Posibles causas:
- API key no configurada
- Error de conexión
- Formato de respuesta inválido
"""
    else:
        final_result = f"""## ✅ Resultado del Análisis

{result_holder['result']}

---

### 📁 Archivos generados:
- `output/trending_companies.json` - Empresas encontradas
- `output/research_report.json` - Investigación detallada  
- `output/decision.md` - Decisión final

---
*Análisis completado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    yield header + formatted_console, final_result


def format_console_output(raw_output: str) -> str:
    """Formatea la salida de consola para mostrar en markdown"""
    if not raw_output:
        return ""
    
    # Primero limpiar códigos ANSI
    clean_output = strip_ansi_codes(raw_output)
    
    # Limpiar y formatear
    lines = clean_output.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line == '─' * len(line):  # Saltar líneas vacías o solo guiones
            continue
            
        # Detectar y formatear diferentes tipos de mensajes de CrewAI
        if 'Crew Execution Started' in line:
            formatted_lines.append(f"\n### 🚀 Ejecución Iniciada")
        elif 'Task Started' in line:
            formatted_lines.append(f"\n### 📋 Tarea Iniciada")
        elif 'Name:' in line:
            formatted_lines.append(f"**{line}**")
        elif 'Agent:' in line:
            formatted_lines.append(f"\n### 🤖 {line}")
        elif 'Task:' in line:
            formatted_lines.append(f"\n**📋 {line}**")
        elif 'Thought:' in line:
            formatted_lines.append(f"\n💭 *{line}*")
        elif 'Action:' in line and 'Action Input' not in line:
            formatted_lines.append(f"\n⚡ `{line}`")
        elif 'Action Input:' in line:
            formatted_lines.append(f"   📥 `{line}`")
        elif 'Observation:' in line:
            formatted_lines.append(f"\n📊 **Observación:** {line.replace('Observation:', '')}")
        elif 'Result:' in line:
            formatted_lines.append(f"\n📊 {line}")
        elif 'Final Answer:' in line:
            formatted_lines.append(f"\n### ✅ {line}")
        elif 'Memory Retrieval' in line or 'Memory Save' in line:
            formatted_lines.append(f"\n🧠 {line}")
        elif 'Retrieving' in line or 'Saving' in line:
            formatted_lines.append(f"   ⏳ {line}")
        elif 'Tool' in line:
            formatted_lines.append(f"\n🔧 {line}")
        elif 'search' in line.lower():
            formatted_lines.append(f"🔍 {line}")
        elif line.startswith('#'):
            formatted_lines.append(f"\n{line}")
        elif 'Working on' in line or 'Starting' in line:
            formatted_lines.append(f"\n🔄 {line}")
        elif 'Error' in line or 'error' in line:
            formatted_lines.append(f"\n❌ {line}")
        elif 'ID:' in line:
            continue  # Saltar IDs técnicos
        elif 'Status:' in line:
            formatted_lines.append(f"   📌 {line}")
        elif '{' in line and '}' in line:
            # JSON o diccionarios - mostrar como código
            formatted_lines.append(f"\n```json\n{line}\n```")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def load_output_file(filename: str):
    """Carga y muestra el contenido de un archivo de output"""
    filepath = os.path.join("output", filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"### 📄 {filename}\n\n```json\n{content}\n```"
    else:
        return f"⚠️ Archivo `{filename}` no encontrado. Ejecuta un análisis primero."


# Interfaz Gradio
with gr.Blocks(
    title="Stock Picker AI - CrewAI",
    theme=gr.themes.Soft(),
    css="""
        .main-header { text-align: center; margin-bottom: 20px; }
        .console-box { 
            background-color: #1a1a2e; 
            border-radius: 8px; 
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            max-height: 500px;
            overflow-y: auto;
        }
        .result-box { 
            min-height: 200px; 
            background-color: #0f3460;
            border-radius: 8px;
            padding: 15px;
        }
    """
) as demo:
    
    # Header
    gr.Markdown(
        """
        # 📈 Stock Picker AI
        ### Encuentra las mejores empresas para invertir usando agentes de IA
        
        Este dashboard utiliza **CrewAI** con múltiples agentes especializados:
        - 🔍 **Buscador de Tendencias**: Encuentra empresas en las noticias
        - 📊 **Investigador Financiero**: Analiza cada empresa en detalle
        - 🎯 **Selector de Acciones**: Elige la mejor opción de inversión
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
                        placeholder="Ej: tecnología, salud, energía, fintech...",
                        value="tecnología",
                        info="Ingresa el sector del mercado que quieres analizar"
                    )
                    
                    gr.Examples(
                        examples=["tecnología", "inteligencia artificial", "energía renovable", "salud", "fintech", "semiconductores"],
                        inputs=sector_input,
                        label="Ejemplos de sectores"
                    )
                    
                    run_btn = gr.Button(
                        "🚀 Iniciar Análisis",
                        variant="primary",
                        size="lg"
                    )
                    
                    gr.Markdown(
                        """
                        ### ℹ️ Información
                        - El análisis puede tardar varios minutos
                        - Verás el proceso en tiempo real
                        - Se generarán archivos en `output/`
                        """
                    )
                
                with gr.Column(scale=2):
                    # Panel de log en tiempo real
                    gr.Markdown("### 🖥️ Consola - Proceso en tiempo real")
                    console_output = gr.Markdown(
                        value="*Esperando inicio del análisis...*",
                        elem_classes=["console-box"]
                    )
                    
                    # Panel de resultado final
                    gr.Markdown("### 📊 Resultado Final")
                    result_output = gr.Markdown(
                        value="*El resultado aparecerá aquí cuando termine el análisis*",
                        elem_classes=["result-box"]
                    )
            
            run_btn.click(
                fn=run_analysis,
                inputs=[sector_input],
                outputs=[console_output, result_output]
            )
        
        # Tab 2: Ver Resultados
        with gr.TabItem("📁 Ver Resultados"):
            gr.Markdown("### Archivos de salida generados")
            
            with gr.Row():
                btn_trending = gr.Button("📊 Empresas en Tendencia")
                btn_research = gr.Button("📋 Informe de Investigación")
                btn_decision = gr.Button("🎯 Decisión Final")
            
            file_output = gr.Markdown()
            
            btn_trending.click(
                fn=lambda: load_output_file("trending_companies.json"),
                outputs=[file_output]
            )
            btn_research.click(
                fn=lambda: load_output_file("research_report.json"),
                outputs=[file_output]
            )
            btn_decision.click(
                fn=lambda: load_output_file("decision.md"),
                outputs=[file_output]
            )
        
        # Tab 3: Configuración
        with gr.TabItem("⚙️ Configuración"):
            gr.Markdown(
                """
                ### Variables de entorno requeridas
                
                Asegúrate de tener configuradas estas variables en tu archivo `.env`:
                
                | Variable | Descripción |
                |----------|-------------|
                | `OPENAI_API_KEY` | API key de OpenAI |
                | `SERPER_API_KEY` | API key de Serper (búsquedas) |
                | `PUSHOVER_USER` | Usuario de Pushover (notificaciones) |
                | `PUSHOVER_TOKEN` | Token de Pushover |
                
                ### Modelos utilizados
                
                Los agentes usan por defecto `gpt-4o-mini`. Puedes cambiarlos en `config/agents.yaml`.
                """
            )
    
    # Footer
    gr.Markdown(
        """
        ---
        *Powered by CrewAI + Gradio | ⚠️ Este análisis es solo informativo, no es consejo de inversión.*
        """
    )


if __name__ == "__main__":
    # Crear carpeta output si no existe
    os.makedirs("output", exist_ok=True)
    
    # Lanzar la app
    demo.launch(
        server_name="0.0.0.0",  # Accesible desde red local
        server_port=7860,
        share=False,  # Cambiar a True para compartir públicamente
        show_error=True
    )