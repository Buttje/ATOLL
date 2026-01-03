"""Prometheus metrics for ATOLL Deployment Server.

This module provides observability metrics for monitoring agent deployments,
API requests, and system health.
"""

import logging
from typing import Optional

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Provide no-op implementations if prometheus not installed
    class Counter:
        def __init__(self, *_args, **_kwargs):
            pass

        def inc(self, *_args, **_kwargs):
            pass

        def labels(self, *_args, **_kwargs):
            return self

    class Gauge:
        def __init__(self, *_args, **_kwargs):
            pass

        def set(self, *_args, **_kwargs):
            pass

        def inc(self, *_args, **_kwargs):
            pass

        def dec(self, *_args, **_kwargs):
            pass

        def labels(self, *_args, **_kwargs):
            return self

    class Histogram:
        def __init__(self, *_args, **_kwargs):
            pass

        def observe(self, *_args, **_kwargs):
            pass

        def labels(self, *_args, **_kwargs):
            return self

        def time(self):
            class Timer:
                def __enter__(self):
                    pass

                def __exit__(self, *args):
                    pass

            return Timer()

    class Info:
        def __init__(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

    def generate_latest(*_args, **_kwargs):
        return b"# Prometheus client not installed\n"

    CONTENT_TYPE_LATEST = "text/plain"


logger = logging.getLogger(__name__)


class ATOLLMetrics:
    """Prometheus metrics for ATOLL Deployment Server."""

    def __init__(self):
        """Initialize metrics collectors."""
        # Info metric - system information
        self.atoll_info = Info("atoll_info", "ATOLL Deployment Server information")
        self.atoll_info.info(
            {
                "version": "2.0.0",
                "prometheus_enabled": str(PROMETHEUS_AVAILABLE).lower(),
            }
        )

        # Agent metrics
        self.agents_total = Gauge(
            "atoll_agents_total",
            "Total number of agents",
            ["status"],  # discovered, running, stopped, failed
        )

        self.agent_deployments_total = Counter(
            "atoll_agent_deployments_total",
            "Total number of agent deployments",
            ["result"],  # success, failure, cached
        )

        self.agent_starts_total = Counter(
            "atoll_agent_starts_total", "Total number of agent start attempts", ["result"]
        )

        self.agent_stops_total = Counter(
            "atoll_agent_stops_total", "Total number of agent stop requests"
        )

        self.agent_restarts_total = Counter(
            "atoll_agent_restarts_total", "Total number of agent restart requests"
        )

        self.agent_failures_total = Counter(
            "atoll_agent_failures_total",
            "Total number of agent failures",
            ["agent_name", "reason"],
        )

        # API metrics
        self.api_requests_total = Counter(
            "atoll_api_requests_total",
            "Total number of API requests",
            ["method", "endpoint", "status"],
        )

        self.api_request_duration_seconds = Histogram(
            "atoll_api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
        )

        # Authentication metrics
        self.auth_attempts_total = Counter(
            "atoll_auth_attempts_total", "Total authentication attempts", ["result"]
        )

        # Resource metrics
        self.allocated_ports = Gauge(
            "atoll_allocated_ports_total", "Number of allocated ports"
        )

        self.active_processes = Gauge(
            "atoll_active_processes_total", "Number of active agent processes"
        )

        # Deployment metrics
        self.deployment_duration_seconds = Histogram(
            "atoll_deployment_duration_seconds",
            "Agent deployment duration in seconds",
            ["stage"],  # extraction, venv_creation, dependency_installation, total
        )

        self.venv_operations_total = Counter(
            "atoll_venv_operations_total",
            "Virtual environment operations",
            ["operation", "result"],
        )

        # Health metrics
        self.health_checks_total = Counter(
            "atoll_health_checks_total", "Total health check requests", ["status"]
        )

        # Checksum cache metrics
        self.checksum_cache_hits = Counter(
            "atoll_checksum_cache_hits_total", "Number of checksum cache hits"
        )

        self.checksum_cache_misses = Counter(
            "atoll_checksum_cache_misses_total", "Number of checksum cache misses"
        )

        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "prometheus-client not installed. Metrics will not be collected. "
                "Install with: pip install atoll[monitoring]"
            )
        else:
            logger.info("Prometheus metrics initialized")

    def update_agent_counts(self, status_counts: dict[str, int]):
        """Update agent count gauges.

        Args:
            status_counts: Dictionary mapping status to count
        """
        for status, count in status_counts.items():
            self.agents_total.labels(status=status).set(count)

    def record_deployment(self, result: str, duration: Optional[float] = None):
        """Record an agent deployment.

        Args:
            result: Deployment result (success, failure, cached)
            duration: Deployment duration in seconds
        """
        self.agent_deployments_total.labels(result=result).inc()
        if duration is not None:
            self.deployment_duration_seconds.labels(stage="total").observe(duration)

    def record_agent_start(self, result: str):
        """Record an agent start attempt.

        Args:
            result: Result (success, failure)
        """
        self.agent_starts_total.labels(result=result).inc()

    def record_agent_failure(self, agent_name: str, reason: str):
        """Record an agent failure.

        Args:
            agent_name: Name of the failed agent
            reason: Failure reason
        """
        self.agent_failures_total.labels(agent_name=agent_name, reason=reason).inc()

    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record an API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            status: HTTP status code
            duration: Request duration in seconds
        """
        self.api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_auth_attempt(self, result: str):
        """Record an authentication attempt.

        Args:
            result: Result (success, failure)
        """
        self.auth_attempts_total.labels(result=result).inc()

    def set_allocated_ports(self, count: int):
        """Set the number of allocated ports.

        Args:
            count: Number of allocated ports
        """
        self.allocated_ports.set(count)

    def set_active_processes(self, count: int):
        """Set the number of active processes.

        Args:
            count: Number of active processes
        """
        self.active_processes.set(count)


# Global metrics instance
_metrics: Optional[ATOLLMetrics] = None


def get_metrics() -> ATOLLMetrics:
    """Get or create global metrics instance.

    Returns:
        Global ATOLLMetrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = ATOLLMetrics()
    return _metrics


def is_prometheus_available() -> bool:
    """Check if prometheus_client is available.

    Returns:
        True if prometheus_client is installed
    """
    return PROMETHEUS_AVAILABLE


def get_metrics_content() -> tuple[bytes, str]:
    """Get Prometheus metrics in exposition format.

    Returns:
        Tuple of (metrics content, content type)
    """
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
    else:
        return b"# Prometheus client not installed\n", "text/plain"
