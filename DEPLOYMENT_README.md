# Backend Deployment - Complete Guide

## 📚 Documentation Overview

Your backend is **ready to deploy** to Render! This folder contains all the deployment guides you need.

### 🚀 Quick Start (5 minutes)
**Read this first:** [`DEPLOY_NOW.md`](./DEPLOY_NOW.md)
- Visual step-by-step guide
- Exact commands to run
- Everything you need in 5 minutes

### ✅ Deployment Checklist
**Before you deploy:** [`DEPLOYMENT_CHECKLIST.md`](./DEPLOYMENT_CHECKLIST.md)
- What to prepare
- Environment variables
- Quick verification steps

### 📖 Complete Deployment Guide
**For detailed information:** [`RENDER_DEPLOYMENT_GUIDE.md`](./RENDER_DEPLOYMENT_GUIDE.md)
- Comprehensive instructions
- Free tier details
- Post-deployment steps
- CORS configuration

### 🔧 Troubleshooting
**If something goes wrong:** [`RENDER_TROUBLESHOOTING.md`](./RENDER_TROUBLESHOOTING.md)
- Common errors and fixes
- Debugging workflow
- Performance optimization
- Getting help

---

## 🎯 Current Status

### ✅ What's Ready
- [x] FastAPI backend with all routes
- [x] SQLModel models for database
- [x] JWT authentication middleware
- [x] Health check endpoint
- [x] Render Blueprint (`render.yaml`)
- [x] Python runtime specification
- [x] Requirements.txt with all dependencies
- [x] CORS configuration
- [x] Database setup with Neon

### 📋 What You Need

