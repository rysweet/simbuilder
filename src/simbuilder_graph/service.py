"""Neo4j graph database service for SimBuilder."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from neo4j import Driver
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError
from neo4j.exceptions import ServiceUnavailable

from src.scaffolding.exceptions import ConfigurationError
from src.tenant_discovery.config import TenantDiscoverySettings
from src.tenant_discovery.config import get_td_settings

from .models import SubscriptionNode
from .models import TenantNode

logger = logging.getLogger(__name__)


class GraphService:
    """Neo4j graph database service for tenant and subscription management."""

    def __init__(self, config: TenantDiscoverySettings | None = None):
        """Initialize the graph service.

        Args:
            config: Optional configuration instance. If not provided, loads from environment.
        """
        self.config = config or get_td_settings()
        self._driver: Driver | None = None

    def connect(self) -> None:
        """Establish connection to Neo4j database.

        Raises:
            ConfigurationError: If connection cannot be established
        """
        try:
            # Extract connection details from graph_db_url
            url = self.config.graph_db_url
            if not url:
                raise ConfigurationError("Graph database URL not configured")

            # For now, use default credentials - in production this would come from config
            self._driver = GraphDatabase.driver(url, auth=("neo4j", "password"))

            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")

            logger.info("Successfully connected to Neo4j database")

        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConfigurationError(f"Cannot connect to graph database: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise ConfigurationError(f"Graph database connection error: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self) -> Generator[Any, None, None]:
        """Context manager for database sessions.

        Yields:
            Session: Neo4j session instance

        Raises:
            ConfigurationError: If not connected to database
        """
        if not self._driver:
            raise ConfigurationError("Not connected to database. Call connect() first.")

        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def __enter__(self) -> "GraphService":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def create_tenant(self, id: str, name: str) -> None:
        """Create a new tenant node.

        Args:
            id: Unique tenant identifier
            name: Tenant display name
        """
        tenant = TenantNode(id=id, name=name)

        with self.session() as session:
            session.run(
                "MERGE (t:Tenant {id: $id}) SET t.name = $name",
                id=tenant.id,
                name=tenant.name
            )

        logger.info(f"Created/updated tenant: {id}")

    def create_subscription(self, id: str, tenant_id: str, name: str) -> None:
        """Create a new subscription node and link to tenant.

        Args:
            id: Unique subscription identifier
            tenant_id: Associated tenant identifier
            name: Subscription display name
        """
        subscription = SubscriptionNode(id=id, tenant_id=tenant_id, name=name)

        with self.session() as session:
            # Create subscription and relationship to tenant
            session.run(
                """
                MERGE (s:Subscription {id: $sub_id})
                SET s.name = $sub_name, s.tenant_id = $tenant_id
                WITH s
                MATCH (t:Tenant {id: $tenant_id})
                MERGE (t)-[:HAS_SUBSCRIPTION]->(s)
                """,
                sub_id=subscription.id,
                sub_name=subscription.name,
                tenant_id=subscription.tenant_id
            )

        logger.info(f"Created/updated subscription: {id} for tenant: {tenant_id}")

    def tenant_exists(self, id: str) -> bool:
        """Check if a tenant exists.

        Args:
            id: Tenant identifier to check

        Returns:
            bool: True if tenant exists, False otherwise
        """
        with self.session() as session:
            result = session.run(
                "MATCH (t:Tenant {id: $id}) RETURN count(t) as count",
                id=id
            )
            record = result.single()
            return record["count"] > 0 if record else False

    def list_subscriptions(self, tenant_id: str) -> list[SubscriptionNode]:
        """List all subscriptions for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            list[SubscriptionNode]: List of subscription nodes
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (t:Tenant {id: $tenant_id})-[:HAS_SUBSCRIPTION]->(s:Subscription)
                RETURN s.id as id, s.name as name, s.tenant_id as tenant_id
                """,
                tenant_id=tenant_id
            )

            subscriptions = []
            for record in result:
                subscriptions.append(SubscriptionNode(
                    id=record["id"],
                    name=record["name"],
                    tenant_id=record["tenant_id"]
                ))

            return subscriptions

    def get_node_counts(self) -> dict[str, int]:
        """Get count of nodes in the database.

        Returns:
            dict: Dictionary with node counts
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (t:Tenant)
                WITH count(t) as tenant_count
                MATCH (s:Subscription)
                RETURN tenant_count, count(s) as subscription_count
                """
            )
            record = result.single()
            if record:
                return {
                    "tenants": record["tenant_count"],
                    "subscriptions": record["subscription_count"]
                }
            return {"tenants": 0, "subscriptions": 0}

    def check_connectivity(self) -> bool:
        """Check database connectivity.

        Returns:
            bool: True if connected and functional, False otherwise
        """
        try:
            if not self._driver:
                return False

            with self.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                return record["test"] == 1 if record else False

        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False
