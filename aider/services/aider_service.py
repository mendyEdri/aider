import uuid
from typing import Dict, Optional
from ..main import Coder, get_parser, InputOutput, Analytics, models
from pathlib import Path
import os
import subprocess

class AiderService:
    def __init__(self):
        self.sessions: Dict[str, Coder] = {}
        self.parser = get_parser([], None)
        
    def create_session(self, session_args: dict = None) -> str:
        print("** create_session **", session_args)
        """Create a new Aider session with optional arguments"""
        print(f"DEBUG: create_session called with args: {session_args}")
        session_id = str(uuid.uuid4())
        
        # Get working directory from args or use default generated directory
        work_dir = session_args.get('work_dir')
        work_path = Path(work_dir).resolve()
    
        # Create the generated directory if it doesn't exist
        try:
            work_path.mkdir(parents=True, exist_ok=True)
            print(f"DEBUG: Created or verified directory: {work_path}")
        except Exception as e:
            raise ValueError(f"Failed to create directory {work_dir}: {str(e)}")
            
        print(f"DEBUG: Using work directory: {work_path}")
        
        # Convert dict to list of args, handling special cases
        arg_list = []
        print(f"DEBUG: Converting session_args to arg_list")
        if session_args:
            for key, value in session_args.items():
                if not isinstance(key, str) or key == 'work_dir':  # Skip work_dir as we handle it separately
                    continue
                    
                # Skip yes_always as it's handled separately
                if key == 'yes_always':
                    continue
                    
                # Convert key to command line format
                cmd_key = str(key).replace('_', '-')
                
                if isinstance(value, bool):
                    if value:
                        arg_list.append(f"--{cmd_key}")
                elif value is not None:
                    arg_list.append(f"--{cmd_key}")
                    arg_list.append(str(value))
        
        # Initialize with provided or default settings
        args = self.parser.parse_args(arg_list)
        
        # Get yes_always value with default True
        yes_always = session_args.get('yes_always', True) if session_args else True
        
        io = InputOutput(
            pretty=args.pretty if hasattr(args, 'pretty') else False,
            yes=yes_always,  # Set yes parameter for auto-confirmation
            input_history_file=args.input_history_file if hasattr(args, 'input_history_file') else None,
            chat_history_file=args.chat_history_file if hasattr(args, 'chat_history_file') else None
        )
        
        analytics = Analytics()
        
        # Initialize the model with proper configuration
        main_model = models.Model(
            args.model if hasattr(args, 'model') else "gpt-4",
            weak_model=args.weak_model if hasattr(args, 'weak_model') else None,
            editor_model=args.editor_model if hasattr(args, 'editor_model') else None,
            editor_edit_format=args.editor_edit_format if hasattr(args, 'editor_edit_format') else None,
        )
        
        # Initialize Git repo if git is enabled
        use_git = session_args.get('git', False)
        print(f"DEBUG: use_git: {use_git}")
        repo = None
        if use_git:
            try:
                from ..repo import GitRepo
                repo = GitRepo(
                    io,
                    [],  # empty fnames list initially
                    str(work_path),  # pass work_path as git_root
                    models=main_model.commit_message_models(),
                )
            except Exception as e:
                print(f"Failed to initialize git repo: {e}")
                # Continue without git if initialization fails
        
        coder = Coder.create(
            main_model=main_model,
            edit_format=args.edit_format if hasattr(args, 'edit_format') else None,
            io=io,
            repo=repo,  # Pass the initialized repo
            fnames=[],  # Don't pass the work directory as a file
            analytics=analytics,
            commands=None,
            use_git=use_git
        )
        
        # Set the root directory explicitly
        coder.root = str(work_path)
        
        self.sessions[session_id] = coder
        return session_id
    
    def process_message(self, session_id: str, message: str) -> str:
        """Process a message in an existing session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Run the message through the coder
        response = coder.run(with_message=message)
        return response
        
    def end_session(self, session_id: str):
        """End and cleanup a session"""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
            
        del self.sessions[session_id]
    
    def map_project(self, session_id: str) -> dict:
        """Map the project files for a given session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        try:
            # Force refresh the repo map
            repo_map = coder.get_repo_map()
            
            # Get all files in the project and convert to list
            all_files = list(coder.get_all_relative_files())
            
            # Get files currently in chat and convert to list
            chat_files = list(coder.get_inchat_relative_files())
            
            # Get files that can be added and convert to list
            addable_files = list(coder.get_addable_relative_files())
            
            return {
                'repo_map': repo_map,
                'all_files': sorted(all_files),  # Sort for consistent output
                'chat_files': sorted(chat_files),
                'addable_files': sorted(addable_files),
                'root': str(coder.root)
            }
        except Exception as e:
            raise Exception(f"Error mapping project: {str(e)}")
    
    def add_files(self, session_id: str, files: list) -> dict:
        """Add files to the chat session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        added_files = []
        for file in files:
            try:
                coder.commands.cmd_add(file)
                added_files.append(file)
            except Exception as e:
                print(f"Error adding file {file}: {e}")
                
        return {'added_files': added_files}
    
    def drop_files(self, session_id: str, files: list) -> dict:
        """Remove files from the chat session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        dropped_files = []
        for file in files:
            try:
                coder.commands.cmd_drop(file)
                dropped_files.append(file)
            except Exception as e:
                print(f"Error dropping file {file}: {e}")
                
        return {'dropped_files': dropped_files}
    
    def list_files(self, session_id: str) -> dict:
        """List all files in the session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        chat_files = list(coder.get_inchat_relative_files())
        all_files = list(coder.get_all_relative_files())
        addable_files = list(coder.get_addable_relative_files())
        read_only_files = [coder.get_rel_fname(f) for f in coder.abs_read_only_fnames]
        
        return {
            'chat_files': sorted(chat_files),
            'all_files': sorted(all_files),
            'addable_files': sorted(addable_files),
            'read_only_files': sorted(read_only_files)
        }
    
    def add_readonly_files(self, session_id: str, files: list) -> dict:
        """Add read-only files to the chat session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        added_files = []
        for file in files:
            try:
                coder.commands.cmd_read_only(file)
                added_files.append(file)
            except Exception as e:
                print(f"Error adding read-only file {file}: {e}")
                
        return {'added_readonly_files': added_files}
    
    def get_tokens(self, session_id: str) -> dict:
        """Get token usage information"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the token information that would normally be printed
        original_tool_output = coder.io.tool_output
        token_info = []
        
        def capture_output(*args, **kwargs):
            if args:
                token_info.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        coder.commands.cmd_tokens("")
        coder.io.tool_output = original_tool_output
        
        return {'token_info': token_info}
    
    def change_model(self, session_id: str, model: str) -> dict:
        """Change the model for the session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        try:
            coder.commands.cmd_model(model)
            return {'status': 'success', 'model': model}
        except Exception as e:
            raise Exception(f"Error changing model: {str(e)}")
    
    def get_settings(self, session_id: str) -> dict:
        """Get current settings for the session"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the settings that would normally be printed
        original_tool_output = coder.io.tool_output
        settings_info = []
        
        def capture_output(*args, **kwargs):
            if args:
                settings_info.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        coder.commands.cmd_settings("")
        coder.io.tool_output = original_tool_output
        
        return {'settings': settings_info}
    
    def clear_history(self, session_id: str) -> dict:
        """Clear chat history"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        coder.commands.cmd_clear("")
        return {'status': 'success'}
    
    def reset_session(self, session_id: str) -> dict:
        """Reset session (clear history and drop all files)"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        coder.commands.cmd_reset("")
        return {'status': 'success'}
    
    def run_command(self, session_id: str, command: str) -> dict:
        """Run a shell command"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the command output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode
        }
    
    def run_lint(self, session_id: str, files: list = None) -> dict:
        """Run linter on files"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the lint output
        original_tool_output = coder.io.tool_output
        lint_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                lint_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        coder.commands.cmd_lint("", files)
        coder.io.tool_output = original_tool_output
        
        return {'lint_output': lint_output}
    
    def run_test(self, session_id: str, command: str = None) -> dict:
        """Run tests"""
        coder = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the test output
        original_tool_output = coder.io.tool_output
        test_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                test_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        coder.commands.cmd_test(command)
        coder.io.tool_output = original_tool_output
        
        return {'test_output': test_output}
    
    def create_session_with_coder(self, coder, session_args: dict = None) -> str:
        """Create a new session with an existing coder instance"""
        session_id = str(uuid.uuid4())
        
        # Get working directory from args or use default
        if session_args and 'work_dir' in session_args:
            work_dir = session_args.get('work_dir')
            work_path = Path(work_dir).resolve()
            # Create the directory if it doesn't exist
            try:
                work_path.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Created or verified directory: {work_path}")
            except Exception as e:
                raise ValueError(f"Failed to create directory {work_dir}: {str(e)}")
            
            # Set the root directory explicitly
            coder.root = str(work_path)
        
        self.sessions[session_id] = coder
        return session_id