**From Neon:**
- [ ] Database URL (get from https://console.neon.tech)

**Generated Locally:**
- [ ] Better Auth Secret (32+ characters random string)

**From OpenAI (optional):**
- [ ] API Key for Phase 3 features

---

## 🏃 Quick Deploy (Right Now!)

### Option 1: One-Click Blueprint Deploy

1. **Go to Render:**
   ```
   https://dashboard.render.com
   ```

2. **New Blueprint:**
   - Click "New +" → "Blueprint"
   - Connect: `codewithurooj/full-stack-todo`
   - Click "Apply"

3. **Set Environment Variables:**
   - DATABASE_URL: Your Neon connection string
   - BETTER_AUTH_SECRET: Generated random string
   - (Optional) OPENAI_API_KEY: Your OpenAI key

4. **Wait for deployment:** 3-5 minutes

5. **Test:**
   ```bash
   curl https://todo-api.onrender.com/health
   ```

**That's it!** Your API is live.

---

## 📦 What Gets Deployed

### Repository Structure
```
full-stack-todo/
├── render.yaml                    ← Deployment config
├── backend/
│   ├── runtime.txt               ← Python 3.13.0
│   ├── requirements.txt          ← Dependencies
│   └── app/
│       ├── main.py              ← FastAPI app
│       ├── config.py            ← Environment config
│       ├── database.py          ← Database connection
│       ├── models/              ← SQLModel models
│       ├── routes/              ← API endpoints
│       └── middleware/          ← JWT auth
```

### Render Blueprint Configuration
```yaml
Service Name:     todo-api
Service Type:     Web Service
Runtime:          Python 3.13.0
Region:           Oregon (us-west)
Plan:             Free Tier
Branch:           master
Build Command:    cd backend && pip install -r requirements.txt
Start Command:    cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check:     /health
Auto Deploy:      On push to master
```

### Environment Variables Required
```env
DATABASE_URL=postgresql://...              # Required
BETTER_AUTH_SECRET=xxxxx...               # Required (32+ chars)
OPENAI_API_KEY=sk-...                     # Optional
CORS_ORIGINS=["http://localhost:3000"]   # Auto-set from render.yaml
PYTHON_VERSION=3.13.0                     # Auto-set from render.yaml
```

---

## 🌐 Deployed Endpoints

After deployment, your API will be available at:
```
https://todo-api.onrender.com
```

### Available Endpoints

**Health & Info:**
```
GET  /                    → API info
GET  /health             → Health check
GET  /docs              → Swagger UI
GET  /redoc             → ReDoc UI
```

**Authentication:**
```
POST /auth/signup        → Create account
POST /auth/signin        → Login
```

**Tasks (requires auth):**
```
GET    /api/{user_id}/tasks              → List all tasks
POST   /api/{user_id}/tasks              → Create task
GET    /api/{user_id}/tasks/{id}         → Get task
PUT    /api/{user_id}/tasks/{id}         → Update task
DELETE /api/{user_id}/tasks/{id}         → Delete task
PATCH  /api/{user_id}/tasks/{id}/complete → Toggle completion
```

---

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://todo-api.onrender.com/health
```
**Expected:** `{"status":"healthy"}`

### 2. API Info
```bash
curl https://todo-api.onrender.com/
```
**Expected:**
```json
{
  "message": "Todo API - Phase 2",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 3. API Documentation
Open in browser:
```
https://todo-api.onrender.com/docs
```
**Expected:** Interactive Swagger UI

### 4. Sign Up (Create Account)
```bash
curl -X POST https://todo-api.onrender.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'
```

### 5. Sign In (Get Token)
```bash
curl -X POST https://todo-api.onrender.com/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```
**Save the token from response!**

### 6. Create Task (Authenticated)
```bash
curl -X POST https://todo-api.onrender.com/api/USER_ID/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "Testing deployment"
  }'
```

---

## 🔄 Continuous Deployment

### Auto-Deploy Setup
Your repository is configured for automatic deployments:

```bash
# Make changes
git add .
git commit -m "Update API endpoint"
git push origin master

# Render automatically:
# 1. Detects push to master
# 2. Pulls latest code
# 3. Runs build command
# 4. Deploys new version
# 5. Runs health checks
```

**Deployment time:** 3-5 minutes

### Manual Deploy
If you need to redeploy without code changes:
1. Go to Render dashboard
2. Click on "todo-api"
3. Click "Manual Deploy" → "Deploy latest commit"

---

## 🔐 Security Checklist

Before going to production:

- [x] Environment variables set (not in code)
- [x] Secrets stored in Render environment
- [x] CORS configured for frontend domain
- [x] JWT authentication on all protected routes
- [x] User ID validation in all endpoints
- [x] Database uses SSL (Neon default)
- [x] No secrets in logs
- [x] Health check endpoint public only
- [ ] Update CORS after frontend deployment
- [ ] Rate limiting (Phase 3)
- [ ] Input validation (in place via Pydantic)

---

## 💰 Free Tier Limits

**What's Included:**
- ✅ 750 hours/month compute time
- ✅ Automatic HTTPS
- ✅ Automatic deployments
- ✅ Health checks
- ✅ Custom domain support

**Limitations:**
- ⚠️ Spins down after 15 min idle
- ⚠️ 30-60 sec cold start on first request
- ⚠️ 512 MB RAM
- ⚠️ Shared CPU

**Perfect for:**
- Development & testing
- Portfolio projects
- Hackathon submissions
- Low-traffic apps

**Upgrade to Starter ($7/month) for:**
- Always-on service
- No cold starts
- Better performance

---

## 🔧 Update CORS After Frontend Deploy

After deploying your frontend to Vercel:

1. **Get Vercel URL:**
   ```
   https://your-todo-app.vercel.app
   ```

2. **Update Render Environment:**
   - Dashboard → todo-api → Environment
   - Find `CORS_ORIGINS`
   - Update to:
     ```json
     ["http://localhost:3000", "https://your-todo-app.vercel.app"]
     ```
   - Save changes

3. **Service auto-redeploys** with new CORS settings

---

## 📊 Monitor Your Deployment

### Render Dashboard
```
https://dashboard.render.com/web/YOUR_SERVICE_ID
```

**Tabs to monitor:**
- **Events:** Deployment history
- **Logs:** Real-time application logs
- **Metrics:** CPU, memory, requests
- **Environment:** Manage env vars
- **Settings:** Service configuration

### View Logs
```bash
# Real-time logs in browser:
Dashboard → Logs tab

# Filter logs:
- Info: General information
- Warning: Warnings
- Error: Errors only
- All: Everything
```

### Check Metrics
```
Dashboard → Metrics tab

Shows:
- Request rate
- Response time
- Error rate
- CPU usage
- Memory usage
```

---

## 🎓 Learning Resources

### Render Documentation
- **Blueprints:** https://render.com/docs/blueprint-spec
- **Python Apps:** https://render.com/docs/deploy-fastapi
- **Environment Variables:** https://render.com/docs/environment-variables

### FastAPI Resources
- **Docs:** https://fastapi.tiangolo.com
- **Deployment:** https://fastapi.tiangolo.com/deployment/

### SQLModel Resources
- **Docs:** https://sqlmodel.tiangolo.com
- **Tutorial:** https://sqlmodel.tiangolo.com/tutorial/

---

## 📱 Share Your Deployment

### Update README.md
```markdown
## 🚀 Live Demo

- **Backend API:** https://todo-api.onrender.com
- **API Docs:** https://todo-api.onrender.com/docs
- **Frontend:** https://your-app.vercel.app

## 🏗️ Deployment

- **Backend:** Render (Free Tier)
- **Frontend:** Vercel (Free Tier)
- **Database:** Neon Serverless PostgreSQL (Free Tier)

### API Health Check
\`\`\`bash
curl https://todo-api.onrender.com/health
\`\`\`
```

### Demo Video Script
```
1. Show deployed API docs (https://todo-api.onrender.com/docs)
2. Test health endpoint
3. Sign up new user
4. Create a task
5. Show frontend using the API
6. Show auto-deployment (push code, show logs)
```

---

## 🆘 Getting Help

### Quick Help
1. Check [`RENDER_TROUBLESHOOTING.md`](./RENDER_TROUBLESHOOTING.md)
2. Review Render logs
3. Test locally first
4. Compare local vs. deployed

### Common Issues
- **Build fails:** Check `buildCommand` in render.yaml
- **Crashes:** Missing environment variables
- **CORS errors:** Update CORS_ORIGINS
- **Slow:** Normal free tier cold starts

### Community Support
- **Render Community:** https://community.render.com
- **Render Status:** https://status.render.com
- **Project Issues:** https://github.com/codewithurooj/full-stack-todo/issues

---

## ✅ Deployment Success Checklist

Your deployment is complete when:

- [ ] Service shows "Live" in Render dashboard
- [ ] Health check returns `{"status":"healthy"}`
- [ ] API docs visible at `/docs`
- [ ] Can sign up new user
- [ ] Can sign in and get token
- [ ] Can create task with auth token
- [ ] Frontend connects without CORS errors
- [ ] No errors in Render logs
- [ ] URL added to README.md
- [ ] Demo video recorded

---

## 🎉 Next Steps

1. ✅ **Backend deployed!** (You are here)
2. ⏭️ Deploy frontend to Vercel
3. ⏭️ Update CORS with Vercel URL
4. ⏭️ Test end-to-end flow
5. ⏭️ Record demo video (<90 seconds)
6. ⏭️ Submit project!

---

## 📞 Quick Reference

**Your Repository:**
```
https://github.com/codewithurooj/full-stack-todo
```

**Render Dashboard:**
```
https://dashboard.render.com
```

**Neon Console:**
```
https://console.neon.tech
```

**Deploy Command:**
```
Just push to master - auto-deploys!
```

**Test Command:**
```bash
curl https://todo-api.onrender.com/health
```

---

**Ready to deploy?** Start with [`DEPLOY_NOW.md`](./DEPLOY_NOW.md)! 🚀

**Questions?** Check [`RENDER_TROUBLESHOOTING.md`](./RENDER_TROUBLESHOOTING.md)

**Good luck with your deployment!** 💪
