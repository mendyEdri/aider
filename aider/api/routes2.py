from flask import Blueprint, request, jsonify
from ..services.aider_service2 import AiderService2

api_bp = Blueprint('api/v2', __name__)
aider_service = AiderService2()

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new session"""
    try:
        session_args = request.json if request.json else {}
        session_id = aider_service.create_session(session_args)
        return jsonify({'session_id': session_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/chat', methods=['POST'])
def chat(session_id):
    """Send a message or command to the session"""
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

@api_bp.route('/sessions/<session_id>/command', methods=['POST'])
def execute_command(session_id):
    """Execute a specific command in the session"""
    try:
        command = request.json.get('command')
        if not command:
            return jsonify({'error': 'Command is required'}), 400
            
        result = aider_service.execute_command(session_id, command)
        return jsonify({'result': result}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/commands', methods=['GET'])
def list_commands(session_id):
    """Get list of available commands for the session"""
    try:
        commands = aider_service.get_command_list(session_id)
        return jsonify({'commands': commands}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
def end_session(session_id):
    """End and cleanup a session"""
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

@api_bp.route('/sessions/<session_id>/map2', methods=['POST'])
def map_project_via_command(session_id):
    """Map the project structure and files using the map command"""
    try:
        # Get coder and commands from the service
        if session_id not in aider_service.sessions:
            return jsonify({'error': 'Session not found'}), 404
            
        coder, commands = aider_service.sessions[session_id]
        
        # Capture the map output
        original_tool_output = coder.io.tool_output
        map_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                map_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        
        # Execute the map command
        commands.cmd_map("")
        
        # Restore original output function
        coder.io.tool_output = original_tool_output
        print("** map_output **", map_output)
        return jsonify({
            'map_output': map_output,
            'root': str(coder.root),
            'files': {
                'all_files': sorted(list(coder.get_all_relative_files())),
                'chat_files': sorted(list(coder.get_inchat_relative_files())),
                'addable_files': sorted(list(coder.get_addable_relative_files()))
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/model', methods=['POST'])
def change_model(session_id):
    """Switch to a new LLM"""
    try:
        model_name = request.json.get('model')
        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400
            
        result = aider_service.cmd_model(session_id, model_name)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/chat-mode', methods=['POST'])
def change_chat_mode(session_id):
    """Switch to a new chat mode"""
    try:
        mode = request.json.get('mode')
        if not mode:
            return jsonify({'error': 'Chat mode is required'}), 400
            
        result = aider_service.cmd_chat_mode(session_id, mode)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/add', methods=['POST'])
def add_files(session_id):
    """Add files to the chat"""
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({'error': 'Files list is required'}), 400
            
        result = aider_service.cmd_add(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/drop', methods=['POST'])
def drop_files(session_id):
    """Remove files from the chat"""
    try:
        files = request.json.get('files', [])
        result = aider_service.cmd_drop(session_id, files)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/git', methods=['POST'])
def git_command(session_id):
    """Run a git command"""
    try:
        command = request.json.get('command')
        if not command:
            return jsonify({'error': 'Git command is required'}), 400
            
        result = aider_service.cmd_git(session_id, command)
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
        result = aider_service.cmd_test(session_id, command)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/ls', methods=['GET'])
def list_files(session_id):
    """List all files"""
    try:
        result = aider_service.cmd_ls(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/tokens', methods=['GET'])
def get_tokens(session_id):
    """Get token information"""
    try:
        result = aider_service.cmd_tokens(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/diff', methods=['GET'])
def get_diff(session_id):
    """Show git diff"""
    try:
        result = aider_service.cmd_diff(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/undo', methods=['POST'])
def undo_commit(session_id):
    """Undo last git commit"""
    try:
        result = aider_service.cmd_undo(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/help', methods=['GET'])
def get_help(session_id):
    """Get help about aider"""
    try:
        topic = request.args.get('topic', '')
        result = aider_service.cmd_help(session_id, topic)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/commit', methods=['POST'])
def commit_changes(session_id):
    """Commit changes"""
    try:
        message = request.json.get('message')
        result = aider_service.cmd_commit(session_id, message)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/clear', methods=['POST'])
def clear_history(session_id):
    """Clear chat history"""
    try:
        result = aider_service.cmd_clear(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/settings', methods=['GET'])
def get_settings(session_id):
    """Get current settings"""
    try:
        result = aider_service.cmd_settings(session_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/code', methods=['POST'])
def code_command(session_id):
    """Ask for changes to your code"""
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        result = aider_service.execute_command(session_id, f"/code {message}")
        return jsonify({'result': result}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/ask', methods=['POST'])
def ask_command(session_id):
    """Ask questions about the code base without editing"""
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        result = aider_service.execute_command(session_id, f"/ask {message}")
        return jsonify({'result': result}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/architect', methods=['POST'])
def architect_command(session_id):
    """Enter architect mode to discuss high-level design"""
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        result = aider_service.execute_command(session_id, f"/architect {message}")
        return jsonify({'result': result}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/commands', methods=['POST'])
def execute_generic_command(session_id):
    """Execute any aider command"""
    try:
        command = request.json.get('command')
        if not command:
            return jsonify({'error': 'Command is required'}), 400
            
        result = aider_service.execute_command(session_id, command)
        return jsonify({'result': result}), 200
    except KeyError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500