import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
def run():
    """
    Démarre le serveur web Flask.
    """
    print("--------------------------------------------------")
    print("--- Lancement du serveur web pour l'assistant AI ---")
    print("--------------------------------------------------")
    from app import app
    
    print(f"Serveur démarré. Ouvrez votre navigateur à l'adresse : http://127.0.0.1:5001")
    os.chdir(project_root)
    app.run(debug=True, port=5001, host='0.0.0.0')


def train():
    print("La fonction 'train' n'est pas implémentée pour l'application web.")

def replay():
    print("La fonction 'replay' n'est pas implémentée pour l'application web.")

def test():
    print("La fonction 'test' n'est pas implémentée pour l'application web.")   