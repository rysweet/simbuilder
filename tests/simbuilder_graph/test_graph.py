"""Tests for the shared graph database service."""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from src.scaffolding.exceptions import ConfigurationError
from src.simbuilder_graph.models import SubscriptionNode
from src.simbuilder_graph.models import TenantNode
from src.simbuilder_graph.service import GraphService


class TestTenantNode:
    """Test cases for TenantNode model."""

    def test_tenant_node_creation(self):
        """Test valid tenant node creation."""
        tenant = TenantNode(id="tenant-123", name="Test Tenant")
        assert tenant.id == "tenant-123"
        assert tenant.name == "Test Tenant"

    def test_tenant_node_immutable(self):
        """Test that tenant nodes are immutable."""
        tenant = TenantNode(id="tenant-123", name="Test Tenant")
        with pytest.raises(ValidationError):
            tenant.id = "new-id"  # type: ignore

    def test_tenant_node_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            TenantNode(id="tenant-123", name="Test Tenant", extra="field")  # type: ignore


class TestSubscriptionNode:
    """Test cases for SubscriptionNode model."""

    def test_subscription_node_creation(self):
        """Test valid subscription node creation."""
        subscription = SubscriptionNode(
            id="sub-123",
            tenant_id="tenant-123",
            name="Test Subscription"
        )
        assert subscription.id == "sub-123"
        assert subscription.tenant_id == "tenant-123"
        assert subscription.name == "Test Subscription"

    def test_subscription_node_immutable(self):
        """Test that subscription nodes are immutable."""
        subscription = SubscriptionNode(
            id="sub-123",
            tenant_id="tenant-123",
            name="Test Subscription"
        )
        with pytest.raises(ValidationError):
            subscription.id = "new-id"  # type: ignore

    def test_subscription_node_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            SubscriptionNode(
                id="sub-123",
                tenant_id="tenant-123",
                name="Test Subscription",
                extra="field"  # type: ignore
            )


