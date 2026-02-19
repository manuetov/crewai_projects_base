from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Optional
import os
import yaml

from coder_agents.models import AgentRole, CrewStrategy


# ---------------------------------------------------------------------------
# Role → method name maps (module-level to avoid @CrewBase introspection issues)
# ---------------------------------------------------------------------------

_AGENT_METHOD_MAP: dict[AgentRole, str] = {
    AgentRole.ENGINEERING_LEAD: "engineering_lead",
    AgentRole.BACKEND_ENGINEER: "backend_engineer",
    AgentRole.FRONTEND_ENGINEER: "frontend_engineer",
    AgentRole.TEST_ENGINEER: "test_engineer",
}

_TASK_METHOD_MAP: dict[AgentRole, str] = {
    AgentRole.ENGINEERING_LEAD: "design_task",
    AgentRole.BACKEND_ENGINEER: "code_task",
    AgentRole.FRONTEND_ENGINEER: "frontend_task",
    AgentRole.TEST_ENGINEER: "test_task",
}


# ---------------------------------------------------------------------------
# ArchitectCrew — single-agent crew that produces a CrewStrategy
# ---------------------------------------------------------------------------

class ArchitectCrew:
    """Ejecuta el Agente Arquitecto y devuelve una CrewStrategy validada."""

    _config_dir = os.path.join(os.path.dirname(__file__), "config")

    def _load_yaml(self, filename: str) -> dict:
        with open(os.path.join(self._config_dir, filename), "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(self, requirements: str) -> CrewStrategy:
        agents_cfg = self._load_yaml("agents.yaml")
        tasks_cfg = self._load_yaml("tasks.yaml")

        a_cfg = agents_cfg["architect"]
        architect = Agent(
            role=a_cfg["role"].strip(),
            goal=a_cfg["goal"].strip(),
            backstory=a_cfg["backstory"].strip(),
            llm=a_cfg["llm"],
            verbose=True,
        )

        t_cfg = tasks_cfg["strategy_task"]
        strategy_task = Task(
            description=t_cfg["description"],
            expected_output=t_cfg["expected_output"],
            agent=architect,
            output_pydantic=CrewStrategy,
        )

        result = Crew(
            agents=[architect],
            tasks=[strategy_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={"requirements": requirements})

        if result.pydantic:
            return result.pydantic
        # Fallback: parse raw JSON string
        return CrewStrategy.model_validate_json(result.raw)


# ---------------------------------------------------------------------------
# EngineeringTeam — builds only the agents/tasks specified by CrewStrategy
# ---------------------------------------------------------------------------

@CrewBase
class EngineeringTeam():
    """Tripulación de Ingenieros. Usa configs sin architect/strategy_task para evitar KeyError."""

    agents_config = 'config/agents_engineering.yaml'
    tasks_config = 'config/tasks_engineering.yaml'

    def set_strategy(self, strategy: CrewStrategy) -> "EngineeringTeam":
        """Almacena la estrategia del Arquitecto para filtrar agentes y tareas."""
        object.__setattr__(self, "_strategy", strategy)
        return self

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="unsafe",
            max_execution_time=240,
            max_retry_limit=5,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="unsafe",
            max_execution_time=240,
            max_retry_limit=5,
        )

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config['design_task'])

    @task
    def code_task(self) -> Task:
        return Task(config=self.tasks_config['code_task'])

    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config['frontend_task'])

    @task
    def test_task(self) -> Task:
        return Task(config=self.tasks_config['test_task'])

    @crew
    def crew(self) -> Crew:
        """Crea la tripulación filtrando agentes y tareas según la estrategia del Arquitecto."""
        strategy: Optional[CrewStrategy] = getattr(self, "_strategy", None)

        if strategy:
            agents = [
                getattr(self, _AGENT_METHOD_MAP[role])()
                for role in strategy.agents_needed
                if role in _AGENT_METHOD_MAP
            ]
            tasks = [
                getattr(self, _TASK_METHOD_MAP[role])()
                for role in strategy.agents_needed
                if role in _TASK_METHOD_MAP
            ]
        else:
            agents = self.agents
            tasks = self.tasks

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )