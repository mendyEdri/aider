import uuid
from typing import Dict, Optional
from ..main import Coder, get_parser, InputOutput, Analytics
from pathlib import Path

class AiderService:
    def __init__(self):
        self.sessions: Dict[str, Coder] = {}
        self.parser = get_parser([], None)
        
    def create_session(self, session_args: dict = None) -> str:
        """Create a new Aider session with optional arguments"""
        session_id = str(uuid.uuid4())
        
        # Convert dict to list of args, handling special cases
        arg_list = []
        if session_args:
            for key, value in session_args.items():
                # Skip yes_always as it's handled separately
                if key == 'yes_always':
                    continue
                    
                if isinstance(value, bool):
                    if value:
                        arg_list.append(f"--{key}")
                else:
                    arg_list.append(f"--{key}")
                    arg_list.append(str(value))
        
        # Initialize with provided or default settings
        args = self.parser.parse_args(arg_list)
        io = InputOutput(
            pretty=args.pretty if hasattr(args, 'pretty') else False,
            input_history_file=args.input_history_file if hasattr(args, 'input_history_file') else None,
            chat_history_file=args.chat_history_file if hasattr(args, 'chat_history_file') else None
        )
        
        analytics = Analytics()
        
        coder = Coder.create(
            main_model="gpt-4",
            io=io,
            repo=None,
            fnames=[],
            analytics=analytics,
            commands=None,
            use_git=False
        )
        
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
