"""
AppBuilderFlow — CrewAI Flow con Human-in-the-Loop (HITL)

Fases:
  1. run_architect  (@start)          → ArchitectCrew produce CrewStrategy
  2. request_approval (@listen)       → HITL: muestra estrategia, espera aprobación
  3. run_engineering_team (@listen)   → construye la app solo si fue aprobado

El HITL se resuelve de forma diferente según el modo de ejecución:
  - CLI (crewai run / python main.py): input() de terminal
  - Gradio UI: los métodos run_architect / run_engineering_team se llaman
    directamente desde app_gradio.py, sin necesidad de pausar el Flow.
"""
from __future__ import annotations

from typing import Optional

from crewai.flow.flow import Flow, FlowState, listen, start

from coder_agents.crew import ArchitectCrew, EngineeringTeam
from coder_agents.models import CrewStrategy


# ---------------------------------------------------------------------------
# Estado del Flow
# ---------------------------------------------------------------------------

class AppBuilderState(FlowState):
    requirements: str = ""
    strategy: Optional[CrewStrategy] = None
    approved: bool = False


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

class AppBuilderFlow(Flow[AppBuilderState]):
    """Orquesta el pipeline Arquitecto → HITL → Equipo de Ingeniería."""

    # ── Fase 1: Arquitecto ──────────────────────────────────────────────────

    @start()
    def run_architect(self):
        """Ejecuta el Agente Arquitecto y almacena la estrategia en el estado."""
        print("\n[Flow] ── Fase 1: Arquitecto ──────────────────────────────")
        print("[Arquitecto] Analizando requisitos...")

        strategy = ArchitectCrew().run(self.state.requirements)
        self.state.strategy = strategy

        print(f"[Arquitecto] Módulo   : {strategy.module_name}")
        print(f"[Arquitecto] Clase    : {strategy.class_name}")
        print(f"[Arquitecto] Agentes  : {[r.value for r in strategy.agents_needed]}")
        print(f"[Arquitecto] Motivo   : {strategy.rationale}")

        return strategy

    # ── Fase 2: HITL ───────────────────────────────────────────────────────

    @listen(run_architect)
    def request_approval(self, strategy: CrewStrategy):
        """
        Human-in-the-Loop: muestra la estrategia y espera aprobación por terminal.
        En modo Gradio este método NO se invoca; la UI gestiona la aprobación.
        """
        print("\n[Flow] ── Fase 2: HITL — Revisión de Estrategia ──────────")
        _print_strategy(strategy)

        while True:
            answer = input(
                "\n¿Aprobar esta estrategia y construir la app? [s/n]: "
            ).strip().lower()
            if answer in ("s", "si", "sí", "y", "yes"):
                self.state.approved = True
                print("[HITL] ✅ Estrategia aprobada.")
                break
            elif answer in ("n", "no"):
                self.state.approved = False
                print("[HITL] ❌ Construcción cancelada por el usuario.")
                break
            else:
                print("  → Por favor responde 's' (aprobar) o 'n' (cancelar).")

        return self.state.approved

    # ── Fase 3: Equipo de Ingeniería ────────────────────────────────────────

    @listen(request_approval)
    def run_engineering_team(self, approved: bool):
        """Construye la app solo si la estrategia fue aprobada."""
        print("\n[Flow] ── Fase 3: Equipo de Ingeniería ────────────────────")

        if not approved:
            print("[Flow] Construcción cancelada. No se generaron archivos.")
            return None

        strategy = self.state.strategy
        inputs = {
            "requirements": self.state.requirements,
            "module_name": strategy.module_name,
            "class_name": strategy.class_name,
        }

        print("[Equipo] Iniciando construcción...")
        result = (
            EngineeringTeam()
            .set_strategy(strategy)
            .crew()
            .kickoff(inputs=inputs)
        )
        print("[Flow] ✅ Construcción completada.")
        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_strategy(strategy: CrewStrategy) -> None:
    """Imprime la estrategia de forma legible en la terminal."""
    sep = "=" * 62
    print(sep)
    print("  ESTRATEGIA PROPUESTA POR EL ARQUITECTO")
    print(sep)
    print(f"  Módulo    : {strategy.module_name}")
    print(f"  Clase     : {strategy.class_name}")
    print(f"  Agentes   : {', '.join(r.value for r in strategy.agents_needed)}")
    print(f"\n  Justificación:\n    {strategy.rationale}")
    print(sep)
