"""Odoo client based on the odooly library."""

import os
import xmlrpc
import ssl
from typing import Any, cast

from pydantic import BaseModel, Field

try:
    from odooly import Client as OdoolyClient  # type: ignore
except Exception:  # pragma: no cover - odooly might not be installed in tests
    OdoolyClient = None  # type: ignore


class CustomClient(OdoolyClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport = CustomTransport()


class CustomTransport(xmlrpc.client.SafeTransport):
    def __init__(self, context=None):
        super().__init__(context)
        self.context = ssl._create_unverified_context()

    def send_headers(self, connection, headers):
        # Get custom header from environment variables
        header_name = os.getenv("ODOO_CUSTOM_HEADER_NAME")
        header_value = os.getenv("ODOO_CUSTOM_HEADER_VALUE")
        
        if header_name and header_value:
            connection.putheader(header_name, header_value)
            super().send_headers(connection, headers)
        else:
            super().send_headers(connection, headers)


class OdooConfig(BaseModel):
    """Configuration for Odoo connection."""
    
    model_config = {"arbitrary_types_allowed": True}

    url: str = Field(..., description="Odoo instance URL")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(..., description="Odoo username (e.g. email)")
    password: str | None = Field(None, description="Odoo password")
    api_key: str | None = Field(None, description="Odoo API key")
    timeout: int = Field(120, description="Request timeout in seconds")
    transport: CustomTransport | None = Field(None, description="Custom transport")

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover - pydantic hook
        """Validate that either password or api_key is provided."""
        if not self.password and not self.api_key:
            raise ValueError("Either password or api_key must be provided")


class OdooClient:
    """Client for interacting with Odoo via the odooly library."""

    def __init__(self, config: OdooConfig) -> None:
        """Initialize Odoo client with configuration."""
        if OdoolyClient is None:  # pragma: no cover - handled in tests
            raise ImportError("odooly is required to use OdooClient")

        self.config = config
        self.url = config.url.rstrip("/")
        self.database = config.database
        self.username = config.username
        self.password = config.api_key or config.password
        self.timeout = config.timeout
        self.uid: int | None = None
        self.transport = config.transport or CustomTransport()
        
        # Initialise odooly client and environment
        self.client = OdoolyClient(
            self.url,
            self.database,
            self.username,
            self.password,
            transport=self.transport,
        )
        self.env = self.client.env

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self) -> int:
        """Authenticate with Odoo and return user ID."""
        if self.uid is None:
            self.uid = self.client.authenticate(
                self.database,
                self.username,
                self.password,
                {},
            )
            if not self.uid:
                raise ValueError("Authentication failed. Check your credentials.")
        return self.uid

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def search(
        self,
        model: str,
        domain: list[list[Any]] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> Any:
        """Search for record IDs matching the domain."""
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order

        return self.env[model].search(domain, **kwargs)

    def search_read(
        self,
        model: str,
        domain: list[list[Any]] | None = None,
        fields: list[str] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> Any:
        """Search and read records in a single call."""
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if fields is not None:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order

        return self.env[model].search_read(domain, **kwargs)

    def read(
        self,
        model: str,
        ids: int | list[int],
        fields: list[str] | None = None,
    ) -> Any:
        """Read records by IDs."""
        if isinstance(ids, int):
            ids = [ids]

        kwargs: dict[str, Any] = {}
        if fields is not None:
            kwargs["fields"] = fields

        result = self.env[model].read(ids, **kwargs)
        return result[0] if len(ids) == 1 else result

    def create(
        self,
        model: str,
        values: dict[str, Any] | list[dict[str, Any]],
    ) -> Any:
        """Create one or more records."""
        single_record = isinstance(values, dict)
        if single_record:
            values_to_create = [cast(dict[str, Any], values)]
        else:
            values_to_create = cast(list[dict[str, Any]], values)

        result = self.env[model].create(values_to_create)
        return result[0] if single_record else result

    def write(
        self,
        model: str,
        ids: int | list[int],
        values: dict[str, Any],
    ) -> Any:
        """Update records."""
        if isinstance(ids, int):
            ids = [ids]

        return self.env[model].write(ids, values)

    def unlink(
        self,
        model: str,
        ids: int | list[int],
    ) -> Any:
        """Delete records."""
        if isinstance(ids, int):
            ids = [ids]

        return self.env[model].unlink(ids)

    def fields_get(
        self,
        model: str,
        fields: list[str] | None = None,
        attributes: list[str] | None = None,
    ) -> Any:
        """Get field definitions for a model."""
        kwargs: dict[str, Any] = {}
        if fields is not None:
            kwargs["fields"] = fields
        if attributes is not None:
            kwargs["attributes"] = attributes

        return self.env[model].fields_get(**kwargs)

    def get_model_list(self) -> Any:
        """Get list of all available models."""
        return self.env["ir.model"].search_read([], ["model", "name", "transient"])
