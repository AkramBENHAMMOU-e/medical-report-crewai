# Fichier : app.py (CORRIGÉ AVEC TÉLÉCHARGEMENT PDF MODERNE)

# --- DÉBUT DE LA CORRECTION ---
import sys
import os

# Ajoute le dossier 'src' au chemin de Python pour trouver nos modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# --- FIN DE LA CORRECTION ---

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from medical_report.crew import MedicalReportCrew
from medical_report.pdf_generator import ModernPDFGenerator
import queue
import threading
import uuid
import tempfile
import os
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

# Ce dictionnaire stockera l'état de chaque session utilisateur.
# Pour une vraie application, on utiliserait une base de données comme Redis.
sessions = {}

# Initialiser le générateur PDF
pdf_generator = ModernPDFGenerator()

# --- Modification du Tool pour communiquer avec le web ---
# Nous allons "patcher" la méthode _run de notre outil au démarrage.

from medical_report.tools.custom_tool import AskPatientTool

def web_ask_patient_run(self, question: str) -> str:
    """Version web de la méthode _run du tool avec limite stricte de 10 questions."""
    session_id = threading.current_thread().name
    
    if session_id not in sessions:
        logger.error(f"Session {session_id} non trouvée dans web_ask_patient_run")
        return "Erreur: session non trouvée"

    # Initialiser le compteur si absent
    if 'question_count' not in sessions[session_id]:
        sessions[session_id]['question_count'] = 0

    # Si la limite est atteinte, informer l'agent de conclure
    if sessions[session_id]['question_count'] >= 10:
        logger.info(f"Session {session_id}: Limite de 10 questions atteinte")
        raise RuntimeError(
            "MAX_QUESTIONS_REACHED: Vous avez atteint 10 questions. "
            "Donnez immédiatement votre Final Answer (la transcription complète) et n'utilisez plus d'outils."
        )

    # Incrémenter le compteur et pousser la question au frontend
    sessions[session_id]['question_count'] += 1
    current_num = sessions[session_id]['question_count']
    logger.info(f"[Session {session_id}] Question {current_num}/10: {question[:80]}")
    
    # Mettre la question dans la file d'attente pour que le frontend la récupère
    sessions[session_id]['question_queue'].put(question)
    
    # Attendre que le frontend fournisse une réponse avec timeout
    try:
        answer = sessions[session_id]['answer_queue'].get(timeout=60)
        return answer
    except queue.Empty:
        logger.error(f"Timeout en attendant la réponse pour session {session_id}")
        return "Pas de réponse reçue"

# On remplace la méthode originale par notre version web
AskPatientTool._run = web_ask_patient_run


# --- Routes de l'API ---

@app.route('/')
def index():
    """Sert la page HTML principale."""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_crew():
    """Démarre une nouvelle session de crew."""
    try:
        session_id = str(uuid.uuid4())
        topic = request.json.get('topic', 'Consultation générale')

        logger.info(f"Démarrage de session {session_id} avec topic: {topic}")

        sessions[session_id] = {
            'question_queue': queue.Queue(),
            'answer_queue': queue.Queue(),
            'thread': None,
            'result': None,
            'report_file': None,
            'question_count': 0,
            'status': 'starting'
        }

        # Lancer le crew dans un thread séparé
        thread = threading.Thread(
            target=run_crew_for_session,
            args=(session_id, topic),
            name=session_id,
            daemon=True  # Le thread se termine quand le processus principal se termine
        )
        sessions[session_id]['thread'] = thread
        thread.start()

        # Attendre la première question
        try:
            first_question = sessions[session_id]['question_queue'].get(timeout=30)
            sessions[session_id]['status'] = 'active'
            return jsonify({
                'session_id': session_id,
                'question': first_question
            })
        except queue.Empty:
            logger.error(f"Timeout en attendant la première question pour session {session_id}")
            return jsonify({'error': 'Timeout en attendant la première question'}), 500

    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {str(e)}")
        return jsonify({'error': f'Erreur lors du démarrage: {str(e)}'}), 500


