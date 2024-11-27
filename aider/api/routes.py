from flask import Blueprint, request, jsonify
from ..services.aider_service import AiderService
from ..main import main  # Import main function

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
    """Create a new session using the main entrypoint"""
    try:
        session_args = request.json if request.json else {}
        print(f"DEBUG: /sessions POST received args: {session_args}")
        
        # Convert session_args to command line arguments
        argv = []
            
        # Add model argument
        model = session_args.get('model', 'anthropic/claude-3-sonnet-20240229')
        argv.extend(['--model', model])
        
        # Add boolean flags
        if session_args.get('yes_always', True):
            argv.append('--yes-always')
        if session_args.get('pretty', True):
            argv.append('--pretty')
        if session_args.get('auto_commits', True):
            argv.append('--auto-commits')
            
        # Add edit format
        edit_format = session_args.get('edit-format', 'diff')
        argv.extend(['--edit-format', edit_format])
        
        # Always disable git for API usage
        # argv.append('--no-git')
        
        print(f"DEBUG: Created argv: {argv}")
        
        # Create coder instance using main
        coder = main(argv=argv, input=None, output=None, return_coder=True)
        if not coder:
            return jsonify({'error': 'Failed to create coder instance'}), 400
            
        # Create session using the coder instance
        # session_id = aider_service.create_session_with_coder(coder, session_args)
        session_id = aider_service.create_session(session_args)
        
        return jsonify({'session_id': session_id}), 201
    except Exception as e:
        print(f"Error creating session: {str(e)}")
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

@api_bp.route('/sessions/<session_id>/map', methods=['POST'])
def map_project(session_id):
    """Map the project structure and files"""
    try:
        project_map = aider_service.map_project(session_id)
        return jsonify(project_map), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/add', methods=['POST'])
def add_files(session_id):
    """Add files to the chat session"""
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({'error': 'Files list is required'}), 400
            
        result = aider_service.add_files(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/drop', methods=['POST'])
def drop_files(session_id):
    """Remove files from the chat session"""
    try:
        files = request.json.get('files', [])
        result = aider_service.drop_files(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/ls', methods=['GET'])
def list_files(session_id):
    """List all files in the session"""
    try:
        files = aider_service.list_files(session_id)
        return jsonify(files), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/read-only', methods=['POST'])
def add_readonly_files(session_id):
    """Add read-only files to the chat session"""
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({'error': 'Files list is required'}), 400
            
        result = aider_service.add_readonly_files(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/tokens', methods=['GET'])
def get_tokens(session_id):
    """Get token usage information"""
    try:
        tokens = aider_service.get_tokens(session_id)
        return jsonify(tokens), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/model', methods=['POST'])
def change_model(session_id):
    """Change the model for the session"""
    try:
        model = request.json.get('model')
        if not model:
            return jsonify({'error': 'Model name is required'}), 400
            
        result = aider_service.change_model(session_id, model)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/settings', methods=['GET'])
def get_settings(session_id):
    """Get current settings for the session"""
    try:
        settings = aider_service.get_settings(session_id)
        return jsonify(settings), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/clear', methods=['POST'])
def clear_history(session_id):
    """Clear chat history"""
    try:
        result = aider_service.clear_history(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/reset', methods=['POST'])
def reset_session(session_id):
    """Reset session (clear history and drop all files)"""
    try:
        result = aider_service.reset_session(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/run', methods=['POST'])
def run_command(session_id):
    """Run a shell command"""
    try:
        command = request.json.get('command')
        if not command:
            return jsonify({'error': 'Command is required'}), 400
            
        result = aider_service.run_command(session_id, command)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/lint', methods=['POST'])
def run_lint(session_id):
    """Run linter on files"""
    try:
        files = request.json.get('files', [])
        result = aider_service.run_lint(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/test', methods=['POST'])
def run_test(session_id):
    """Run tests"""
    try:
        command = request.json.get('command')
        result = aider_service.run_test(session_id, command)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
