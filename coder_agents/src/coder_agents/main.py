#!/usr/bin/env python
import warnings
import os

from coder_agents.crew import ArchitectCrew, EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs("generated-apps", exist_ok=True)

# ---------------------------------------------------------------------------
# Prompt del usuario — en Prioridad 3 esto llegará desde la UI Gradio
# ---------------------------------------------------------------------------

USER_PROMPT = """
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


def run():
    """
    Flujo principal:
      1. El Agente Arquitecto analiza el prompt y produce una CrewStrategy.
      2. El equipo de ingeniería se construye filtrando solo los agentes necesarios.
      3. El equipo ejecuta las tareas en orden secuencial.
    """
    # ── Fase 1: Arquitecto ──────────────────────────────────────────────────
    print("[Arquitecto] Analizando requisitos...")
    strategy = ArchitectCrew().run(USER_PROMPT)

    print(f"[Arquitecto] Módulo   : {strategy.module_name}")
    print(f"[Arquitecto] Clase    : {strategy.class_name}")
    print(f"[Arquitecto] Agentes  : {[r.value for r in strategy.agents_needed]}")
    print(f"[Arquitecto] Motivo   : {strategy.rationale}")

    # ── Fase 2: Equipo de ingeniería ────────────────────────────────────────
    inputs = {
        "requirements": USER_PROMPT,
        "module_name": strategy.module_name,
        "class_name": strategy.class_name,
    }

    print("\n[Equipo] Iniciando construcción...")
    result = (
        EngineeringTeam()
        .set_strategy(strategy)
        .crew()
        .kickoff(inputs=inputs)
    )
    return result


if __name__ == "__main__":
    run()