class TestGraphService:
    """Test cases for GraphService."""

    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration."""
        config = Mock()
        config.graph_db_url = "bolt://localhost:7687"
        return config

    @pytest.fixture
    def service(self, mock_config):
        """Provide a GraphService instance with mock config."""
        return GraphService(config=mock_config)

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_connect_success(self, mock_driver_class, service):
        """Test successful database connection."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_driver.session.return_value = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver.session.return_value.__exit__.return_value = None
        mock_driver_class.return_value = mock_driver

        service.connect()

        assert service._driver is mock_driver
        mock_driver_class.assert_called_once_with("bolt://localhost:7687", auth=("neo4j", "password"))
        mock_session.run.assert_called_once_with("RETURN 1")

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_connect_failure(self, mock_driver_class, service):
        """Test database connection failure."""
        from neo4j.exceptions import ServiceUnavailable
        mock_driver_class.side_effect = ServiceUnavailable("Connection failed")

        with pytest.raises(ConfigurationError, match="Cannot connect to graph database"):
            service.connect()

    def test_connect_no_url(self):
        """Test connection failure when no URL is configured."""
        config = Mock()
        config.graph_db_url = None
        service = GraphService(config=config)

        with pytest.raises(ConfigurationError, match="Graph database URL not configured"):
            service.connect()

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_close(self, mock_driver_class, service):
        """Test closing database connection."""
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        service.close()

        mock_driver.close.assert_called_once()
        assert service._driver is None

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_context_manager(self, mock_driver_class, service):
        """Test using service as context manager."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        with service as s:
            assert s is service
            assert service._driver is mock_driver

        mock_driver.close.assert_called_once()

    def test_session_not_connected(self, service):
        """Test session context manager when not connected."""
        with pytest.raises(ConfigurationError, match="Not connected to database"), service.session():
            pass

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_create_tenant(self, mock_driver_class, service):
        """Test creating a tenant."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        service.create_tenant("tenant-123", "Test Tenant")

        mock_session.run.assert_called_once_with(
            "MERGE (t:Tenant {id: $id}) SET t.name = $name",
            id="tenant-123",
            name="Test Tenant"
        )

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_create_subscription(self, mock_driver_class, service):
        """Test creating a subscription."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        service.create_subscription("sub-123", "tenant-123", "Test Subscription")

        expected_query = """
                MERGE (s:Subscription {id: $sub_id})
                SET s.name = $sub_name, s.tenant_id = $tenant_id
                WITH s
                MATCH (t:Tenant {id: $tenant_id})
                MERGE (t)-[:HAS_SUBSCRIPTION]->(s)
                """
        mock_session.run.assert_called_once_with(
            expected_query,
            sub_id="sub-123",
            sub_name="Test Subscription",
            tenant_id="tenant-123"
        )

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_tenant_exists_true(self, mock_driver_class, service):
        """Test tenant_exists returns True when tenant exists."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 1
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.tenant_exists("tenant-123")

        assert result is True
        mock_session.run.assert_called_once_with(
            "MATCH (t:Tenant {id: $id}) RETURN count(t) as count",
            id="tenant-123"
        )

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_tenant_exists_false(self, mock_driver_class, service):
        """Test tenant_exists returns False when tenant doesn't exist."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 0
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.tenant_exists("tenant-123")

        assert result is False

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_list_subscriptions(self, mock_driver_class, service):
        """Test listing subscriptions for a tenant."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_result = Mock()

        # Mock records
        mock_record1 = MagicMock()
        mock_record1.__getitem__.side_effect = lambda key: {
            "id": "sub-1",
            "name": "Subscription 1",
            "tenant_id": "tenant-123"
        }[key]

        mock_record2 = MagicMock()
        mock_record2.__getitem__.side_effect = lambda key: {
            "id": "sub-2",
            "name": "Subscription 2",
            "tenant_id": "tenant-123"
        }[key]

        mock_result.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.list_subscriptions("tenant-123")

        assert len(result) == 2
        assert result[0].id == "sub-1"
        assert result[0].name == "Subscription 1"
        assert result[1].id == "sub-2"
        assert result[1].name == "Subscription 2"

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_get_node_counts(self, mock_driver_class, service):
        """Test getting node counts."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {"tenant_count": 5, "subscription_count": 12}[key]
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.get_node_counts()

        assert result == {"tenants": 5, "subscriptions": 12}

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_check_connectivity_success(self, mock_driver_class, service):
        """Test successful connectivity check."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 1
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.check_connectivity()

        assert result is True

    def test_check_connectivity_no_driver(self, service):
        """Test connectivity check when no driver is set."""
        result = service.check_connectivity()
        assert result is False

    @patch('src.simbuilder_graph.service.GraphDatabase.driver')
    def test_check_connectivity_exception(self, mock_driver_class, service):
        """Test connectivity check when exception occurs."""
        mock_driver = Mock()
        mock_session = MagicMock()
        mock_session.run.side_effect = Exception("Connection error")
        mock_driver.session.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        service._driver = mock_driver

        result = service.check_connectivity()

        assert result is False


class TestGraphCLI:
    """Test cases for graph CLI commands."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_info_success(self, mock_get_service):
        """Test graph info command success."""
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = True
        mock_service.get_node_counts.return_value = {"tenants": 3, "subscriptions": 7}
        mock_get_service.return_value = mock_service

        # Import the app from scaffolding CLI
        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "info"])

        assert result.exit_code == 0
        assert "✓ Connected" in result.stdout
        assert "3" in result.stdout  # tenant count
        assert "7" in result.stdout  # subscription count

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_info_connection_failure(self, mock_get_service):
        """Test graph info command with connection failure."""
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = False
        mock_get_service.return_value = mock_service

        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "info"])

        assert result.exit_code == 1
        assert "Failed to connect" in result.stdout

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_info_configuration_error(self, mock_get_service):
        """Test graph info command with configuration error."""
        mock_get_service.side_effect = ConfigurationError("Config error")

        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "info"])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_check_success(self, mock_get_service):
        """Test graph check command success."""
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = True
        mock_service.get_node_counts.return_value = {"tenants": 2, "subscriptions": 5}
        mock_get_service.return_value = mock_service

        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "check"])

        assert result.exit_code == 0
        assert "All graph database checks passed!" in result.stdout

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_check_failure(self, mock_get_service):
        """Test graph check command failure."""
        mock_service = MagicMock()
        mock_service.check_connectivity.return_value = False
        mock_get_service.return_value = mock_service

        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "check"])

        assert result.exit_code == 1
        assert "Some graph database checks failed!" in result.stdout

    @patch('src.simbuilder_graph.cli.get_graph_service')
    def test_graph_check_configuration_error(self, mock_get_service):
        """Test graph check command with configuration error."""
        mock_get_service.side_effect = ConfigurationError("Config error")

        from src.scaffolding.cli import app
        result = self.runner.invoke(app, ["graph", "check"])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout
