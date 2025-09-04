"""Tests for Odoo client based on odooly."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server_odoo.odoo_client import OdooClient, OdooConfig


@pytest.fixture
def odoo_config():
    """Create test Odoo configuration."""
    return OdooConfig(
        url="https://test.odoo.com",
        database="test_db",
        username="test_user",
        password="test_pass",
        timeout=60,
    )


@pytest.fixture
def odoo_client(odoo_config):
    """Create Odoo client with mocked odooly backend."""
    with patch("mcp_server_odoo.odoo_client.OdoolyClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.env = MagicMock()
        mock_client.authenticate = MagicMock(return_value=123)
        client = OdooClient(odoo_config)
        return client


class TestOdooConfig:
    """Test OdooConfig validation."""

    def test_valid_config_with_password(self):
        """Test valid config with password."""
        config = OdooConfig(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert config.password == "test_pass"
        assert config.api_key is None

    def test_valid_config_with_api_key(self):
        """Test valid config with API key."""
        config = OdooConfig(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            api_key="test_key",
        )
        assert config.api_key == "test_key"
        assert config.password is None

    def test_invalid_config_no_auth(self):
        """Test config without password or API key."""
        with pytest.raises(ValueError, match="Either password or api_key must be provided"):
            OdooConfig(
                url="https://test.odoo.com",
                database="test_db",
                username="test_user",
            )


class TestOdooClient:
    """Test OdooClient methods."""

    def test_authenticate_success(self, odoo_client):
        """Test successful authentication."""
        uid = odoo_client.authenticate()
        assert uid == 123
        assert odoo_client.uid == 123
        odoo_client.client.authenticate.assert_called_once()

    def test_authenticate_failure(self, odoo_client):
        """Test authentication failure."""
        odoo_client.client.authenticate.return_value = False
        odoo_client.uid = None
        with pytest.raises(ValueError, match="Authentication failed"):
            odoo_client.authenticate()

    def test_search_records(self, odoo_client):
        """Test search method."""
        model = MagicMock()
        model.search.return_value = [1, 2, 3]
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.search(
            "res.partner",
            [["name", "ilike", "test"]],
            limit=10,
            order="name asc",
        )

        assert result == [1, 2, 3]
        model.search.assert_called_once_with(
            [["name", "ilike", "test"]], offset=0, limit=10, order="name asc"
        )

    def test_search_read(self, odoo_client):
        """Test search_read method."""
        model = MagicMock()
        expected = [
            {"id": 1, "name": "Test Partner 1"},
            {"id": 2, "name": "Test Partner 2"},
        ]
        model.search_read.return_value = expected
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.search_read(
            "res.partner",
            [["active", "=", True]],
            fields=["name", "email"],
            limit=5,
        )

        assert result == expected
        model.search_read.assert_called_once_with(
            [["active", "=", True]],
            offset=0,
            fields=["name", "email"],
            limit=5,
        )

    def test_read_single_record(self, odoo_client):
        """Test reading a single record."""
        model = MagicMock()
        model.read.return_value = [{"id": 1, "name": "Test"}]
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.read("res.partner", 1, ["name"])

        assert result == {"id": 1, "name": "Test"}
        model.read.assert_called_once_with([1], fields=["name"])

    def test_read_multiple_records(self, odoo_client):
        """Test reading multiple records."""
        model = MagicMock()
        expected = [{"id": 1, "name": "Test1"}, {"id": 2, "name": "Test2"}]
        model.read.return_value = expected
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.read("res.partner", [1, 2], ["name"])

        assert result == expected
        model.read.assert_called_once_with([1, 2], fields=["name"])

    def test_create_single_record(self, odoo_client):
        """Test creating a single record."""
        model = MagicMock()
        model.create.return_value = [42]
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.create("res.partner", {"name": "New Partner"})

        assert result == 42
        model.create.assert_called_once_with([{"name": "New Partner"}])

    def test_create_multiple_records(self, odoo_client):
        """Test creating multiple records."""
        model = MagicMock()
        model.create.return_value = [42, 43]
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.create(
            "res.partner",
            [{"name": "Partner 1"}, {"name": "Partner 2"}],
        )

        assert result == [42, 43]
        model.create.assert_called_once_with([{"name": "Partner 1"}, {"name": "Partner 2"}])

    def test_write_records(self, odoo_client):
        """Test updating records."""
        model = MagicMock()
        model.write.return_value = True
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.write(
            "res.partner",
            [1, 2],
            {"active": False},
        )

        assert result is True
        model.write.assert_called_once_with([1, 2], {"active": False})

    def test_unlink_records(self, odoo_client):
        """Test deleting records."""
        model = MagicMock()
        model.unlink.return_value = True
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.unlink("res.partner", [1, 2])

        assert result is True
        model.unlink.assert_called_once_with([1, 2])

    def test_fields_get(self, odoo_client):
        """Test getting field definitions."""
        model = MagicMock()
        expected = {
            "name": {"type": "char", "string": "Name", "required": True},
            "email": {"type": "char", "string": "Email"},
        }
        model.fields_get.return_value = expected
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.fields_get("res.partner", ["name", "email"])

        assert result == expected
        model.fields_get.assert_called_once_with(fields=["name", "email"])

    def test_get_model_list(self, odoo_client):
        """Test getting model list."""
        model = MagicMock()
        expected = [
            {"model": "res.partner", "name": "Contact", "transient": False},
            {"model": "sale.order", "name": "Sales Order", "transient": False},
        ]
        model.search_read.return_value = expected
        odoo_client.env.__getitem__.return_value = model

        result = odoo_client.get_model_list()

        assert result == expected
        model.search_read.assert_called_once_with([], ["model", "name", "transient"])
