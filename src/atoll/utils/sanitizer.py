"""Log sanitization and secret redaction utilities.

This module provides functions to sanitize logs and diagnostics by removing
sensitive information like API keys, tokens, passwords, and other secrets.
"""

import re
from typing import Dict, List, Pattern

from .logger import get_logger

logger = get_logger(__name__)


# Patterns to detect and redact secrets
SECRET_PATTERNS: List[tuple[Pattern, str]] = [
    # API keys
    (re.compile(r'\b[A-Za-z0-9_-]{32,}\b'), '[REDACTED_API_KEY]'),
    # Bearer tokens
    (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
    # Authorization headers
    (re.compile(r'Authorization:\s*[^\s]+', re.IGNORECASE), 'Authorization: [REDACTED]'),
    # X-API-Key headers
    (re.compile(r'X-API-Key:\s*[^\s]+', re.IGNORECASE), 'X-API-Key: [REDACTED]'),
    # AWS keys
    (re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED_AWS_KEY]'),
    # Generic passwords in URLs
    (re.compile(r'://[^:]+:([^@]+)@', re.IGNORECASE), '://[REDACTED]@'),
    # Password assignments
    (re.compile(r'password\s*[:=]\s*["\']?([^"\'\s]+)', re.IGNORECASE), 'password=[REDACTED]'),
    # Secret assignments
    (re.compile(r'secret\s*[:=]\s*["\']?([^"\'\s]+)', re.IGNORECASE), 'secret=[REDACTED]'),
    # Token assignments
    (re.compile(r'token\s*[:=]\s*["\']?([^"\'\s]+)', re.IGNORECASE), 'token=[REDACTED]'),
    # Private keys (PEM format)
    (re.compile(r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (RSA |EC |OPENSSH )?PRIVATE KEY-----', re.DOTALL), '[REDACTED_PRIVATE_KEY]'),
    # SSH keys
    (re.compile(r'ssh-rsa\s+[A-Za-z0-9+/=]+'), 'ssh-rsa [REDACTED]'),
    # Generic base64 that looks like secrets (at least 40 chars)
    (re.compile(r'\b[A-Za-z0-9+/]{40,}={0,2}\b'), '[REDACTED_SECRET]'),
    # Credit card numbers (basic pattern)
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '[REDACTED_CARD]'),
    # Email addresses (for privacy)
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED_EMAIL]'),
]


# Environment variables that typically contain secrets
SECRET_ENV_VARS = [
    'API_KEY', 'APIKEY', 'SECRET', 'TOKEN', 'PASSWORD', 'PASSWD',
    'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
    'GITHUB_TOKEN', 'GH_TOKEN',
    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
    'DATABASE_URL', 'DB_PASSWORD',
    'PRIVATE_KEY', 'SSH_KEY',
]


def sanitize_text(text: str, additional_patterns: List[tuple[Pattern, str]] = None) -> str:
    """Sanitize text by redacting secrets.

    Args:
        text: Text to sanitize
        additional_patterns: Additional regex patterns to apply

    Returns:
        Sanitized text with secrets redacted

    Examples:
        >>> sanitize_text("password=secret123")
        'password=[REDACTED]'
        >>> sanitize_text("Bearer abc123def456")
        'Bearer [REDACTED_TOKEN]'
    """
    if not text:
        return text

    sanitized = text
    patterns = SECRET_PATTERNS.copy()

    if additional_patterns:
        patterns.extend(additional_patterns)

    for pattern, replacement in patterns:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_dict(data: dict, keys_to_redact: List[str] = None) -> dict:
    """Sanitize dictionary by redacting sensitive keys.

    Args:
        data: Dictionary to sanitize
        keys_to_redact: Additional keys to redact (case-insensitive)

    Returns:
        Sanitized dictionary with sensitive values redacted

    Examples:
        >>> sanitize_dict({"api_key": "secret", "name": "test"})
        {'api_key': '[REDACTED]', 'name': 'test'}
    """
    if not isinstance(data, dict):
        return data

    # Default keys to redact
    redact_keys = [
        'password', 'passwd', 'pwd',
        'secret', 'api_key', 'apikey',
        'token', 'bearer', 'auth',
        'private_key', 'ssh_key',
        'access_key', 'secret_key',
    ]

    if keys_to_redact:
        redact_keys.extend([k.lower() for k in keys_to_redact])

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key should be redacted
        if any(redact_key in key_lower for redact_key in redact_keys):
            sanitized[key] = '[REDACTED]'
        # Recursively sanitize nested dicts
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, keys_to_redact)
        # Sanitize strings
        elif isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        # Keep other values as-is
        else:
            sanitized[key] = value

    return sanitized


