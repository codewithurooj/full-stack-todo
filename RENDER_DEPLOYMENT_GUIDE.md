# Render Deployment Guide - FastAPI Backend

## Overview
This guide will walk you through deploying your FastAPI backend to Render using the Blueprint configuration already set up in your repository.

**Repository:** https://github.com/codewithurooj/full-stack-todo
**Backend Path:** `/backend`
**Deployment Method:** Render Blueprint (render.yaml)

---

## Prerequisites

### 1. Render Account
- Go to https://render.com
- Sign up with GitHub (recommended) or email
- Verify your email address

### 2. Environment Variables Ready
You'll need these values handy before deploying:

```
DATABASE_URL=postgresql://username:password@ep-xxx.neon.tech/neondb?sslmode=require
BETTER_AUTH_SECRET=your-secret-key-min-32-chars-replace-this-with-random-string
OPENAI_API_KEY=sk-your-openai-api-key (optional for Phase 2)
```

**Get your DATABASE_URL from Neon:**
1. Log into https://console.neon.tech
2. Select your project
3. Click "Connection Details"
4. Copy the connection string (starts with `postgresql://`)

**Generate BETTER_AUTH_SECRET:**
```bash
# Option 1: Use OpenSSL
openssl rand -base64 32

# Option 2: Use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 3: Use Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

---

## Deployment Steps

### Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com
2. Click **"New +"** button in top right
3. Select **"Blueprint"**

### Step 2: Connect Your Repository
1. You'll see "Connect a repository"
2. If this is your first time:
   - Click **"Connect GitHub"**
   - Authorize Render to access your GitHub account
   - Select which repositories to allow (or allow all)
3. Search for or select: **codewithurooj/full-stack-todo**
4. Click **"Connect"**

### Step 3: Configure Blueprint
1. Render will detect `render.yaml` in your repository
2. You'll see a preview showing:
   ```
   Service Type: Web Service
   Name: todo-api
   Runtime: Python
   Region: Oregon
   Plan: Free
   ```
3. Click **"Apply"** to create the service

### Step 4: Set Environment Variables
Before the first deployment, you MUST set environment variables:

1. The deployment will start but will **FAIL** without env vars
2. Click on the **"todo-api"** service
3. Go to **"Environment"** tab on the left
4. Click **"Add Environment Variable"**
5. Add each variable one by one:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://user:pass@host.neon.tech/db` | Your Neon connection string |
| `BETTER_AUTH_SECRET` | `your-generated-secret-min-32-chars` | Must be 32+ characters |
| `OPENAI_API_KEY` | `sk-your-key` | Optional, can skip for now |

**Important:** Don't set `PYTHON_VERSION` or `CORS_ORIGINS` - they're already in render.yaml!

6. Click **"Save Changes"**

### Step 5: Trigger Deployment
1. After saving environment variables, the service will automatically redeploy
2. Or manually trigger: Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Watch the build logs in real-time

### Step 6: Monitor Deployment

**Build Phase:**
```
==> Building application...
==> cd backend && pip install -r requirements.txt
Collecting fastapi==0.115.0
Collecting uvicorn[standard]==0.32.0
...
Successfully installed all packages
==> Build successful!
```

**Deploy Phase:**
```
==> Starting service...
==> cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:10000
INFO:     Application startup complete
==> Your service is live!
```

**Expected duration:** 3-5 minutes for first deployment

### Step 7: Verify Deployment

Your service URL will be: `https://todo-api.onrender.com` (or similar)

**Test the endpoints:**

1. **Health Check:**
   ```bash
   curl https://todo-api.onrender.com/health
   ```
   Expected response:
   ```json
   {"status": "healthy"}
   ```

2. **Root Endpoint:**
   ```bash
   curl https://todo-api.onrender.com/
   ```
   Expected response:
   ```json
   {
     "message": "Todo API - Phase 2",
     "version": "1.0.0",
     "docs": "/docs"
   }
   ```

3. **API Documentation:**
   Open in browser: `https://todo-api.onrender.com/docs`

   You should see interactive Swagger UI with all your endpoints!

### Step 8: Update Frontend Configuration

Once deployed, update your frontend to use the live API:

1. Open `frontend/.env.local`
2. Add the production API URL:
   ```env
   NEXT_PUBLIC_API_URL=https://todo-api.onrender.com
   ```
