from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Roles disponibles en el equipo de ingeniería."""

    ENGINEERING_LEAD = "engineering_lead"
    BACKEND_ENGINEER = "backend_engineer"
    FRONTEND_ENGINEER = "frontend_engineer"
    TEST_ENGINEER = "test_engineer"
    DOCS_ENGINEER = "docs_engineer"


class CrewStrategy(BaseModel):
    """Estrategia de construcción devuelta por el Agente Arquitecto."""

    module_name: str = Field(
        ...,
        description=(
            "Nombre del archivo Python principal del módulo, ej. 'accounts.py'. "
            "Debe terminar en '.py'."
        ),
    )
    class_name: str = Field(
        ...,
        description=(
            "Nombre de la clase principal dentro del módulo, ej. 'Account'. "
            "Debe seguir la convención PascalCase."
        ),
    )
    agents_needed: List[AgentRole] = Field(
        ...,
        description=(
            "Lista ordenada de roles de agentes necesarios para implementar los requisitos. "
            "Debe incluir siempre engineering_lead y backend_engineer. "
            "Añadir frontend_engineer si se requiere UI/demo/Gradio. "
            "Añadir test_engineer si se requieren pruebas unitarias."
        ),
    )
    rationale: str = Field(
        ...,
        description=(
            "Justificación breve de las decisiones tomadas: nombre del módulo, "
            "clase y agentes seleccionados."
        ),
    )
