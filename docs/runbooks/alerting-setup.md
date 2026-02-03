# Alerting Setup Guide

This guide covers configuring alerts for the todo application using Prometheus Alertmanager.

---

## Overview

The alerting stack consists of:
- **Prometheus** - Collects metrics and evaluates alert rules
- **Alertmanager** - Routes alerts to notification channels
- **Notification Channels** - Email, Slack, PagerDuty, etc.

---

## Prerequisites

- kube-prometheus-stack installed
- Access to notification channel credentials

```bash
# Verify Prometheus stack is running
kubectl get pods -n monitoring | grep prometheus
kubectl get pods -n monitoring | grep alertmanager
```

---

## Configure Alertmanager

### Email Notifications

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-prometheus-kube-prometheus-alertmanager
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      smtp_smarthost: 'smtp.gmail.com:587'
      smtp_from: 'alerts@example.com'
      smtp_auth_username: 'alerts@example.com'
      smtp_auth_password: 'app-password'
      smtp_require_tls: true

    route:
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'email-notifications'
      routes:
        - match:
            severity: critical
          receiver: 'email-critical'
        - match:
            severity: warning
          receiver: 'email-warnings'

    receivers:
      - name: 'email-notifications'
        email_configs:
          - to: 'team@example.com'

      - name: 'email-critical'
        email_configs:
          - to: 'oncall@example.com'
            send_resolved: true

      - name: 'email-warnings'
        email_configs:
          - to: 'team@example.com'
            send_resolved: true
```

### Slack Notifications

```yaml
# alertmanager-config.yaml
stringData:
  alertmanager.yaml: |
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

    route:
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'slack-notifications'
      routes:
        - match:
            severity: critical
          receiver: 'slack-critical'

    receivers:
      - name: 'slack-notifications'
        slack_configs:
          - channel: '#alerts'
            send_resolved: true
            title: '{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}'
            text: |
              {{ range .Alerts }}
              *Alert:* {{ .Labels.alertname }}
              *Severity:* {{ .Labels.severity }}
              *Namespace:* {{ .Labels.namespace }}
              *Description:* {{ .Annotations.description }}
              {{ end }}

      - name: 'slack-critical'
        slack_configs:
          - channel: '#critical-alerts'
            send_resolved: true
            title: 'CRITICAL: {{ .CommonLabels.alertname }}'
            color: 'danger'
```

### Apply Configuration

```bash
kubectl apply -f alertmanager-config.yaml
```

---

## Alert Rules

### Import Existing Rules

The application includes predefined alert rules in `monitoring/alerts.yaml`:

```bash
# Apply alert rules
kubectl apply -f monitoring/alerts.yaml
```

### Custom Alert Rules

Create application-specific rules:

```yaml
# monitoring/alerts-todo-app.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: todo-app-alerts
  namespace: todo-app
  labels:
    release: prometheus
spec:
  groups:
    - name: todo-app.rules
      rules:
        # High Error Rate
        - alert: TodoAppHighErrorRate
          expr: |
            sum(rate(http_requests_total{namespace="todo-app", status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{namespace="todo-app"}[5m])) > 0.05
          for: 5m
          labels:
            severity: warning
            app: todo-app
          annotations:
            summary: "High error rate in todo-app"
            description: "Error rate is {{ $value | humanizePercentage }} for todo-app"

        # Pod Not Ready
        - alert: TodoAppPodNotReady
          expr: kube_deployment_status_replicas_ready{namespace="todo-app", deployment=~"todo-.*"} < kube_deployment_spec_replicas{namespace="todo-app", deployment=~"todo-.*"}
          for: 5m
          labels:
            severity: critical
            app: todo-app
          annotations:
            summary: "Pod not ready in {{ $labels.deployment }}"
            description: "Deployment {{ $labels.deployment }} has {{ $value }} ready replicas"

        # High Memory Usage
        - alert: TodoAppHighMemory
          expr: |
            container_memory_usage_bytes{namespace="todo-app", container!=""}
            /
            container_spec_memory_limit_bytes{namespace="todo-app", container!=""} > 0.9
          for: 5m
          labels:
            severity: warning
            app: todo-app
          annotations:
            summary: "High memory usage in {{ $labels.pod }}"
            description: "Memory usage is {{ $value | humanizePercentage }} in pod {{ $labels.pod }}"

        # Certificate Expiring Soon
        - alert: TodoAppCertificateExpiringSoon
          expr: certmanager_certificate_expiration_timestamp_seconds{namespace="todo-app"} - time() < 604800
          for: 1h
          labels:
            severity: warning
            app: todo-app
          annotations:
            summary: "TLS certificate expiring soon"
            description: "Certificate {{ $labels.name }} expires in {{ $value | humanizeDuration }}"

        # Database Connection Issues
        - alert: TodoAppDatabaseConnectionFailed
          expr: up{namespace="todo-app", job="todo-backend"} == 0
          for: 2m
          labels:
            severity: critical
            app: todo-app
          annotations:
            summary: "Backend service down"
            description: "todo-backend health endpoint is not responding"
```

Apply:

```bash
kubectl apply -f monitoring/alerts-todo-app.yaml
```

---

## Verify Alerting

### Check Alert Status

```bash
# View firing alerts
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  wget -qO- http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# Access Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090/alerts
```

### Check Alertmanager

```bash
# Access Alertmanager UI
kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093
# Open http://localhost:9093

# Check alert routing
kubectl exec -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager-0 -- \
  amtool alert query
```

### Test Alert Firing

Create a test alert:

```bash
# Scale down to trigger pod-not-ready alert
kubectl scale deployment todo-backend --replicas=0 -n todo-app

# Wait for alert to fire (5 minutes)
# Check Alertmanager for notification

# Scale back up
kubectl scale deployment todo-backend --replicas=2 -n todo-app
```

---

## Silencing Alerts

### Via Alertmanager UI

1. Access Alertmanager UI (port-forward to 9093)
2. Click "Silences" → "New Silence"
3. Add matchers (e.g., `alertname=TodoAppPodNotReady`)
4. Set duration and comment

### Via CLI

```bash
# Create silence
kubectl exec -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager-0 -- \
  amtool silence add alertname=TodoAppPodNotReady --comment="Maintenance window" --duration=2h

# List silences
kubectl exec -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager-0 -- \
  amtool silence query

# Expire silence
kubectl exec -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager-0 -- \
  amtool silence expire <silence-id>
```

---

## Integration Examples

### PagerDuty

```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<your-service-key>'
        send_resolved: true
```

### Microsoft Teams

```yaml
receivers:
  - name: 'msteams'
    webhook_configs:
      - url: 'https://outlook.office.com/webhook/...'
        send_resolved: true
```

### Opsgenie

```yaml
receivers:
  - name: 'opsgenie'
    opsgenie_configs:
      - api_key: '<your-api-key>'
        send_resolved: true
```

---

## Quick Reference

| Task | Command |
|------|---------|
| View alerts | `kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090` |
| View Alertmanager | `kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093` |
| Check firing alerts | Open http://localhost:9090/alerts |
| Create silence | Use Alertmanager UI at http://localhost:9093 |
| Apply alert rules | `kubectl apply -f monitoring/alerts-todo-app.yaml` |
