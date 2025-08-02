from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .tools.custom_tool import AskPatientTool

@CrewBase
class MedicalReportCrew():
    """Crew psychiatrique pour la génération de rapports médicaux"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def interviewer_clinique(self) -> Agent:
        return Agent(
            config=self.agents_config['interviewer_clinique'],
            tools=[AskPatientTool()],
            verbose=True
        )

    @agent
    def analyste_clinique(self) -> Agent:
        return Agent(
            config=self.agents_config['analyste_clinique'], 
            verbose=True
        )

    @agent
    def synthetiseur_diagnostique(self) -> Agent:
        return Agent(
            config=self.agents_config['synthetiseur_diagnostique'], 
            verbose=True
        )

    @agent
    def redacteur_medical(self) -> Agent:
        return Agent(
            config=self.agents_config['redacteur_medical'], 
            verbose=True
        )

    @task
    def tache_entretien_interactif(self) -> Task:
        return Task(
            config=self.tasks_config['tache_entretien_interactif'],
            agent=self.interviewer_clinique()
        )

    @task
    def tache_structuration_dossier(self) -> Task:
        return Task(
            config=self.tasks_config['tache_structuration_dossier'],
            agent=self.analyste_clinique(),
            context=[self.tache_entretien_interactif()]
        )

    @task
    def tache_analyse_diagnostique(self) -> Task:
        return Task(
            config=self.tasks_config['tache_analyse_diagnostique'],
            agent=self.synthetiseur_diagnostique(),
            context=[self.tache_structuration_dossier()]
        )

    @task
    def tache_redaction_rapport_final(self) -> Task:
        return Task(
            config=self.tasks_config['tache_redaction_rapport_final'],
            agent=self.redacteur_medical(),
            context=[self.tache_analyse_diagnostique()],
            output_file='rapport_psychiatrique.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )