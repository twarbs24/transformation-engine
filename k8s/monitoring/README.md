# Transformation Engine Monitoring

This directory contains Kubernetes manifests and scripts for deploying Prometheus, Grafana, and Alertmanager to monitor the Transformation Engine.

## Components

This directory contains Kubernetes manifests for setting up monitoring for the Transformation Engine:

1. **Prometheus**: For metrics collection and storage
   - `prometheus-configmap.yaml`: Configuration for Prometheus
   - `prometheus-deployment.yaml`: Deployment for Prometheus
   - `prometheus-rbac.yaml`: RBAC permissions for Prometheus
   - `prometheus-service.yaml`: Service for Prometheus
   - `prometheus-storage.yaml`: PersistentVolumeClaim for Prometheus
   - `prometheus-rules.yaml`: Alerting rules for Prometheus

2. **Grafana**: For visualization and dashboards
   - `grafana-configmaps.yaml`: Configuration and dashboards for Grafana
   - `grafana-deployment.yaml`: Deployment for Grafana
   - `grafana-service.yaml`: Service for Grafana
   - `grafana-storage.yaml`: PersistentVolumeClaim for Grafana
   - `create-grafana-secret.sh`: Script to create Grafana admin credentials

3. **Alertmanager**: For handling alerts from Prometheus
   - `alertmanager.yaml`: Deployment, Service, and ConfigMap for Alertmanager
   - `create-alertmanager-secret.sh`: Script to create Alertmanager secrets (Slack webhook)

4. **Deployment Scripts**:
   - `deploy-monitoring.sh`: Script to deploy the entire monitoring stack

## Deployment

To deploy the monitoring stack:

1. Create Grafana admin credentials:
   ```bash
   ./create-grafana-secret.sh
   ```

2. Create Alertmanager secrets (for Slack notifications):
   ```bash
   ./create-alertmanager-secret.sh
   ```

3. Deploy the monitoring stack:
   ```bash
   ./deploy-monitoring.sh
   ```

## Accessing the Dashboards

After deployment, you can access the dashboards using port forwarding:

1. Grafana:
   ```bash
   kubectl port-forward -n monitoring svc/grafana 3000:3000
   ```
   Then open http://localhost:3000 in your browser.

2. Prometheus:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   ```
   Then open http://localhost:9090 in your browser.

3. Alertmanager:
   ```bash
   kubectl port-forward -n monitoring svc/alertmanager 9093:9093
   ```
   Then open http://localhost:9093 in your browser.

## Alerting

The monitoring system includes alerting capabilities through Prometheus Alertmanager. Alerts are configured to be sent to Slack channels:

1. **#monitoring-alerts**: Receives all alerts
2. **#critical-alerts**: Receives only critical alerts

The following alerts are configured:

1. **High Error Rate Alert**: Triggers when the error rate exceeds 10% for 5 minutes
2. **Low Verification Success Rate Alert**: Triggers when the verification success rate falls below 80% for 10 minutes
3. **Slow Transformations Alert**: Triggers when the 95th percentile of transformation duration exceeds 30 seconds for 10 minutes
4. **Transformation Engine Downtime Alert**: Triggers when the Transformation Engine is down for more than 1 minute
5. **High Memory Usage Alert**: Triggers when memory usage exceeds 85% of the limit for 5 minutes
6. **High CPU Usage Alert**: Triggers when CPU usage exceeds 85% of the limit for 5 minutes

## Metrics

The Transformation Engine exposes metrics at the `/metrics` endpoint, which Prometheus scrapes automatically based on pod annotations.

For more details, see the [monitoring setup documentation](../../docs/monitoring-setup.md).
