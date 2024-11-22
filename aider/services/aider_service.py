import uuid
from typing import Dict, Optional
from ..main import Coder, get_parser, InputOutput, Analytics
from pathlib import Path

class AiderService:
    def __init__(self):
        self.sessions: Dict[str, Coder] = {}
        self.parser = get_parser([], None)
        
    def create_session(self) -> str:
        """Create a new Aider session"""
        session_id = str(uuid.uuid4())
        
        # Initialize with default settings
        args = self.parser.parse_args([])
        io = InputOutput(
            pretty=False,
            yes_always=True,
            input_history_file=None,
            chat_history_file=None
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
