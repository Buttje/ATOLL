# Observability & Monitoring Guide

This guide explains how to monitor ATOLL Deployment Server using Prometheus metrics, structured logging, and health checks.

## Table of Contents
1. [Prometheus Metrics](#prometheus-metrics)
2. [Configuration](#configuration)
3. [Available Metrics](#available-metrics)
4. [Integration Examples](#integration-examples)
5. [Grafana Dashboards](#grafana-dashboards)

---

## Prometheus Metrics

ATOLL v2.0 exposes Prometheus-compatible metrics for monitoring agent deployments, API performance, and system health.

### Installation

Metrics support is optional. Install with:

```bash
# Install with monitoring support
pip install atoll[monitoring]

# Or install prometheus-client separately
pip install prometheus-client>=0.19.0
```

### Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `/health` | No | Health check + feature flags |
| `/metrics` | No | Prometheus metrics (exposition format) |

---

## Configuration

### Enable Metrics

Metrics are automatically enabled when `prometheus-client` is installed:

```bash
# Check if metrics are enabled
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "auth_enabled": true,
  "metrics_enabled": true
}
```

### Prometheus Scraping

Configure Prometheus to scrape ATOLL metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'atoll_deployment'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
```

---

## Available Metrics

### System Information

**`atoll_info`** (Info)
- Server version and configuration

```
atoll_info{version="2.0.0", prometheus_enabled="true"} 1
```

### Agent Metrics

**`atoll_agents_total`** (Gauge)
- Total number of agents by status

Labels: `status` (discovered, running, stopped, failed)

```
atoll_agents_total{status="running"} 3
atoll_agents_total{status="stopped"} 1
atoll_agents_total{status="failed"} 0
```

**`atoll_agent_deployments_total`** (Counter)
- Total agent deployments

Labels: `result` (success, failure, cached)

```
atoll_agent_deployments_total{result="success"} 15
atoll_agent_deployments_total{result="cached"} 7
atoll_agent_deployments_total{result="failure"} 2
```

**`atoll_agent_starts_total`** (Counter)
- Agent start attempts

Labels: `result` (success, failure)

**`atoll_agent_stops_total`** (Counter)
- Agent stop requests

**`atoll_agent_restarts_total`** (Counter)
- Agent restart requests

**`atoll_agent_failures_total`** (Counter)
- Agent failures by reason

Labels: `agent_name`, `reason`

```
atoll_agent_failures_total{agent_name="ghidra", reason="port_conflict"} 1
```

### API Metrics

**`atoll_api_requests_total`** (Counter)
- Total API requests

Labels: `method`, `endpoint`, `status`

```
atoll_api_requests_total{method="POST", endpoint="/deploy", status="200"} 45
atoll_api_requests_total{method="POST", endpoint="/start", status="500"} 3
```

**`atoll_api_request_duration_seconds`** (Histogram)
- API request latency

Labels: `method`, `endpoint`

Buckets: 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0

```
atoll_api_request_duration_seconds_bucket{method="POST", endpoint="/deploy", le="1.0"} 38
atoll_api_request_duration_seconds_sum{method="POST", endpoint="/deploy"} 124.5
atoll_api_request_duration_seconds_count{method="POST", endpoint="/deploy"} 45
```

### Authentication Metrics

**`atoll_auth_attempts_total`** (Counter)
- Authentication attempts

Labels: `result` (success, failure)

### Resource Metrics

**`atoll_allocated_ports_total`** (Gauge)
- Number of allocated ports

**`atoll_active_processes_total`** (Gauge)
- Number of active agent processes

### Deployment Metrics

**`atoll_deployment_duration_seconds`** (Histogram)
- Deployment operation duration

Labels: `stage` (extraction, venv_creation, dependency_installation, total)

**`atoll_venv_operations_total`** (Counter)
- Virtual environment operations

Labels: `operation` (create, delete), `result` (success, failure)

### Health & Cache Metrics

**`atoll_health_checks_total`** (Counter)
- Health check requests

Labels: `status` (success, failure)

**`atoll_checksum_cache_hits_total`** (Counter)
- Checksum cache hits (duplicate deployments detected)

**`atoll_checksum_cache_misses_total`** (Counter)
- Checksum cache misses (new deployments)

---

## Integration Examples

### Querying Metrics

**Health Check:**
```bash
curl http://localhost:8080/health
```

**Raw Metrics:**
```bash
curl http://localhost:8080/metrics
```

**Filter Specific Metrics:**
```bash
curl http://localhost:8080/metrics | grep atoll_agent
```

### Prometheus Queries

**Agent Status Distribution:**
```promql
sum by (status) (atoll_agents_total)
```

**Deployment Success Rate:**
```promql
rate(atoll_agent_deployments_total{result="success"}[5m]) / 
rate(atoll_agent_deployments_total[5m])
```

**API Request Rate (requests/second):**
```promql
rate(atoll_api_requests_total[1m])
```

**Average API Latency:**
```promql
rate(atoll_api_request_duration_seconds_sum[5m]) / 
rate(atoll_api_request_duration_seconds_count[5m])
```

**P95 Deployment Duration:**
```promql
histogram_quantile(0.95, 
  rate(atoll_deployment_duration_seconds_bucket{stage="total"}[5m])
)
```

**Failed Agents:**
```promql
atoll_agents_total{status="failed"} > 0
```

**Authentication Failure Rate:**
```promql
rate(atoll_auth_attempts_total{result="failure"}[5m])
```

---

## Grafana Dashboards

### Sample Dashboard JSON

Create a Grafana dashboard with these panels:

#### Panel 1: Agent Status Overview
```json
{
  "title": "Agent Status",
  "targets": [{
    "expr": "sum by (status) (atoll_agents_total)"
  }],
  "type": "piechart"
}
```

#### Panel 2: API Request Rate
```json
{
  "title": "API Requests/s",
  "targets": [{
    "expr": "rate(atoll_api_requests_total[1m])"
  }],
  "type": "graph"
}
```

#### Panel 3: Deployment Success Rate
```json
{
  "title": "Deployment Success Rate",
  "targets": [{
    "expr": "rate(atoll_agent_deployments_total{result=\"success\"}[5m]) / rate(atoll_agent_deployments_total[5m])"
  }],
  "type": "gauge"
}
```

### Alert Rules

**High API Error Rate:**
```yaml
- alert: HighAPIErrorRate
  expr: |
    rate(atoll_api_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High API error rate detected"
```

**Agent Failure:**
```yaml
- alert: AgentFailed
  expr: |
    atoll_agents_total{status="failed"} > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "One or more agents have failed"
```

**Authentication Failures:**
```yaml
- alert: HighAuthFailureRate
  expr: |
    rate(atoll_auth_attempts_total{result="failure"}[5m]) > 0.5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate of authentication failures"
```

---

## Metric Collection Best Practices

### Scraping Interval

Recommended scraping interval: **15-30 seconds**

```yaml
scrape_interval: 15s
scrape_timeout: 10s
```

### Retention

Configure Prometheus retention based on your needs:

```bash
# 15 days retention
prometheus --storage.tsdb.retention.time=15d
```

### High Cardinality Warning

**Avoid high cardinality labels:**
- ❌ Don't use user IDs, timestamps, or unique identifiers as labels
- ✅ Use status, operation type, result categories

Example:
```python
# Bad - high cardinality
metrics.counter.labels(user_id="12345").inc()

# Good - bounded cardinality
metrics.counter.labels(status="success").inc()
```

---

## Troubleshooting

### Metrics Not Available

**Problem:** `/metrics` returns "Prometheus client not installed"

**Solution:**
```bash
pip install prometheus-client>=0.19.0
# Or
pip install atoll[monitoring]
```

### Metrics Not Updating

**Check agent discovery:**
```bash
# Verify agents are discovered
curl http://localhost:8080/agents
```

**Force metrics update:**
```bash
# The /metrics endpoint automatically updates counts
curl http://localhost:8080/metrics | grep atoll_agents_total
```

### Prometheus Not Scraping

**Verify connectivity:**
```bash
# From Prometheus host
curl http://atoll-host:8080/metrics
```

**Check Prometheus targets:**
- Navigate to `http://prometheus:9090/targets`
- Verify ATOLL target shows "UP" status

---

## Example: Complete Monitoring Stack

### Docker Compose Setup

```yaml
version: '3.8'
services:
  atoll:
    image: atoll:2.0.0
    ports:
      - "8080:8080"
    environment:
      - ATOLL_API_KEY=your-secret-key
    command: atoll-deploy serve

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

### Access URLs

- **ATOLL API**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Next Steps

1. **Set up Prometheus** to scrape ATOLL metrics
2. **Create Grafana dashboards** for visualization
3. **Configure alerts** for critical conditions
4. **Review metrics regularly** to optimize performance

For more information:
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [ATOLL API Guide](API_USAGE_GUIDE.md)
