# INSTRUCTIONS.md

## 1. Propósito

El proyecto **Task Distribution Assistant** es una herramienta impulsada por IA diseñada para equilibrar la carga de trabajo mediante el análisis de tareas, prioridades y disponibilidad del equipo. Su clase principal es `TaskDistributionAssistant`, que se encarga de procesar la información de las tareas y disponibilidades del equipo, y genera propuestas de asignación óptimas utilizando un modelo de lenguaje de IA (LLM) como GPT-3.

## 2. Stack tecnológico

- **Python**: Lenguaje principal utilizado para implementar la lógica del backend.
- **SQLite**: Utilizado para el almacenamiento de datos local.
- **OpenAI API**: Se utiliza para las capacidades de IA, específicamente para la generación de propuestas de asignación a través de LLM.
- **Gradio** (si existe frontend): Para construir la interfaz web interactiva que permite a los usuarios ingresar datos y obtener resultados visualizados.

## 3. Estructura de archivos

En el directorio `generated-apps/`, los archivos principales son:

- **`task_distribution_assistant.py`**: Contiene la implementación principal del backend y la clase `TaskDistributionAssistant`.
- **`app.py`** (si existe): Implementa el frontend utilizando Gradio para la interacción del usuario.
- **`test_task_distribution_assistant.py`**: Contiene pruebas unitarias para el módulo backend.

## 4. Instalación

Para instalar las dependencias necesarias, ejecute:

```sh
pip install -r requirements.txt
```

## 5. Ejecución

Para iniciar el backend (y el frontend si está disponible), siga las siguientes instrucciones:

- **Backend**: Ejecute el módulo principal con el siguiente comando:
  ```sh
  python task_distribution_assistant.py
  ```

- **Frontend** (si existe): Ejecute:
  ```sh
  python app.py
  ```

## 6. Tests

Para ejecutar las pruebas:

```sh
python -m pytest test_task_distribution_assistant.py
```

## 7. Convenciones

- **Nomenclatura**: Use un estilo de nomenclatura de la serpiente (snake_case) para variables y funciones. Las clases utilizan el PascalCase.
- **Estilo de código**: Siguiendo las pautas de PEP 8. Asegúrese de que las líneas no superen los 79 caracteres de longitud donde sea posible.

## 8. Notas para IA

- **Entry Points**: `task_distribution_assistant.py` y `app.py` (si existe) son los puntos de entrada principales del proyecto. Inicie procesos o servidores desde aquí.
- **No Modificar**: Evite modificar `requirements.txt` y cualquier archivo de configuración del entorno planeado, a menos que sea necesario al agregar dependencias.
- **Extensión del proyecto**: Para implementar nuevas funcionalidades, agregue métodos a la clase `TaskDistributionAssistant` y considere actualizar o crear nueva lógica de frontend en `app.py`. Mantenga siempre las pruebas actualizadas para cualquier cambio significativo realizado en el backend.