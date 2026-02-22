"""
FileWriterTool para CrewAI — compatible con Windows.

Usa crewai_tools.FileWriterTool y FileReaderTool para operaciones de archivo
sin necesidad de MCP o NodeJS.
"""

from crewai_tools import FileWriterTool, FileReaderTool
import os

# Ruta del proyecto
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
GENERATED_APPS_DIR = os.path.join(_PROJECT_ROOT, "generated-apps")

# Crear directorio si no existe
os.makedirs(GENERATED_APPS_DIR, exist_ok=True)

# Inicializar herramientas
file_writer_tool = FileWriterTool(dir_path=GENERATED_APPS_DIR)
file_reader_tool = FileReaderTool(dir_path=GENERATED_APPS_DIR)

__all__ = ["file_writer_tool", "file_reader_tool"]