3. Update CORS in Render:
   - Go to Render dashboard → todo-api → Environment
   - Update `CORS_ORIGINS` value to include your Vercel URL:
     ```json
     ["http://localhost:3000", "https://your-app.vercel.app"]
     ```
   - Save and redeploy

---

## Troubleshooting

### Issue 1: Build Fails - "requirements.txt not found"
**Cause:** Build command not finding the backend directory
**Solution:** Check render.yaml has correct buildCommand:
```yaml
buildCommand: "cd backend && pip install -r requirements.txt"
```

### Issue 2: Service Crashes - "DATABASE_URL not set"
**Cause:** Missing environment variables
**Solution:**
1. Go to Environment tab
2. Add `DATABASE_URL` with your Neon connection string
3. Save and redeploy

### Issue 3: Health Check Failing
**Cause:** Port mismatch or app not starting
**Solution:**
1. Check logs for errors
2. Verify startCommand in render.yaml:
   ```yaml
   startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```
3. Ensure `/health` endpoint exists in app/main.py

### Issue 4: CORS Errors from Frontend
**Cause:** Frontend URL not in CORS_ORIGINS
**Solution:**
1. Update CORS_ORIGINS env var to include your frontend URL
2. Format: `["http://localhost:3000", "https://your-app.vercel.app"]`
3. Save and redeploy

### Issue 5: Service Sleeps After 15 Minutes
**Cause:** Free tier limitation
**Behavior:**
- Service spins down after 15 minutes of inactivity
- First request takes 30-60 seconds (cold start)
- Subsequent requests are fast

**Solutions:**
- **Upgrade to Starter plan** ($7/month) for always-on service
- **Accept the limitation** for development/testing
- **Use a ping service** like UptimeRobot (free) to keep it awake

### Issue 6: Logs Show Python Version Error
**Cause:** Python 3.13 might not be available yet
**Solution:**
1. Update `backend/runtime.txt` to `python-3.12.0`
2. Push to GitHub
3. Render will auto-deploy with new version

---

## Free Tier Limitations

**What's Included:**
- 750 hours/month free compute time
- Automatic HTTPS
- Custom domain support
- Automatic deploys from GitHub
- Health checks
- Build & deploy logs

**Limitations:**
- Service spins down after 15 min inactivity
- 512 MB RAM
- Shared CPU
- Cold starts: 30-60 seconds on first request
- Monthly usage limits

**Recommended for:**
- Development and testing
- Portfolio projects
- Low-traffic applications

---

## Post-Deployment Checklist

- [ ] Service is deployed and showing "Live" status
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] API docs accessible at `/docs`
- [ ] Database connection working (test with a signup/signin)
- [ ] CORS configured for frontend domain
- [ ] Frontend `.env.local` updated with production API URL
- [ ] Demo video shows live deployment
- [ ] GitHub repo has deployment URL in README

---

## Useful Render Dashboard Links

Once deployed, bookmark these:

- **Service Dashboard:** https://dashboard.render.com/web/[your-service-id]
- **Logs:** Dashboard → Logs tab (real-time logging)
- **Environment:** Dashboard → Environment tab (manage env vars)
- **Settings:** Dashboard → Settings tab (service configuration)
- **Metrics:** Dashboard → Metrics tab (CPU, memory, requests)

---

## Update Deployment (Push Changes)

After making code changes:

```bash
# Commit and push
git add .
git commit -m "Update API endpoint"
git push origin master

# Render automatically deploys!
```

**Auto-deploy triggers:**
- Push to `master` branch (configured in render.yaml)
- Manual deploy button in dashboard
- Re-deploy same commit (useful for env var changes)

---

## Your Deployed URL

After deployment, your API will be at:
```
https://todo-api.onrender.com
```

Update this in:
1. **Frontend:** `NEXT_PUBLIC_API_URL` in `.env.local`
2. **README.md:** Add live API URL
3. **Demo video:** Show the live deployment

---

## Support

**Render Documentation:**
- Blueprints: https://render.com/docs/blueprint-spec
- Environment Variables: https://render.com/docs/environment-variables
- Python Services: https://render.com/docs/deploy-fastapi

**Need Help?**
- Render Community: https://community.render.com
- Render Status: https://status.render.com
- Project GitHub: https://github.com/codewithurooj/full-stack-todo

---

**Ready to deploy? Follow Step 1!** 🚀
