import sys
import warnings

from medical_report.crew import MedicalReportCrew 

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Exécute le crew.
    """

    inputs = {
        'topic': 'Anxiété généralisée et troubles du sommeil' 
    }
    
    try:
        MedicalReportCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Entraîne le crew pour un nombre donné d'itérations.
    """
    inputs = {
        'topic': 'Anxiété généralisée et troubles du sommeil'
    }
    try:
        MedicalReportCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Rejoue l'exécution du crew à partir d'une tâche spécifique.
    """
    try:
        MedicalReportCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Teste l'exécution du crew et retourne les résultats.
    """
    inputs = {
        'topic': 'Anxiété généralisée et troubles du sommeil'
    }
    try:
        MedicalReportCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")