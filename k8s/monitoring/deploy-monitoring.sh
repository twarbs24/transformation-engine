#!/bin/bash

# Create monitoring namespace if it doesn't exist
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Create Prometheus RBAC
kubectl apply -f prometheus-rbac.yaml

# Create Prometheus ConfigMap
kubectl apply -f prometheus-configmap.yaml

# Create Prometheus Rules ConfigMap
kubectl apply -f prometheus-rules.yaml

# Create Prometheus Storage
kubectl apply -f prometheus-storage.yaml

# Deploy Prometheus
kubectl apply -f prometheus-deployment.yaml

# Create Prometheus Service
kubectl apply -f prometheus-service.yaml

# Deploy Alertmanager
kubectl apply -f alertmanager.yaml

# Create Grafana ConfigMaps
kubectl apply -f grafana-configmaps.yaml

# Create Grafana Storage
kubectl apply -f grafana-storage.yaml

# Deploy Grafana
kubectl apply -f grafana-deployment.yaml

# Create Grafana Service
kubectl apply -f grafana-service.yaml

echo "Monitoring stack deployed successfully!"
echo "To access Grafana dashboard:"
echo "kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "Then open http://localhost:3000 in your browser"
echo "Default credentials: admin / admin"
echo ""
echo "To access Prometheus dashboard:"
echo "kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "Then open http://localhost:9090 in your browser"
echo ""
echo "To access Alertmanager dashboard:"
echo "kubectl port-forward -n monitoring svc/alertmanager 9093:9093"
echo "Then open http://localhost:9093 in your browser"
