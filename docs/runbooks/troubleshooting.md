# Troubleshooting Guide

Common issues and solutions for the todo application on cloud Kubernetes.

---

## Table of Contents

1. [Pod Issues](#pod-issues)
2. [Network/Ingress Issues](#networkingress-issues)
3. [TLS Certificate Issues](#tls-certificate-issues)
4. [Database Issues](#database-issues)
5. [Image Pull Issues](#image-pull-issues)
6. [Performance Issues](#performance-issues)
7. [Deployment Issues](#deployment-issues)

---

## Pod Issues

### Pods Not Starting (Pending)

**Symptoms**: Pods stuck in `Pending` state

```bash
# Check pod status
kubectl get pods -n todo-app

# Describe pod for events
kubectl describe pod <pod-name> -n todo-app
```

**Common Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Insufficient resources | Increase node count or reduce resource requests |
| Node selector mismatch | Check `nodeSelector` in values.yaml matches available nodes |
| PVC not bound | Check storage class and PVC status |
| ImagePullBackOff | See [Image Pull Issues](#image-pull-issues) |

```bash
# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check events
kubectl get events -n todo-app --sort-by='.lastTimestamp'
```

### Pods Crashing (CrashLoopBackOff)

**Symptoms**: Pods restart repeatedly

```bash
# Check logs from current container
kubectl logs <pod-name> -n todo-app

# Check logs from previous container
kubectl logs <pod-name> -n todo-app --previous

# Watch logs in real-time
kubectl logs -f <pod-name> -n todo-app
```

**Common Causes**:

1. **Missing environment variables**
   ```bash
   kubectl get configmap todo-backend-config -n todo-app -o yaml
   kubectl get secret todo-backend-secret -n todo-app -o yaml
   ```

2. **Database connection failure**
   ```bash
   kubectl exec -it <pod-name> -n todo-app -- python -c "from app.db import engine; print(engine.url)"
   ```

3. **Port conflict**
   ```bash
   kubectl get svc -n todo-app
   ```

### Pods Unhealthy (Readiness/Liveness Probe Failures)

```bash
# Check probe configuration
kubectl get deployment todo-backend -n todo-app -o yaml | grep -A 10 "livenessProbe"

# Test health endpoint manually
kubectl exec -it <pod-name> -n todo-app -- curl localhost:8000/health
```

---

## Network/Ingress Issues

### Service Not Accessible

```bash
# Check service exists
kubectl get svc -n todo-app

# Check endpoints
kubectl get endpoints -n todo-app

# Test service internally
kubectl run test-curl --image=curlimages/curl -n todo-app --rm -it --restart=Never -- \
  curl -v http://todo-backend:8000/health
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n todo-app

# Describe ingress for events
kubectl describe ingress todo-app-ingress -n todo-app

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=100

# Verify ingress class
kubectl get ingressclass
```

**Common Fixes**:

```bash
# Ensure ingress controller is running
kubectl get pods -n ingress-nginx

# Check LoadBalancer has external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Restart ingress controller if stuck
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx
```

### CORS Errors

Check ingress annotations:

```yaml
annotations:
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "*"
  nginx.ingress.kubernetes.io/cors-allow-methods: "GET, PUT, POST, DELETE, PATCH, OPTIONS"
```

---

## TLS Certificate Issues

### Certificate Not Issuing

```bash
# Check certificate status
kubectl get certificates -n todo-app
kubectl describe certificate todo-app-tls -n todo-app

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager --tail=100

# Check challenges
kubectl get challenges -n todo-app
kubectl describe challenge <challenge-name> -n todo-app
```

**Common Causes**:

| Issue | Solution |
|-------|----------|
| DNS not pointing to LoadBalancer | Update DNS A record |
| HTTP-01 challenge blocked | Ensure port 80 is open |
| Rate limited by Let's Encrypt | Wait or use staging issuer |
| ClusterIssuer not found | Apply ClusterIssuer manifest |

### Using Staging Issuer for Testing

```bash
# Switch to staging issuer
kubectl patch ingress todo-app-ingress -n todo-app \
  -p '{"metadata":{"annotations":{"cert-manager.io/cluster-issuer":"letsencrypt-staging"}}}'

# Delete old certificate to trigger reissuance
kubectl delete certificate todo-app-tls -n todo-app
```

### Verify TLS Certificate

```bash
# Check certificate details
echo | openssl s_client -servername todo.example.com -connect todo.example.com:443 2>/dev/null | \
  openssl x509 -noout -text | grep -E "(Issuer|Subject|Not Before|Not After)"
```

---

## Database Issues

### Connection Refused

```bash
# Verify DATABASE_URL secret
kubectl get secret todo-backend-secret -n todo-app -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test connection from pod
kubectl exec -it <backend-pod> -n todo-app -- python -c "
from sqlmodel import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
print('Connection successful')
"
```

### Connection Timeout

Check if Neon database requires SSL:

```bash
# DATABASE_URL should include sslmode
# postgresql://user:pass@host/db?sslmode=require
```

### Too Many Connections

```bash
# Check current connections (from Neon dashboard)
# Or reduce connection pool size in backend config
```

---

## Image Pull Issues

### ImagePullBackOff

```bash
# Check pod events
kubectl describe pod <pod-name> -n todo-app | grep -A 10 "Events"

# Verify image exists
docker pull <registry>/<image>:<tag>

# Check imagePullSecrets
kubectl get pod <pod-name> -n todo-app -o jsonpath='{.spec.imagePullSecrets}'
kubectl get secret <secret-name> -n todo-app
```

**Solutions**:

```bash
# Recreate pull secret
kubectl delete secret ocir-secret -n todo-app
kubectl create secret docker-registry ocir-secret \
  --namespace todo-app \
  --docker-server=<registry> \
  --docker-username=<username> \
  --docker-password=<password>

# Verify secret is configured in deployment
kubectl get deployment todo-backend -n todo-app -o yaml | grep -A 2 imagePullSecrets
```

### ErrImageNeverPull

Change `imagePullPolicy` from `Never` to `Always` for cloud deployments:

```bash
helm upgrade todo-backend ./charts/backend \
  --set image.pullPolicy=Always \
  -n todo-app
```

---

## Performance Issues

### High CPU/Memory Usage

```bash
# Check resource usage
kubectl top pods -n todo-app
kubectl top nodes

# Check resource limits
kubectl get deployment todo-backend -n todo-app -o yaml | grep -A 10 resources
```

### Slow Response Times

```bash
# Check pod logs for slow queries
kubectl logs <pod-name> -n todo-app | grep -i slow

# Check HPA status
kubectl get hpa -n todo-app

# Scale manually if needed
kubectl scale deployment todo-backend --replicas=3 -n todo-app
```

### Pod OOMKilled

```bash
# Check events
kubectl get events -n todo-app | grep OOMKilled

# Increase memory limits
helm upgrade todo-backend ./charts/backend \
  --set resources.limits.memory=1Gi \
  -n todo-app
```

---

## Deployment Issues

### Helm Upgrade Failed

```bash
# Check Helm status
helm status todo-backend -n todo-app

# View Helm history
helm history todo-backend -n todo-app

# Rollback to previous version
helm rollback todo-backend -n todo-app
```

### Stuck in Terminating

```bash
# Force delete pod
kubectl delete pod <pod-name> -n todo-app --force --grace-period=0

# If namespace stuck in terminating
kubectl get namespace todo-app -o json | \
  jq '.spec.finalizers = []' | \
  kubectl replace --raw "/api/v1/namespaces/todo-app/finalize" -f -
```

### Deployment Not Updating

```bash
# Check rollout status
kubectl rollout status deployment/todo-backend -n todo-app

# Force rollout restart
kubectl rollout restart deployment/todo-backend -n todo-app

# Check image tag
kubectl get deployment todo-backend -n todo-app -o jsonpath='{.spec.template.spec.containers[0].image}'
```

---

## Quick Diagnostic Commands

```bash
# Overall cluster health
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running

# Application status
kubectl get all -n todo-app

# Recent events
kubectl get events -n todo-app --sort-by='.lastTimestamp' | tail -20

# Resource usage
kubectl top pods -n todo-app
kubectl top nodes

# Logs from all backend pods
kubectl logs -l app.kubernetes.io/name=todo-backend -n todo-app --tail=50

# Check all secrets exist
kubectl get secrets -n todo-app

# Check all configmaps exist
kubectl get configmaps -n todo-app
```

---

## Getting Help

1. Check the [quickstart guide](../specs/013-cloud-k8s-deployment/quickstart.md)
2. Review deployment logs in GitHub Actions
3. Check cloud provider status pages
4. File an issue in the GitHub repository
