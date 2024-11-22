from flask import Blueprint, request, jsonify
from ..services.aider_service import AiderService

api_bp = Blueprint('api', __name__)
aider_service = AiderService()

@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """Get list of all active sessions"""
    try:
        sessions = aider_service.list_sessions()
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get status and info about a specific session"""
    try:
        session = aider_service.get_session(session_id)
        return jsonify(session), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """Get chat history for a session"""
    try:
        history = aider_service.get_chat_history(session_id)
        return jsonify({'history': history}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    try:
        session_id = aider_service.create_session()
        return jsonify({'session_id': session_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/chat', methods=['POST'])
def chat(session_id):
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        response = aider_service.process_message(session_id, message)
        return jsonify({'response': response}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
def end_session(session_id):
    try:
        aider_service.end_session(session_id)
        return '', 204
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
