# src/investigador_financiero_app/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai import LLM
import os


@CrewBase
class ResearchCrew():
    """Crew para investigación financiera y creación de informes"""
    
    # def __init__(self):
    #     # LLM para el researcher
    #      # OpenAI para agentes que usan herramientas
    #     self.openai_llm = LLM(
    #         model="gpt-4o-mini",
    #         api_key=os.getenv("OPENAI_API_KEY")
    #     )
        
    #     self.deepseek_chat = LLM(
    #         model="deepseek/deepseek-chat",
    #         base_url="https://api.deepseek.com",
    #         api_key=os.getenv("DEEPSEEK_API_KEY")
    #     )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[SerperDevTool()],
            #llm=self.openai_llm
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            verbose=True,
            #llm=self.deepseek_chat
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task']
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task']
        )

    @crew
    def crew(self) -> Crew:
        """Crea la crew para investigación financiera y creación de informes"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )