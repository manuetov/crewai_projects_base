---
name: gradio-patterns
description: Convenciones de Gradio en CoderAgents. Usar al crear, modificar o revisar app.py o interfaces generadas por frontend_engineer.
---

# Patrones Gradio en CoderAgents

## Estructura esperada

- **Archivo**: `app.py` en el mismo directorio que el módulo backend
- **Ubicación**: `generated-apps/app.py` (junto a `{module_name}`)
- **Import**: `from {base_name} import {class_name}` (ej. `from accounts import Account`)

## Reglas del frontend_engineer

1. Una sola interfaz para demostrar la clase backend
2. Un solo usuario, prototipo/demo sencillo
3. Código autónomo: ejecutable tal cual, sin pasos extra
4. Si necesita `gradio`, el backend_engineer puede instalar vía:
   ```python
   import subprocess
   subprocess.run(["pip", "install", "gradio"], check=True)
   ```
   Usar siempre lista de argumentos, nunca string con espacios

## Output del agente

- Entregar **solo código Python**, sin markdown, sin delimitadores ``` ni comillas invertidas
- La salida debe poder guardarse directamente en `app.py` y ejecutarse

## Ejemplo de estructura mínima

```python
# app.py
from accounts import Account  # módulo backend en el mismo directorio

def main():
    account = Account()
    # ... UI Gradio que demuestra métodos de Account
```
