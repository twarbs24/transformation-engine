# Monitoring Setup for Transformation Engine

This document describes the monitoring setup for the Transformation Engine using Prometheus, Grafana, and Alertmanager.

## Overview

The Transformation Engine includes a comprehensive monitoring solution based on:

- **Prometheus**: For metrics collection and storage
- **Grafana**: For visualization and dashboards
- **Alertmanager**: For handling alerts from Prometheus and routing them to the appropriate receiver

The monitoring stack provides insights into:

1. Transformation performance and success rates
2. Verification success rates
3. Error tracking
4. System resource utilization

## Components

The monitoring stack consists of the following components:

1. **Prometheus**: Time-series database for metrics collection and storage
2. **Grafana**: Visualization and dashboarding tool
3. **Alertmanager**: Handles alerts from Prometheus and routes them to the appropriate receiver

## Metrics Collected

The Transformation Engine exposes the following metrics via Prometheus:

| Metric | Type | Description |
|--------|------|-------------|
| `transformation_engine_transformations_total` | Counter | Total number of transformations performed |
| `transformation_engine_transformations_by_type_total` | Counter | Transformations broken down by type (REFACTOR, OPTIMIZE, etc.) |
| `transformation_engine_errors_total` | Counter | Total number of errors encountered |
| `transformation_engine_verification_attempts_total` | Counter | Total number of verification attempts |
| `transformation_engine_verification_successes_total` | Counter | Total number of successful verifications |
| `transformation_engine_verification_success_ratio` | Gauge | Ratio of successful verifications to total attempts |
| `transformation_engine_transformation_duration_seconds` | Histogram | Time taken to perform transformations |
| `transformation_engine_complexity_reduction_percentage` | Gauge | Percentage reduction in complexity after transformation |
| `transformation_engine_file_size_reduction_percentage` | Gauge | Percentage reduction in file size after transformation |

## Deployment

### Prerequisites

- Kubernetes cluster with the `monitoring` namespace
- kubectl access to the cluster

### Deploying the Monitoring Stack

1. Navigate to the monitoring directory:

```bash
cd k8s/monitoring
```

2. Make the deployment scripts executable:

```bash
chmod +x create-grafana-secret.sh deploy-monitoring.sh create-alertmanager-secret.sh
```

3. Create the Grafana admin credentials:

```bash
./create-grafana-secret.sh
```

4. Deploy the monitoring stack:

```bash
./deploy-monitoring.sh
```

### Accessing the Dashboards

1. Forward the Grafana port to your local machine:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

2. Open your browser and navigate to `http://localhost:3000`

3. Log in with the credentials shown when you ran `create-grafana-secret.sh`

4. The Transformation Engine dashboard should be automatically available

## Dashboard Details

The Transformation Engine dashboard includes the following panels:

1. **Transformation Rate**: Shows the rate of transformations over time
2. **Verification Success Ratio**: Displays the success rate of verifications
3. **Total Transformations**: Shows the total count of transformations
4. **Total Errors**: Shows the total count of errors
5. **Transformations by Type**: Breaks down transformations by type (REFACTOR, OPTIMIZE, etc.)

## Alerting

The monitoring system includes alerting capabilities through Prometheus Alertmanager. The following alerts are configured:

1. **High Error Rate Alert**: Triggers when the error rate exceeds 10% for 5 minutes
2. **Low Verification Success Rate Alert**: Triggers when the verification success rate falls below 80% for 10 minutes
3. **Slow Transformations Alert**: Triggers when the 95th percentile of transformation duration exceeds 30 seconds for 10 minutes
4. **Transformation Engine Downtime Alert**: Triggers when the Transformation Engine is down for more than 1 minute
5. **High Memory Usage Alert**: Triggers when memory usage exceeds 85% of the limit for 5 minutes
6. **High CPU Usage Alert**: Triggers when CPU usage exceeds 85% of the limit for 5 minutes

### Alert Notification Channels

Alerts are configured to be sent to Slack channels. Two notification channels are set up:

1. **#monitoring-alerts**: Receives all alerts
2. **#critical-alerts**: Receives only critical alerts

### Setting Up Alert Notifications

To configure Slack notifications:

1. Create a Slack webhook URL for your workspace
2. Run the following command to create the necessary secret:

```bash
cd k8s/monitoring
./create-alertmanager-secret.sh
```

3. When prompted, enter your Slack webhook URL

## Troubleshooting

If metrics are not appearing in Prometheus:

1. Check that the Prometheus pod is running:
   ```bash
   kubectl get pods -n monitoring
   ```

2. Verify that the Transformation Engine pods have the correct annotations:
   ```bash
   kubectl get pods -n code-analysis -o yaml | grep -A 3 prometheus.io
   ```

3. Check Prometheus targets:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   ```
   Then open `http://localhost:9090/targets` in your browser

## Extending the Monitoring

To add more metrics:

1. Add new metrics to the `PrometheusMetrics` class in `metrics.py`
2. Use the metrics in the appropriate places in the code
3. Update the Grafana dashboard to include the new metrics

## References

- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
