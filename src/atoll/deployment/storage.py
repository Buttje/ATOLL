"""Persistent storage for agent metadata and state.

This module provides a lightweight persistent storage layer using JSON files
to store agent metadata, checksums, and deployment state.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentRecord(BaseModel):
    """Persistent record for an agent."""

    name: str
    checksum: str
    path: str
    status: str  # discovered, starting, running, stopped, failed
    port: Optional[int] = None
    pid: Optional[int] = None
    created_at: str
    updated_at: str
    error_message: Optional[str] = None
    restart_count: int = 0
    last_started: Optional[str] = None
    last_stopped: Optional[str] = None


class AgentStorage:
    """Persistent storage for agent records."""

    def __init__(self, storage_path: Path):
        """Initialize storage.

        Args:
            storage_path: Directory to store database files
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Database files
        self.agents_db = storage_path / "agents.json"
        self.checksums_db = storage_path / "checksums.json"
        self.state_db = storage_path / "state.json"

        # In-memory caches
        self._agents: Dict[str, AgentRecord] = {}
        self._checksums: Dict[str, str] = {}
        self._state: Dict[str, any] = {}

        # Load from disk
        self._load()

    def _load(self) -> None:
        """Load all data from disk."""
        # Load agents
        if self.agents_db.exists():
            try:
                with open(self.agents_db) as f:
                    data = json.load(f)
                    self._agents = {
                        name: AgentRecord(**record)
                        for name, record in data.items()
                    }
                logger.info(f"Loaded {len(self._agents)} agent records from storage")
            except Exception as e:
                logger.error(f"Failed to load agents database: {e}")
                self._agents = {}

        # Load checksums
        if self.checksums_db.exists():
            try:
                with open(self.checksums_db) as f:
                    self._checksums = json.load(f)
                logger.info(f"Loaded {len(self._checksums)} checksums from storage")
            except Exception as e:
                logger.error(f"Failed to load checksums database: {e}")
                self._checksums = {}

        # Load state
        if self.state_db.exists():
            try:
                with open(self.state_db) as f:
                    self._state = json.load(f)
                logger.info("Loaded state from storage")
            except Exception as e:
                logger.error(f"Failed to load state database: {e}")
                self._state = {}

    def _save_agents(self) -> None:
        """Save agents to disk."""
        try:
            data = {
                name: record.model_dump()
                for name, record in self._agents.items()
            }
            with open(self.agents_db, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self._agents)} agent records")
        except Exception as e:
            logger.error(f"Failed to save agents database: {e}")

    def _save_checksums(self) -> None:
        """Save checksums to disk."""
        try:
            with open(self.checksums_db, "w") as f:
                json.dump(self._checksums, f, indent=2)
            logger.debug(f"Saved {len(self._checksums)} checksums")
        except Exception as e:
            logger.error(f"Failed to save checksums database: {e}")

    def _save_state(self) -> None:
        """Save state to disk."""
        try:
            with open(self.state_db, "w") as f:
                json.dump(self._state, f, indent=2)
            logger.debug("Saved state")
        except Exception as e:
            logger.error(f"Failed to save state database: {e}")

    # Agent operations

    def add_agent(self, name: str, checksum: str, path: str, status: str = "discovered") -> AgentRecord:
        """Add a new agent record.

        Args:
            name: Agent name
            checksum: Package checksum
            path: Agent directory path
            status: Initial status

        Returns:
            Created agent record
        """
        now = datetime.utcnow().isoformat()
        record = AgentRecord(
            name=name,
            checksum=checksum,
            path=path,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._agents[name] = record
        self._save_agents()
        logger.info(f"Added agent record: {name}")
        return record

    def get_agent(self, name: str) -> Optional[AgentRecord]:
        """Get agent record by name.

        Args:
            name: Agent name

        Returns:
            Agent record if found, None otherwise
        """
        return self._agents.get(name)

    def get_all_agents(self) -> List[AgentRecord]:
        """Get all agent records.

        Returns:
            List of all agent records
        """
        return list(self._agents.values())

    def update_agent(self, name: str, **updates) -> Optional[AgentRecord]:
        """Update agent record.

        Args:
            name: Agent name
            **updates: Fields to update

        Returns:
            Updated agent record if found, None otherwise
        """
        record = self._agents.get(name)
        if not record:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)

        # Update timestamp
        record.updated_at = datetime.utcnow().isoformat()

        self._save_agents()
        logger.debug(f"Updated agent record: {name}")
        return record

    def delete_agent(self, name: str) -> bool:
        """Delete agent record.

        Args:
            name: Agent name

        Returns:
            True if deleted, False if not found
        """
        if name in self._agents:
            del self._agents[name]
            self._save_agents()
            logger.info(f"Deleted agent record: {name}")
            return True
        return False

    def agent_exists(self, name: str) -> bool:
        """Check if agent exists.

        Args:
            name: Agent name

        Returns:
            True if exists
        """
        return name in self._agents

    # Checksum operations

    def get_checksum(self, name: str) -> Optional[str]:
        """Get checksum for agent.

        Args:
            name: Agent name

        Returns:
            Checksum if found, None otherwise
        """
        return self._checksums.get(name)

    def set_checksum(self, name: str, checksum: str) -> None:
        """Set checksum for agent.

        Args:
            name: Agent name
            checksum: Package checksum
        """
        self._checksums[name] = checksum
        self._save_checksums()
        logger.debug(f"Set checksum for {name}: {checksum}")

    def checksum_exists(self, checksum: str) -> Optional[str]:
        """Check if checksum exists and return agent name.

        Args:
            checksum: Checksum to check

        Returns:
            Agent name if checksum exists, None otherwise
        """
        for name, stored_checksum in self._checksums.items():
            if stored_checksum == checksum:
                return name
        return None

    # State operations

    def get_state(self, key: str, default=None):
        """Get state value.

        Args:
            key: State key
            default: Default value if not found

        Returns:
            State value or default
        """
        return self._state.get(key, default)

    def set_state(self, key: str, value) -> None:
        """Set state value.

        Args:
            key: State key
            value: Value to store
        """
        self._state[key] = value
        self._save_state()
        logger.debug(f"Set state: {key}")

    def clear_state(self) -> None:
        """Clear all state."""
        self._state = {}
        self._save_state()
        logger.info("Cleared all state")

    # Bulk operations

    def restore_state(self) -> Dict[str, AgentRecord]:
        """Restore agents from persistent storage on server restart.

        Returns:
            Dictionary of agent records by name
        """
        logger.info(f"Restoring state: {len(self._agents)} agents")
        return self._agents.copy()

    def export_data(self) -> Dict:
        """Export all data for backup.

        Returns:
            Dictionary with all storage data
        """
        return {
            "agents": {name: record.model_dump() for name, record in self._agents.items()},
            "checksums": self._checksums.copy(),
            "state": self._state.copy(),
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_data(self, data: Dict) -> None:
        """Import data from backup.

        Args:
            data: Dictionary with storage data
        """
        try:
            # Import agents
            if "agents" in data:
                self._agents = {
                    name: AgentRecord(**record)
                    for name, record in data["agents"].items()
                }

            # Import checksums
            if "checksums" in data:
                self._checksums = data["checksums"]

            # Import state
            if "state" in data:
                self._state = data["state"]

            # Save to disk
            self._save_agents()
            self._save_checksums()
            self._save_state()

            logger.info("Imported data from backup")
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            raise
