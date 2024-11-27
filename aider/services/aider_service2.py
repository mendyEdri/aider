import uuid
from typing import Dict, Optional
from ..main import Coder, get_parser, InputOutput, Analytics, models
from ..commands import Commands, SwitchCoder
from pathlib import Path
import os
import subprocess

class AiderService2:
    def __init__(self):
        self.sessions: Dict[str, tuple[Coder, Commands]] = {}
        self.parser = get_parser([], None)
        
    def create_session(self, session_args: dict = None) -> str:
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
        
        # Get yes_always value with default True
        yes_always = session_args.get('yes_always', True) if session_args else True
        
        # Initialize IO
        io = InputOutput(
            pretty=session_args.get('pretty', True),
            yes=yes_always,
            input_history_file=None,
            chat_history_file=None
        )
        
        # Initialize Commands first
        commands = Commands(
            io=io,
            coder=None,  # Will be set after coder creation
            voice_language=None,
            verify_ssl=True,
            args=None,
            parser=self.parser,
            verbose=session_args.get('verbose', False)
        )
        
        # Initialize the model
        main_model = models.Model(
            session_args.get('model', "gpt-4"),
            weak_model=session_args.get('weak_model'),
            editor_model=session_args.get('editor_model'),
            editor_edit_format=session_args.get('editor_edit_format')
        )
        
        # Initialize Git repo if git is enabled
        use_git = session_args.get('git', False)
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
        
        # Create Coder instance
        coder = Coder.create(
            main_model=main_model,
            edit_format=session_args.get('edit_format'),
            io=io,
            repo=repo,
            fnames=[],
            analytics=Analytics(),
            commands=commands,  # Pass the commands instance
            use_git=use_git
        )
        
        # Set coder in commands
        commands.coder = coder
        
        # Set the root directory
        coder.root = str(work_path)
        
        # Store both coder and commands
        self.sessions[session_id] = (coder, commands)
        return session_id
    
    def process_message(self, session_id: str, message: str) -> str:
        """Process a message using commands"""
        print(f"DEBUG: process_message called with session_id: {session_id} and message: {message}")
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
            
        coder, commands = self.sessions[session_id]
        
        if message.startswith('/') or message.startswith('!'):
            # Handle command
            print("** command CODE CODE **", message)
            return commands.cmd_code(message)
        else:
            # Handle regular message
            return coder.run(with_message=message)
    
    def end_session(self, session_id: str):
        """End and cleanup a session"""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
            
        coder, commands = self.sessions[session_id]
        commands.cmd_exit("")  # Clean exit
        del self.sessions[session_id]
    
    def execute_command(self, session_id: str, command: str) -> any:
        """Execute a command in the session"""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
            
        coder, commands = self.sessions[session_id]
        return commands.run(command)
    
    def get_command_list(self, session_id: str) -> list:
        """Get list of available commands"""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
            
        _, commands = self.sessions[session_id]
        return commands.get_commands()
    
    def map_project(self, session_id: str) -> dict:
        """Map the project files for a given session"""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
        
        coder, _ = self.sessions[session_id]
        
        try:
            # Force refresh the repo map
            repo_map = coder.get_repo_map(force_refresh=True)
            
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
    
    def run_command(self, session_id: str, command: str) -> dict:
        """Run a shell command"""
        print("session_id", session_id)
        coder, _ = self.sessions.get(session_id)
        print("coder", self.sessions)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the command output
        print("** ROOT **", coder)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=coder.root  # Set the working directory to the coder's root
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode
        }
    
    def cmd_model(self, session_id: str, model_name: str) -> dict:
        """Switch to a new LLM"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_model(model_name)
    
    def cmd_chat_mode(self, session_id: str, mode: str) -> dict:
        """Switch to a new chat mode"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_chat_mode(mode)
    
    def cmd_add(self, session_id: str, files: list) -> dict:
        """Add files to the chat"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        results = []
        for file in files:
            result = commands.cmd_add(file)
            results.append(result)
        return {'results': results}
    
    def cmd_drop(self, session_id: str, files: list = None) -> dict:
        """Remove files from the chat"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_drop(" ".join(files) if files else "")
    
    def cmd_git(self, session_id: str, git_command: str) -> dict:
        """Run a git command"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_git(git_command)
    
    def cmd_test(self, session_id: str, command: str = None) -> dict:
        """Run tests"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_test(command)
    
    def cmd_run(self, session_id: str, command: str, add_on_nonzero_exit: bool = False) -> dict:
        """Run a shell command"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_run(command, add_on_nonzero_exit)
    
    def cmd_ls(self, session_id: str) -> dict:
        """List all files"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the output
        original_tool_output = coder.io.tool_output
        ls_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                ls_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        commands.cmd_ls("")
        coder.io.tool_output = original_tool_output
        
        return {'ls_output': ls_output}
    
    def cmd_tokens(self, session_id: str) -> dict:
        """Get token information"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the output
        original_tool_output = coder.io.tool_output
        token_info = []
        
        def capture_output(*args, **kwargs):
            if args:
                token_info.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        commands.cmd_tokens("")
        coder.io.tool_output = original_tool_output
        
        return {'token_info': token_info}
    
    def cmd_diff(self, session_id: str) -> dict:
        """Show git diff"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the output
        original_tool_output = coder.io.tool_output
        diff_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                diff_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        diff = commands.cmd_diff("")
        coder.io.tool_output = original_tool_output
        
        return {'diff_output': diff}
    
    def cmd_undo(self, session_id: str) -> dict:
        """Undo last git commit"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_undo("")
    
    def cmd_help(self, session_id: str, topic: str = "") -> dict:
        """Get help about aider"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the output
        original_tool_output = coder.io.tool_output
        help_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                help_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        commands.cmd_help(topic)
        coder.io.tool_output = original_tool_output
        
        return {'help_output': help_output}
    
    def cmd_commit(self, session_id: str, message: str = None) -> dict:
        """Commit changes"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_commit(message)
    
    def cmd_clear(self, session_id: str) -> dict:
        """Clear chat history"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        return commands.cmd_clear("")
    
    def cmd_settings(self, session_id: str) -> dict:
        """Get current settings"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
            
        # Capture the output
        original_tool_output = coder.io.tool_output
        settings_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                settings_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        commands.cmd_settings("")
        coder.io.tool_output = original_tool_output
        
        return {'settings_output': settings_output}
    
    def cmd_architect(self, session_id: str, message: str) -> dict:
        """Enter architect mode to discuss high-level design"""
        coder, commands = self.sessions.get(session_id)
        if not coder:
            raise KeyError(f"Session {session_id} not found")
        
        # Capture the output
        original_tool_output = coder.io.tool_output
        architect_output = []
        
        def capture_output(*args, **kwargs):
            if args:
                architect_output.append(str(args[0]))
                
        coder.io.tool_output = capture_output
        
        try:
            # Execute architect command with message
            result = commands.cmd_architect(message)
            
            # Restore original output function
            coder.io.tool_output = original_tool_output
            
            return {
                'result': result,
                'output': architect_output,
                'status': 'success'
            }
        except Exception as e:
            coder.io.tool_output = original_tool_output
            raise Exception(f"Error in architect mode: {str(e)}")