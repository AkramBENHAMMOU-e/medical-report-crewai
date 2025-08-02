from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class AskPatientInput(BaseModel):
    """Schéma d'input pour l'outil qui pose une question au patient."""
    question: str = Field(..., description="La question exacte à poser au patient.")

class AskPatientTool(BaseTool):
    name: str = "Poser une Question au Patient"
    description: str = (
        "Utilisez cet outil pour poser une seule question au patient et obtenir sa réponse. "
        "C'est le seul moyen que vous avez pour communiquer avec le patient."
    )
    args_schema: Type[BaseModel] = AskPatientInput

    def _run(self, question: str) -> str:
        """Pose la question à l'utilisateur dans la console et retourne sa réponse."""

        print("\n---------------------------------")
        print(f"Agent [Interviewer Clinique]: {question}")
       
        response = input("Votre réponse [Patient]: ")
        print("---------------------------------\n")
        
        return response