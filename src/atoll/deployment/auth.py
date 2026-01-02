"""Authentication and security for ATOLL Deployment Server API.

This module provides API key and token-based authentication using FastAPI
dependency injection. Authentication can be enabled/disabled via configuration.
"""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthConfig(BaseModel):
    """Authentication configuration."""

    enabled: bool = False
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    auth_header_name: str = "X-API-Key"

    def __init__(self, **data):
        """Initialize auth config with environment variables."""
        # Check environment variables
        if "api_key" not in data or data["api_key"] is None:
            data["api_key"] = os.getenv("ATOLL_API_KEY")

        if "bearer_token" not in data or data["bearer_token"] is None:
            data["bearer_token"] = os.getenv("ATOLL_BEARER_TOKEN")

        # Enable auth if key or token is set
        if "enabled" not in data:
            data["enabled"] = bool(data.get("api_key") or data.get("bearer_token"))

        super().__init__(**data)


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, auth_config: AuthConfig):
        """Initialize API key auth.

        Args:
            auth_config: Authentication configuration
        """
        self.config = auth_config
        self.api_key_header = APIKeyHeader(
            name=auth_config.auth_header_name,
            auto_error=False,
        )

    async def __call__(self, api_key: Optional[str] = Depends(lambda: None)) -> bool:
        """Verify API key.

        Args:
            api_key: API key from header

        Returns:
            True if authenticated

        Raises:
            HTTPException: If authentication fails
        """
        if not self.config.enabled:
            return True

        # Get API key from header via dependency injection
        from fastapi import Request

        async def get_api_key(request: Request) -> Optional[str]:
            return request.headers.get(self.config.auth_header_name)

        api_key_header = Depends(get_api_key)

        if not self.config.api_key:
            logger.warning("API key authentication enabled but no key configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication misconfigured",
            )

        if not api_key or not secrets.compare_digest(api_key, self.config.api_key):
            logger.warning(f"Invalid API key attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return True


class BearerTokenAuth:
    """Bearer token authentication handler."""

    def __init__(self, auth_config: AuthConfig):
        """Initialize bearer token auth.

        Args:
            auth_config: Authentication configuration
        """
        self.config = auth_config
        self.bearer_scheme = HTTPBearer(auto_error=False)

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
    ) -> bool:
        """Verify bearer token.

        Args:
            credentials: Bearer token credentials

        Returns:
            True if authenticated

        Raises:
            HTTPException: If authentication fails
        """
        if not self.config.enabled:
            return True

        if not self.config.bearer_token:
            logger.warning("Bearer token authentication enabled but no token configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication misconfigured",
            )

        if not credentials or not credentials.credentials:
            logger.warning("Missing bearer token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not secrets.compare_digest(credentials.credentials, self.config.bearer_token):
            logger.warning("Invalid bearer token attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return True


def verify_api_key_or_token(api_key: str, bearer_token: str, config: AuthConfig) -> bool:
    """Verify either API key or bearer token.

    Args:
        api_key: API key from header
        bearer_token: Bearer token from Authorization header
        config: Authentication configuration

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    if not config.enabled:
        return True

    # Try API key first
    if config.api_key and api_key:
        if secrets.compare_digest(api_key, config.api_key):
            return True

    # Try bearer token
    if config.bearer_token and bearer_token:
        if secrets.compare_digest(bearer_token, config.bearer_token):
            return True

    # Neither worked
    logger.warning("Authentication failed - invalid credentials")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        Random 32-byte hex string suitable for API key

    Example:
        >>> key = generate_api_key()
        >>> len(key)
        64
    """
    return secrets.token_hex(32)


def generate_bearer_token() -> str:
    """Generate a secure random bearer token.

    Returns:
        Random URL-safe token suitable for bearer auth

    Example:
        >>> token = generate_bearer_token()
        >>> len(token) >= 32
        True
    """
    return secrets.token_urlsafe(32)


# Dependency for FastAPI routes
def get_auth_dependency(auth_config: AuthConfig):
    """Create authentication dependency for FastAPI routes.

    Args:
        auth_config: Authentication configuration

    Returns:
        FastAPI dependency function

    Example:
        >>> config = AuthConfig(enabled=True, api_key="secret")
        >>> auth_dep = get_auth_dependency(config)
        >>> # Use in FastAPI route:
        >>> # @app.get("/protected", dependencies=[Depends(auth_dep)])
    """
    if not auth_config.enabled:
        # Return a dependency that always succeeds
        async def no_auth():
            return True

        return no_auth

    # Return authentication dependency based on config
    if auth_config.bearer_token:
        return BearerTokenAuth(auth_config)
    elif auth_config.api_key:
        return APIKeyAuth(auth_config)
    else:
        logger.warning("Authentication enabled but no credentials configured")
        async def auth_error():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication misconfigured",
            )
        return auth_error
