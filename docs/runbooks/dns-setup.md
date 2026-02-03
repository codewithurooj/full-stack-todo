# DNS Setup Guide

This guide covers configuring DNS for the todo application with cloud Kubernetes deployments.

## Prerequisites

- Domain name registered with a DNS provider
- NGINX Ingress Controller installed with LoadBalancer IP
- kubectl configured to access your cluster

---

## Step 1: Get LoadBalancer External IP

```bash
# Check ingress controller service
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Output example:
# NAME                       TYPE           EXTERNAL-IP     PORT(S)
# ingress-nginx-controller   LoadBalancer   203.0.113.50    80:30080/TCP,443:30443/TCP

# Store the IP
EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "LoadBalancer IP: $EXTERNAL_IP"
```

**Note**: The external IP may take a few minutes to be assigned.

---

## Step 2: Configure DNS Records

### Option A: Using Your Domain Registrar

Add an A record in your DNS provider's dashboard:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | todo | `<EXTERNAL_IP>` | 300 |

For example, if your domain is `example.com`:
- `todo.example.com` → `203.0.113.50`

### Option B: Using Cloudflare

```bash
# Using Cloudflare API
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "todo",
    "content": "'$EXTERNAL_IP'",
    "ttl": 300,
    "proxied": false
  }'
```

### Option C: Using AWS Route 53

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "todo.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$EXTERNAL_IP'"}]
      }
    }]
  }'
```

### Option D: Using Google Cloud DNS

```bash
gcloud dns record-sets create todo.example.com. \
  --zone=example-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=$EXTERNAL_IP
```

---

## Step 3: Testing Without DNS (nip.io)

For testing before DNS propagation, use [nip.io](https://nip.io):

```bash
# Access application using nip.io
# Format: <name>.<IP>.nip.io

# Example:
curl http://todo.$EXTERNAL_IP.nip.io/health
# Or open in browser:
echo "http://todo.$EXTERNAL_IP.nip.io"
```

**Note**: nip.io won't work with Let's Encrypt certificates. Use only for testing.

---

## Step 4: Verify DNS Propagation

```bash
# Check DNS resolution
dig todo.example.com +short
# Should return: 203.0.113.50

# Or use nslookup
nslookup todo.example.com

# Check from multiple DNS servers
dig @8.8.8.8 todo.example.com +short    # Google DNS
dig @1.1.1.1 todo.example.com +short    # Cloudflare DNS
dig @208.67.222.222 todo.example.com +short  # OpenDNS
```

**DNS Propagation Time**:
- New records: 5-30 minutes
- Changes: Up to 48 hours (TTL dependent)

---

## Step 5: Update Ingress Configuration

After DNS is configured, update your ingress:

```yaml
# k8s/ingress/todo-app-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-app-ingress
  namespace: todo-app
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - todo.example.com  # ← Your domain
      secretName: todo-app-tls
  rules:
    - host: todo.example.com  # ← Your domain
      http:
        paths:
          # ... paths
```

Apply the updated ingress:

```bash
kubectl apply -f k8s/ingress/todo-app-ingress.yaml
```

---

## Step 6: Verify TLS Certificate

After ingress is applied, cert-manager will request a certificate:

```bash
# Check certificate status
kubectl get certificates -n todo-app

# View certificate details
kubectl describe certificate todo-app-tls -n todo-app

# Check certificate challenges
kubectl get challenges -n todo-app

# Verify TLS with openssl
echo | openssl s_client -servername todo.example.com \
  -connect todo.example.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

---

## Troubleshooting

### DNS Not Resolving

```bash
# Check if record exists at registrar
# Wait for TTL to expire
# Try flushing local DNS cache:

# macOS
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Linux
sudo systemd-resolve --flush-caches

# Windows
ipconfig /flushdns
```

### Certificate Not Issuing

```bash
# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Check challenge status
kubectl describe challenge -n todo-app

# Common issues:
# 1. DNS not pointing to LoadBalancer IP
# 2. Ingress controller not receiving requests
# 3. HTTP-01 challenge path blocked
```

### LoadBalancer Pending

```bash
# Check service events
kubectl describe svc ingress-nginx-controller -n ingress-nginx

# Common causes:
# - Cloud provider quota reached
# - Network configuration issues
# - Missing cloud provider annotations
```

---

## DNS Configuration by Cloud Provider

### Oracle Cloud OKE

The LoadBalancer IP is automatically assigned by OCI Load Balancer service.

### Azure AKS

```bash
# Get IP from Azure Load Balancer
az network public-ip list \
  --resource-group MC_todo-rg_todo-cluster_eastus \
  --query "[?contains(name, 'kubernetes')].ipAddress" -o tsv
```

### Google Cloud GKE

```bash
# Get IP from GCP Load Balancer
gcloud compute forwarding-rules list \
  --filter="description~kubernetes" \
  --format="value(IPAddress)"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Get LoadBalancer IP | `kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'` |
| Check DNS | `dig todo.example.com +short` |
| Test with nip.io | `curl http://todo.<IP>.nip.io/health` |
| Check certificate | `kubectl get certificates -n todo-app` |
| View cert details | `openssl s_client -servername todo.example.com -connect todo.example.com:443` |
