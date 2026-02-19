#!/usr/bin/env python
import warnings
import os

from coder_agents.flow import AppBuilderFlow

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs("generated-apps", exist_ok=True)

# ---------------------------------------------------------------------------
# Prompt de ejemplo — usado solo cuando se llama con `crewai run`
# En Prioridad 3+ el prompt llega desde la UI Gradio vía run(prompt)
# ---------------------------------------------------------------------------

_DEFAULT_PROMPT = """
Un sistema sencillo de gestión de cuentas para una plataforma de simulación de trading.
El sistema debe permitir a los usuarios crear una cuenta, depositar fondos y retirar fondos.
El sistema debe permitir a los usuarios registrar que han comprado o vendido acciones, proporcionando una cantidad.
El sistema debe calcular el valor total del portafolio del usuario, así como la ganancia o pérdida respecto al depósito inicial.
El sistema debe poder informar las posiciones (holdings) del usuario en cualquier momento.
El sistema debe poder informar la ganancia o pérdida del usuario en cualquier momento.
El sistema debe poder listar las transacciones que el usuario ha realizado a lo largo del tiempo.
El sistema debe evitar que el usuario retire fondos que lo dejen con un saldo negativo, o que compre más
acciones de las que puede pagar, o que venda acciones que no posee.
El sistema tiene acceso a una función get_share_price(symbol) que devuelve el precio actual de una acción,
e incluye una implementación de prueba que retorna precios fijos para AAPL, TSLA y GOOGL.
Requiere interfaz de usuario Gradio y pruebas unitarias.
"""


def run(requirements: str | None = None):
    """
    Flujo principal (con HITL por terminal):
      1. AppBuilderFlow.run_architect  — Agente Arquitecto → CrewStrategy
      2. AppBuilderFlow.request_approval — HITL: aprobación por terminal
      3. AppBuilderFlow.run_engineering_team — construye la app si fue aprobado

    Args:
        requirements: Descripción de la app. Si es None usa _DEFAULT_PROMPT.
    """
    prompt = (requirements or _DEFAULT_PROMPT).strip()
    flow = AppBuilderFlow()
    flow.state.requirements = prompt
    return flow.kickoff()


if __name__ == "__main__":
    run()