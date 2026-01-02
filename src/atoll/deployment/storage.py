"""Persistent storage for agent metadata using SQLite.

This module provides a lightweight database for storing agent deployment
metadata including status, ports, timestamps, and configuration.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AgentMetadataStore:
    """SQLite-based persistent storage for agent metadata."""

    def __init__(self, db_path: Path):
        """Initialize metadata store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()
        logger.info(f"Agent metadata store initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic commit/rollback.

        Yields:
            SQLite connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _initialize_db(self):
        """Create database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create agents table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    name TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config_path TEXT NOT NULL,
                    port INTEGER,
                    pid INTEGER,
                    deployed_at TEXT NOT NULL,
                    started_at TEXT,
                    stopped_at TEXT,
                    restart_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    stdout_log TEXT,
                    stderr_log TEXT,
                    exit_code INTEGER,
                    health_status TEXT DEFAULT 'unknown',
                    last_health_check TEXT,
                    metadata TEXT
                )
            """
            )

            # Create deployment history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS deployment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    result TEXT NOT NULL,
                    duration_seconds REAL,
                    error_message TEXT,
                    FOREIGN KEY (agent_name) REFERENCES agents(name)
                )
            """
            )

            # Create indices for common queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_agents_checksum ON agents(checksum)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_agent ON deployment_history(agent_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON deployment_history(timestamp)"
            )

    def save_agent(self, agent_data: dict[str, Any]) -> bool:
        """Save or update agent metadata.

        Args:
            agent_data: Dictionary with agent metadata

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Convert metadata dict to JSON if present
                metadata_json = None
                if "metadata" in agent_data and agent_data["metadata"]:
                    metadata_json = json.dumps(agent_data["metadata"])

                # Upsert agent record
                cursor.execute(
                    """
                    INSERT INTO agents (
                        name, checksum, status, config_path, port, pid,
                        deployed_at, started_at, stopped_at, restart_count,
                        error_message, stdout_log, stderr_log, exit_code,
                        health_status, last_health_check, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        checksum=excluded.checksum,
                        status=excluded.status,
                        config_path=excluded.config_path,
                        port=excluded.port,
                        pid=excluded.pid,
                        started_at=excluded.started_at,
                        stopped_at=excluded.stopped_at,
                        restart_count=excluded.restart_count,
                        error_message=excluded.error_message,
                        stdout_log=excluded.stdout_log,
                        stderr_log=excluded.stderr_log,
                        exit_code=excluded.exit_code,
                        health_status=excluded.health_status,
                        last_health_check=excluded.last_health_check,
                        metadata=excluded.metadata
                """,
                    (
                        agent_data["name"],
                        agent_data["checksum"],
                        agent_data["status"],
                        str(agent_data["config_path"]),
                        agent_data.get("port"),
                        agent_data.get("pid"),
                        agent_data.get("deployed_at", datetime.now().isoformat()),
                        agent_data.get("started_at"),
                        agent_data.get("stopped_at"),
                        agent_data.get("restart_count", 0),
                        agent_data.get("error_message"),
                        agent_data.get("stdout_log"),
                        agent_data.get("stderr_log"),
                        agent_data.get("exit_code"),
                        agent_data.get("health_status", "unknown"),
                        agent_data.get("last_health_check"),
                        metadata_json,
                    ),
                )

            logger.debug(f"Saved agent metadata: {agent_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to save agent metadata: {e}")
            return False

    def get_agent(self, name: str) -> Optional[dict[str, Any]]:
        """Get agent metadata by name.

        Args:
            name: Agent name

        Returns:
            Agent metadata dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE name = ?", (name,))
                row = cursor.fetchone()

                if row:
                    agent_data = dict(row)
                    # Parse metadata JSON
                    if agent_data.get("metadata"):
                        agent_data["metadata"] = json.loads(agent_data["metadata"])
                    return agent_data
                return None

        except Exception as e:
            logger.error(f"Failed to get agent metadata: {e}")
            return None

    def get_all_agents(self) -> list[dict[str, Any]]:
        """Get all agent metadata.

        Returns:
            List of agent metadata dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents ORDER BY deployed_at DESC")
                rows = cursor.fetchall()

                agents = []
                for row in rows:
                    agent_data = dict(row)
                    if agent_data.get("metadata"):
                        agent_data["metadata"] = json.loads(agent_data["metadata"])
                    agents.append(agent_data)

                return agents

        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            return []

    def get_agents_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get agents filtered by status.

        Args:
            status: Agent status (discovered, running, stopped, failed)

        Returns:
            List of agent metadata dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM agents WHERE status = ? ORDER BY deployed_at DESC",
                    (status,),
                )
                rows = cursor.fetchall()

                agents = []
                for row in rows:
                    agent_data = dict(row)
                    if agent_data.get("metadata"):
                        agent_data["metadata"] = json.loads(agent_data["metadata"])
                    agents.append(agent_data)

                return agents

        except Exception as e:
            logger.error(f"Failed to get agents by status: {e}")
            return []

    def get_agent_by_checksum(self, checksum: str) -> Optional[dict[str, Any]]:
        """Get agent by package checksum.

        Args:
            checksum: MD5 checksum

        Returns:
            Agent metadata dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE checksum = ?", (checksum,))
                row = cursor.fetchone()

                if row:
                    agent_data = dict(row)
                    if agent_data.get("metadata"):
                        agent_data["metadata"] = json.loads(agent_data["metadata"])
                    return agent_data
                return None

        except Exception as e:
            logger.error(f"Failed to get agent by checksum: {e}")
            return None

    def delete_agent(self, name: str) -> bool:
        """Delete agent metadata.

        Args:
            name: Agent name

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM agents WHERE name = ?", (name,))
                logger.info(f"Deleted agent metadata: {name}")
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to delete agent metadata: {e}")
            return False

    def record_deployment(
        self,
        agent_name: str,
        checksum: str,
        action: str,
        result: str,
        duration: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Record deployment action in history.

        Args:
            agent_name: Agent name
            checksum: Package checksum
            action: Action performed (deploy, start, stop, restart)
            result: Result (success, failure, cached)
            duration: Duration in seconds
            error_message: Error message if failed

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO deployment_history (
                        agent_name, checksum, action, timestamp, result,
                        duration_seconds, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        agent_name,
                        checksum,
                        action,
                        datetime.now().isoformat(),
                        result,
                        duration,
                        error_message,
                    ),
                )
                logger.debug(f"Recorded deployment history: {agent_name} - {action}")
                return True

        except Exception as e:
            logger.error(f"Failed to record deployment history: {e}")
            return False

    def get_deployment_history(
        self, agent_name: Optional[str] = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get deployment history.

        Args:
            agent_name: Filter by agent name (optional)
            limit: Maximum number of records

        Returns:
            List of deployment history records
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if agent_name:
                    cursor.execute(
                        """
                        SELECT * FROM deployment_history
                        WHERE agent_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """,
                        (agent_name, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM deployment_history
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """,
                        (limit,),
                    )

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get deployment history: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Count agents by status
                cursor.execute(
                    "SELECT status, COUNT(*) as count FROM agents GROUP BY status"
                )
                status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

                # Total deployments
                cursor.execute("SELECT COUNT(*) as count FROM deployment_history")
                total_deployments = cursor.fetchone()["count"]

                # Recent failures
                cursor.execute(
                    """
                    SELECT COUNT(*) as count FROM deployment_history
                    WHERE result = 'failure'
                    AND datetime(timestamp) > datetime('now', '-24 hours')
                """
                )
                recent_failures = cursor.fetchone()["count"]

                return {
                    "total_agents": sum(status_counts.values()),
                    "status_counts": status_counts,
                    "total_deployments": total_deployments,
                    "failures_last_24h": recent_failures,
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
