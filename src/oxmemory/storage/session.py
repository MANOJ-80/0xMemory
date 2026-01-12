"""Session Data Manager.

Handles reading, writing, and organizing chat sessions in the brain.
Sessions are stored as JSON files in .0xmemory/sessions/.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from oxmemory.core.models import Session, Message
from oxmemory.core.config import get_brain_path


class SessionManager:
    """Manages chat sessions."""
    
    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize the Session manager.
        
        Args:
            project_dir: Project directory.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.brain_path = get_brain_path(self.project_dir)
        self.sessions_dir = self.brain_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
    def create_session(self, title: str = "New Session", metadata: dict = None) -> Session:
        """Create a new session.
        
        Args:
            title: Session title.
            metadata: Optional metadata.
            
        Returns:
            Created Session object.
        """
        session = Session(
            title=title,
            metadata=metadata or {}
        )
        self.save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.
        
        Args:
            session_id: Session ID.
            
        Returns:
            Session object if found, None otherwise.
        """
        if not session_id.endswith(".json"):
            file_path = self.sessions_dir / f"{session_id}.json"
        else:
            file_path = self.sessions_dir / session_id
            
        if not file_path.exists():
            return None
            
        try:
            data = json.loads(file_path.read_text())
            return Session(**data)
        except (json.JSONDecodeError, Exception):
            return None
            
    def save_session(self, session: Session) -> None:
        """Save a session to disk.
        
        Args:
            session: Session to save.
        """
        file_path = self.sessions_dir / f"{session.id}.json"
        
        # Update timestamp
        session.updated_at = datetime.now()
        
        # Serialize to JSON with datetime handling
        data = session.model_dump(mode="json")
        file_path.write_text(json.dumps(data, indent=2))
        
    def add_message(self, session_id: str, message: Message) -> bool:
        """Add a message to a session.
        
        Args:
            session_id: Session to add to.
            message: Message object.
            
        Returns:
            True if successful.
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.messages.append(message)
        self.save_session(session)
        return True
        
    def list_sessions(self) -> list[Session]:
        """List all sessions.
        
        Returns:
            List of sessions sorted by update time (newest first).
        """
        sessions = []
        for file_path in self.sessions_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                sessions.append(Session(**data))
            except Exception:
                continue
                
        # Sort by updated_at desc
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
        
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            True if deleted.
        """
        file_path = self.sessions_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
