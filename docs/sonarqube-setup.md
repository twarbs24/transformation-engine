# SonarQube/SonarCloud Setup Guide

This guide explains how to set up SonarQube or SonarCloud for code quality analysis of the Transformation Engine.

## Option 1: SonarCloud (Recommended for Open Source)

SonarCloud is a cloud-based solution that's free for open-source projects and requires minimal setup.

### Setting up SonarCloud

1. Go to [SonarCloud](https://sonarcloud.io/) and sign in with your GitHub account
2. Click "+" and select "Analyze new project"
3. Find and select your GitHub repository
4. Choose "GitHub Actions" as the analysis method
5. Follow the setup instructions provided by SonarCloud:
   - Set up the `SONAR_TOKEN` secret in your GitHub repository
   - Make sure your `sonar-project.properties` file is correctly configured

### Configuring sonar-project.properties

The `sonar-project.properties` file should be configured with your SonarCloud organization and project key:

```properties
sonar.projectKey=your-org_transformation-engine
sonar.organization=your-org

# Sources
sonar.sources=.
sonar.exclusions=tests/**/*,**/*.md,k8s/**/*,.github/**/*

# Python specific configuration
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-results.xml

# Encoding of the source code
sonar.sourceEncoding=UTF-8
```

Replace `your-org` with your actual SonarCloud organization name.

## Option 2: Self-hosted SonarQube

If you prefer to host SonarQube yourself, you can set it up in your Kubernetes cluster.

### Deploying SonarQube to Kubernetes

1. Add the SonarQube Helm repository:
   ```bash
   helm repo add sonarqube https://SonarSource.github.io/helm-chart-sonarqube
   helm repo update
   ```

2. Create a values file (`sonarqube-values.yaml`):
   ```yaml
   service:
     type: ClusterIP
   
   persistence:
     enabled: true
     storageClass: "standard"
     size: 10Gi
   
   postgresql:
     enabled: true
     persistence:
       enabled: true
       storageClass: "standard"
       size: 8Gi
   
   plugins:
     install:
       - "https://github.com/SonarSource/sonar-python/releases/download/3.9.0.9230/sonar-python-plugin-3.9.0.9230.jar"
   ```

3. Install SonarQube using Helm:
   ```bash
   kubectl create namespace sonarqube
   helm install sonarqube sonarqube/sonarqube -n sonarqube -f sonarqube-values.yaml
   ```

4. Access SonarQube:
   ```bash
   kubectl port-forward svc/sonarqube-sonarqube 9000:9000 -n sonarqube
   ```

5. Open http://localhost:9000 in your browser and log in with admin/admin
   - Change the default password
   - Create a new project manually
   - Generate a token for your CI/CD pipeline

### Configuring sonar-project.properties for Self-hosted

```properties
sonar.projectKey=transformation-engine
# No organization needed for self-hosted
# sonar.organization=your-org

# Host URL
sonar.host.url=http://sonarqube-sonarqube.sonarqube.svc.cluster.local:9000

# Sources
sonar.sources=.
sonar.exclusions=tests/**/*,**/*.md,k8s/**/*,.github/**/*

# Python specific configuration
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-results.xml

# Encoding of the source code
sonar.sourceEncoding=UTF-8
```

## Quality Gates

SonarQube/SonarCloud uses Quality Gates to determine if your code meets quality standards. By default, the "Sonar Way" quality gate is used, which checks:

- No new bugs
- No new vulnerabilities
- No new code smells with "blocker" severity
- Code coverage on new code is at least 80%
- Duplicate code is less than 3%

You can customize these rules in the SonarQube/SonarCloud UI.
