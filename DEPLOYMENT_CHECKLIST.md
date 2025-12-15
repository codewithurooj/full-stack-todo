# Render Deployment Quick Checklist

## Before You Start

### 1. Get Your Neon Database URL
```
Log into: https://console.neon.tech
Navigate to: Your Project → Connection Details
Copy: Connection string (starts with postgresql://)

Format: postgresql://username:password@ep-xxx.neon.tech/neondb?sslmode=require
```

### 2. Generate Better Auth Secret
```bash
# Run ONE of these commands:
openssl rand -base64 32
# OR
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. (Optional) Get OpenAI API Key
```
Log into: https://platform.openai.com/api-keys
Create: New secret key
Copy: Starts with sk-
```

---

## Deployment Steps (5 minutes)

### Step 1: Render Dashboard
1. Go to: https://dashboard.render.com
2. Click: **"New +"** → **"Blueprint"**
3. Connect repository: **codewithurooj/full-stack-todo**
4. Click: **"Apply"**

### Step 2: Set Environment Variables
Navigate to: **todo-api** → **Environment** → **Add Environment Variable**

| Key | Value | Where to Get |
|-----|-------|--------------|
| `DATABASE_URL` | `postgresql://...` | Neon console |
| `BETTER_AUTH_SECRET` | `your-32-char-secret` | Generated above |
| `OPENAI_API_KEY` | `sk-...` | OpenAI dashboard (optional) |

Click: **"Save Changes"**

### Step 3: Wait for Deployment (3-5 min)
Watch logs for:
```
==> Build successful!
==> Your service is live!
```

### Step 4: Test Deployment
```bash
# Replace with your actual URL
curl https://todo-api.onrender.com/health

# Expected: {"status": "healthy"}
```

### Step 5: Get Your URL
Copy your service URL from dashboard:
```
https://todo-api.onrender.com
```

---

## Update Frontend

Add to `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://todo-api.onrender.com
```

After frontend deploys to Vercel, update CORS:
1. Render Dashboard → todo-api → Environment
2. Find `CORS_ORIGINS`
3. Update to: `["http://localhost:3000", "https://your-app.vercel.app"]`
4. Save and redeploy

---

## Verify Everything Works

- [ ] Health check returns healthy
- [ ] API docs visible at `/docs`
- [ ] Can sign up a new user
- [ ] Can sign in
- [ ] Can create a task
- [ ] Frontend connects to backend
- [ ] No CORS errors

---

## Common Issues

**Build fails?**
→ Check environment variables are set

**Service crashes?**
→ Check logs for DATABASE_URL errors

**CORS errors?**
→ Add your Vercel URL to CORS_ORIGINS

**Slow first request?**
→ Normal! Free tier cold starts take 30-60 sec

---

## Your Deployed URLs

After deployment, update these:

```markdown
## Live Demo

- **Backend API:** https://todo-api.onrender.com
- **API Docs:** https://todo-api.onrender.com/docs
- **Frontend:** https://your-app.vercel.app
```

Add to your README.md!

---

**Quick start:** Open https://dashboard.render.com and follow Step 1! 🚀