@app.route('/chat', methods=['POST'])
def handle_chat():
    """Reçoit la réponse de l'utilisateur et renvoie la question suivante."""
    session_id = request.json.get('session_id')
    answer = request.json.get('answer')

    logger.info(f"Réponse reçue pour session {session_id}: {str(answer)[:50]}...")
    
    if session_id not in sessions:
        logger.error(f"Session invalide: {session_id}")
        return jsonify({'error': 'Session invalide'}), 400

    # Fournir la réponse à l'agent qui attend
    sessions[session_id]['answer_queue'].put(answer)

    # Attendre la question suivante ou le résultat final
    try:
        next_question = sessions[session_id]['question_queue'].get(timeout=120)  # Augmenté le timeout
        if next_question is None:
            # Le crew a terminé
            logger.info(f"Crew terminé pour session {session_id}")
            sessions[session_id]['thread'].join()  # S'assurer que le thread est terminé
            final_report = sessions[session_id]['result']

            logger.info(f"Rapport final généré pour session {session_id}: {len(str(final_report))} caractères")

            # Générer le PDF moderne
            if final_report:
                pdf_file = pdf_generator.generate_pdf(str(final_report), session_id)
                if pdf_file:
                    sessions[session_id]['report_file'] = pdf_file
                    logger.info(f"PDF moderne généré: {pdf_file}")
                else:
                    logger.error("Erreur lors de la génération du PDF")

            return jsonify({'report': str(final_report), 'session_id': session_id})
        else:
            logger.info(f"Question suivante pour session {session_id}: {next_question[:50]}...")
        return jsonify({'question': next_question})
    except queue.Empty:
        logger.error(f"Timeout pour la question suivante de session {session_id}")
        # Si plus de questions, le crew a probablement fini.
        sessions[session_id]['thread'].join()  # S'assurer que le thread est terminé
        final_report = sessions[session_id]['result']

        logger.info(f"Rapport final (timeout) pour session {session_id}: {len(str(final_report))} caractères")

        # Générer le PDF moderne
        if final_report:
            pdf_file = pdf_generator.generate_pdf(str(final_report), session_id)
            if pdf_file:
                sessions[session_id]['report_file'] = pdf_file
                logger.info(f"PDF moderne généré (timeout): {pdf_file}")
            else:
                logger.error("Erreur lors de la génération du PDF (timeout)")

        return jsonify({'report': str(final_report), 'session_id': session_id})

@app.route('/download/<session_id>')
def download_report(session_id):
    """Télécharge le rapport PDF généré."""
    logger.info(f"Demande de téléchargement PDF pour session {session_id}")

    if session_id not in sessions:
        logger.error(f"Session invalide pour téléchargement: {session_id}")
        return jsonify({'error': 'Session invalide'}), 400

    report_file = sessions[session_id].get('report_file')
    if not report_file or not os.path.exists(report_file):
        logger.error(f"Fichier PDF non trouvé: {report_file}")
        return jsonify({'error': 'Rapport PDF non disponible'}), 404

    try:
        logger.info(f"Téléchargement du PDF: {report_file}")
        return send_file(
            report_file,
            as_attachment=True,
            download_name=f'rapport_psychiatrique_{session_id[:8]}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement PDF: {str(e)}")
        return jsonify({'error': f'Erreur lors du téléchargement: {str(e)}'}), 500

@app.route('/cleanup/<session_id>', methods=['POST'])
def cleanup_session(session_id):
    """Nettoie les fichiers temporaires d'une session."""
    logger.info(f"Nettoyage de la session {session_id}")

    if session_id in sessions:
        report_file = sessions[session_id].get('report_file')
        if report_file and os.path.exists(report_file):
            try:
                os.unlink(report_file)
                logger.info(f"Fichier PDF temporaire supprimé: {report_file}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier: {str(e)}")
        del sessions[session_id]
        logger.info(f"Session {session_id} supprimée")
    return jsonify({'success': True})


def run_crew_for_session(session_id, topic):
    """Fonction exécutée dans le thread pour faire tourner le crew."""
    try:
        logger.info(f"Démarrage du crew pour session {session_id} avec topic: {topic}")
        crew = MedicalReportCrew().crew()
        result = crew.kickoff(inputs={'topic': topic})
        sessions[session_id]['result'] = result
        logger.info(f"Crew terminé pour session {session_id}, résultat: {len(str(result))} caractères")
        # Mettre un signal de fin dans la file d'attente au cas où le frontend attendrait toujours
        sessions[session_id]['question_queue'].put(None) 
    except Exception as e:
        logger.error(f"Erreur dans le crew pour session {session_id}: {str(e)}")
        # En cas d'erreur, on met un message d'erreur dans la file d'attente
        error_message = f"Une erreur est survenue pendant l'exécution du crew: {e}"
        sessions[session_id]['question_queue'].put(error_message)
        sessions[session_id]['result'] = error_message


if __name__ == '__main__':
    app.run(debug=True, port=5001)