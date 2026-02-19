"""FalkorDB integration for Mahabharatha MQL queries."""

import os
from typing import Any

from falkordb import FalkorDB

from mahabharatha.logging import get_logger

logger = get_logger("db")


class ZergDB:
    """Interface for FalkorDB operations."""

    def __init__(
        self, host: str = "localhost", port: int = 6379, username: str | None = None, password: str | None = None
    ):
        """Initialize the FalkorDB connection.

        Args:
            host: DB host
            port: DB port
            username: DB username
            password: DB password
        """
        self.host = os.environ.get("Mahabharatha_DB_HOST", host)
        self.port = int(os.environ.get("Mahabharatha_DB_PORT", port))
        self.username = os.environ.get("Mahabharatha_DB_USERNAME", username)
        self.password = os.environ.get("Mahabharatha_DB_PASSWORD", password)

        self.db = FalkorDB(host=self.host, port=self.port, username=self.username, password=self.password)
        self.graph = None

    def select_graph(self, graph_name: str):
        """Select a graph to work with."""
        self.graph = self.db.select_graph(graph_name)

    def query(self, cypher_query: str, params: dict[str, Any] | None = None) -> list[Any]:
        """Execute a Cypher (MQL) query.

        Args:
            cypher_query: The Cypher query string
            params: Optional parameters for the query

        Returns:
            Result set from the query
        """
        if not self.graph:
            raise RuntimeError("No graph selected. Call select_graph first.")

        try:
            logger.debug(f"Executing MQL: {cypher_query}")
            return self.graph.query(cypher_query, params).result_set
        except Exception as e:
            logger.error(f"MQL query failed: {e}")
            raise


def get_db(graph_name: str = "mahabharatha") -> ZergDB:
    """Helper to get a ZergDB instance with a default graph selected."""
    db = ZergDB()
    db.select_graph(graph_name)
    return db
