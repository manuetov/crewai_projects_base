"""
McpFilesystemTool — conecta agentes CrewAI con el servidor MCP Filesystem.

El acceso queda restringido al directorio generated-apps/ del proyecto.
Los agentes no pueden leer ni escribir fuera de ese sandbox.

Operaciones disponibles (argumento tool_name):
    read_file        → {"path": "archivo.py"}
    write_file       → {"path": "archivo.py", "content": "..."}
    list_directory   → {"path": "."}
    create_directory → {"path": "subdir/"}

Las rutas son siempre relativas a generated-apps/.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Type

from crewai.tools import BaseTool
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic import BaseModel, Field


# Ruta absoluta al sandbox — computed once at import time
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
GENERATED_APPS_DIR = os.path.join(_PROJECT_ROOT, "generated-apps")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class McpFilesystemInput(BaseModel):
    """Input schema para McpFilesystemTool."""

    tool_name: str = Field(
        ...,
        description=(
            "Nombre de la herramienta MCP filesystem a invocar. "
            "Valores válidos: 'read_file', 'write_file', 'list_directory', 'create_directory'."
        ),
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Argumentos para la herramienta MCP como diccionario. Ejemplos: "
            "read_file → {'path': 'temperature_converter.py'}; "
            "write_file → {'path': 'result.txt', 'content': 'hola'}; "
            "list_directory → {'path': '.'}; "
            "create_directory → {'path': 'subdir'}."
        ),
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class McpFilesystemTool(BaseTool):
    """
    Herramienta CrewAI que actúa como puente hacia el servidor MCP Filesystem.
    Restringe todas las rutas al directorio generated-apps/ del proyecto.
    """

    name: str = "mcp_filesystem"
    description: str = (
        "Lee, escribe y lista archivos dentro del directorio generated-apps/ "
        "a través del servidor MCP Filesystem. "
        "Operaciones disponibles: read_file, write_file, list_directory, create_directory. "
        "Todas las rutas son relativas a generated-apps/ y no pueden salir de ese directorio."
    )
    args_schema: Type[BaseModel] = McpFilesystemInput

    def _run(self, tool_name: str, arguments: dict[str, Any] | None = None) -> str:
        """Entry point síncrono — lanza el cliente MCP async en un loop nuevo."""
        if arguments is None:
            arguments = {}
        os.makedirs(GENERATED_APPS_DIR, exist_ok=True)
        try:
            return asyncio.run(self._call_mcp(tool_name, arguments))
        except ValueError as exc:
            return f"❌ Acceso denegado: {exc}"
        except Exception as exc:
            return f"❌ Error MCP ({tool_name}): {exc}"

    # ── async internals ─────────────────────────────────────────────────────

    async def _call_mcp(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Conecta con el servidor MCP stdio y llama a la herramienta indicada."""
        # Parchear el campo 'path' para aplicar el sandbox
        patched_args = dict(arguments)
        if "path" in patched_args:
            patched_args["path"] = self._sandbox_path(patched_args["path"])

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", GENERATED_APPS_DIR],
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, patched_args)

        # Serializar la respuesta (list[TextContent | ImageContent | ...])
        parts: list[str] = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))

        return "\n".join(parts) if parts else "(sin contenido)"

    # ── sandbox ──────────────────────────────────────────────────────────────

    def _sandbox_path(self, path: str) -> str:
        """
        Resuelve la ruta relativa dentro de GENERATED_APPS_DIR
        y lanza ValueError si intentara escapar del sandbox.
        """
        base = os.path.realpath(GENERATED_APPS_DIR)
        candidate = os.path.realpath(os.path.join(base, path))
        if not candidate.startswith(base + os.sep) and candidate != base:
            raise ValueError(
                f"'{path}' resolvería a '{candidate}', fuera de generated-apps/."
            )
        return candidate
