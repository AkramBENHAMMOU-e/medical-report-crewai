from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class AskPatientInput(BaseModel):
    """Schéma d'input pour l'outil qui pose une question au patient."""
    question: str = Field(..., description="La question exacte à poser au patient.")

class AnalyzeResponseInput(BaseModel):
    """Schéma d'input pour l'outil d'analyse des réponses."""
    patient_response: str = Field(..., description="La réponse du patient à analyser.")
    conversation_context: str = Field(..., description="Le contexte de la conversation jusqu'à présent.")

class AskPatientTool(BaseTool):
    name: str = "Poser une Question au Patient"
    description: str = (
        "Utilisez cet outil pour poser UNE question et obtenir la réponse. "
        "GÉNÉREZ des questions dynamiques en fonction des réponses précédentes. "
        "Après la 10e question répondue, DONNEZ votre Final Answer et n'utilisez plus d'outils."
    )
    args_schema: Type[BaseModel] = AskPatientInput

    def _run(self, question: str) -> str:
        """Pose la question à l'utilisateur dans la console et retourne sa réponse."""
        print("\n---------------------------------")
        print(f"Agent [Interviewer Clinique]: {question}")
        response = input("Votre réponse [Patient]: ")
        print("---------------------------------\n")
        return response

class AnalyzePatientResponseTool(BaseTool):
    name: str = "Analyser la Réponse du Patient"
    description: str = (
        "Analysez la réponse du patient pour déterminer la prochaine question la plus pertinente. "
        "Identifiez les informations manquantes et le domaine à approfondir."
    )
    args_schema: Type[BaseModel] = AnalyzeResponseInput

    def _run(self, patient_response: str, conversation_context: str) -> str:
        return (
            f"Analyse de la réponse: {patient_response[:100]}... - "
            f"Contexte: {conversation_context[:100]}..."
        )