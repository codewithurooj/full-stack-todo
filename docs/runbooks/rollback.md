# Rollback Procedures

This guide covers how to rollback deployments when issues occur.

---

## Quick Rollback (Helm)

### Rollback to Previous Release

```bash
# List release history
helm history todo-backend -n todo-app

# Rollback to previous version
helm rollback todo-backend -n todo-app

# Rollback to specific revision
helm rollback todo-backend 3 -n todo-app

# Verify rollback
kubectl rollout status deployment/todo-backend -n todo-app
```

### Rollback All Components

```bash
# Rollback backend
helm rollback todo-backend -n todo-app

# Rollback frontend
helm rollback todo-frontend -n todo-app

# Verify all pods are running
kubectl get pods -n todo-app
```

---

## Kubernetes Native Rollback

### Using kubectl

```bash
# Check rollout history
kubectl rollout history deployment/todo-backend -n todo-app

# Rollback to previous revision
kubectl rollout undo deployment/todo-backend -n todo-app

# Rollback to specific revision
kubectl rollout undo deployment/todo-backend -n todo-app --to-revision=2

# Check status
kubectl rollout status deployment/todo-backend -n todo-app
```

---

## Image Rollback

### Rollback to Previous Image Tag

```bash
# Get current image
kubectl get deployment todo-backend -n todo-app -o jsonpath='{.spec.template.spec.containers[0].image}'

# Set previous image tag
kubectl set image deployment/todo-backend \
  todo-backend=<registry>/todo-backend:sha-abc123 \
  -n todo-app

# Or using Helm
helm upgrade todo-backend ./charts/backend \
  --set image.tag=sha-abc123 \
  -n todo-app \
  --reuse-values
```

---

## Database Rollback

### Before Rolling Back Code

If the deployment included database migrations:

1. **Check if rollback is safe** - Some migrations cannot be reversed
2. **Backup current state** if needed
3. **Run reverse migration** before code rollback

```bash
# Connect to database pod
kubectl exec -it <backend-pod> -n todo-app -- bash

# Run migration rollback (if supported)
alembic downgrade -1
```

---

## Emergency Procedures

### Scale to Zero

If pods are causing issues:

```bash
# Scale down immediately
kubectl scale deployment todo-backend --replicas=0 -n todo-app

# Investigate logs
kubectl logs deployment/todo-backend -n todo-app --previous

# Scale back up after fix
kubectl scale deployment todo-backend --replicas=2 -n todo-app
```

### Force Delete Stuck Pods

```bash
kubectl delete pod <pod-name> -n todo-app --force --grace-period=0
```

### Restart All Pods

```bash
kubectl rollout restart deployment todo-backend -n todo-app
kubectl rollout restart deployment todo-frontend -n todo-app
```

---

## GitHub Actions Rollback

### Manual Workflow Dispatch

1. Go to Actions tab in GitHub
2. Select "Deploy to Cloud Kubernetes" workflow
3. Click "Run workflow"
4. Select the branch/tag to deploy

### Revert Commit and Redeploy

```bash
# Revert the problematic commit
git revert HEAD
git push origin main
# CI/CD will automatically redeploy
```

---

## Rollback Checklist

Before rolling back:

- [ ] Identify the problematic release/revision
- [ ] Check if database migrations were included
- [ ] Notify team members
- [ ] Have previous image tag ready

After rolling back:

- [ ] Verify all pods are running
- [ ] Test health endpoints
- [ ] Check application functionality
- [ ] Monitor logs for errors
- [ ] Update incident documentation

---

## Prevention

### Pre-deployment Checks

1. Run tests in CI/CD
2. Deploy to staging first
3. Use rolling update strategy
4. Set proper resource limits
5. Configure health checks

### Configuration

Ensure these are set in Helm values:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

revisionHistoryLimit: 10  # Keep 10 revisions for rollback
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| View Helm history | `helm history todo-backend -n todo-app` |
| Rollback Helm | `helm rollback todo-backend -n todo-app` |
| View K8s history | `kubectl rollout history deployment/todo-backend -n todo-app` |
| Rollback K8s | `kubectl rollout undo deployment/todo-backend -n todo-app` |
| Scale to zero | `kubectl scale deployment todo-backend --replicas=0 -n todo-app` |
| Restart pods | `kubectl rollout restart deployment todo-backend -n todo-app` |