def sanitize_env_vars(env: Dict[str, str]) -> Dict[str, str]:
    """Sanitize environment variables dictionary.

    Args:
        env: Environment variables dictionary

    Returns:
        Sanitized environment variables

    Examples:
        >>> sanitize_env_vars({"API_KEY": "secret", "PATH": "/usr/bin"})
        {'API_KEY': '[REDACTED]', 'PATH': '/usr/bin'}
    """
    sanitized = {}

    for key, value in env.items():
        key_upper = key.upper()

        # Check if this is a known secret env var
        if any(secret_key in key_upper for secret_key in SECRET_ENV_VARS):
            sanitized[key] = '[REDACTED]'
        else:
            # Still apply text sanitization
            sanitized[key] = sanitize_text(value)

    return sanitized


def sanitize_command_line(command: str) -> str:
    """Sanitize command line arguments.

    Args:
        command: Command line string

    Returns:
        Sanitized command line

    Examples:
        >>> sanitize_command_line("curl -H 'Authorization: Bearer abc123'")
        "curl -H 'Authorization: [REDACTED]'"
    """
    # First apply general text sanitization
    sanitized = sanitize_text(command)

    # Additional patterns for command line arguments
    cmd_patterns = [
        # --password=value
        (re.compile(r'--password[=\s]+[^\s]+', re.IGNORECASE), '--password=[REDACTED]'),
        # --token=value
        (re.compile(r'--token[=\s]+[^\s]+', re.IGNORECASE), '--token=[REDACTED]'),
        # --api-key=value
        (re.compile(r'--api-key[=\s]+[^\s]+', re.IGNORECASE), '--api-key=[REDACTED]'),
        # -p value, -P value
        (re.compile(r'-[pP]\s+[^\s]+'), '-p [REDACTED]'),
    ]

    for pattern, replacement in cmd_patterns:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_log_line(log_line: str) -> str:
    """Sanitize a single log line.

    Args:
        log_line: Log line to sanitize

    Returns:
        Sanitized log line

    Examples:
        >>> sanitize_log_line("INFO: API key is abc123")
        'INFO: API key is [REDACTED_API_KEY]'
    """
    return sanitize_text(log_line)


def sanitize_logs(logs: str) -> str:
    """Sanitize multi-line logs.

    Args:
        logs: Multi-line log string

    Returns:
        Sanitized logs

    Examples:
        >>> sanitize_logs("Line 1\\npassword=secret\\nLine 3")
        'Line 1\\npassword=[REDACTED]\\nLine 3'
    """
    lines = logs.split('\n')
    sanitized_lines = [sanitize_log_line(line) for line in lines]
    return '\n'.join(sanitized_lines)


def sanitize_diagnostics(diagnostics: dict) -> dict:
    """Sanitize diagnostic information.

    Args:
        diagnostics: Diagnostic data dictionary

    Returns:
        Sanitized diagnostics

    Examples:
        >>> sanitize_diagnostics({"stdout": "password=secret", "config": {"api_key": "123"}})
        {'stdout': 'password=[REDACTED]', 'config': {'api_key': '[REDACTED]'}}
    """
    sanitized = {}

    for key, value in diagnostics.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, str):
            # For stdout/stderr/logs, sanitize as logs
            if key in ('stdout', 'stderr', 'logs', 'output'):
                sanitized[key] = sanitize_logs(value)
            else:
                sanitized[key] = sanitize_text(value)
        elif isinstance(value, list):
            # Sanitize list items if they're strings or dicts
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict)
                else sanitize_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def add_custom_pattern(pattern: str, replacement: str) -> None:
    """Add a custom pattern for secret detection.

    Args:
        pattern: Regular expression pattern
        replacement: Replacement text

    Example:
        >>> add_custom_pattern(r'my_secret_\d+', '[CUSTOM_SECRET]')
    """
    compiled_pattern = re.compile(pattern)
    SECRET_PATTERNS.append((compiled_pattern, replacement))
    logger.info(f"Added custom sanitization pattern: {pattern}")
