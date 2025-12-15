# Deploy to Render NOW - 5 Minute Guide

## What You Need (Gather These First!)

### 1. Neon Database URL
```
https://console.neon.tech
→ Your Project → Connection Details → Copy Connection String

Example:
postgresql://username:password@ep-abc123.neon.tech/neondb?sslmode=require
```

### 2. Better Auth Secret (Generate Fresh)
```bash
# Copy-paste ONE of these into your terminal:

# Mac/Linux:
openssl rand -base64 32

# Windows PowerShell:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Python (any OS):
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Save the output! You'll need it in 2 minutes.
```

### 3. OpenAI API Key (Optional - Skip for now)
```
https://platform.openai.com/api-keys
→ Create new secret key → Copy (starts with sk-)

Note: Not needed for Phase 2, you can skip this!
```

---

## Deployment Steps

### ⏱️ Minute 1: Access Render

1. Open browser: https://dashboard.render.com
2. Sign in (or sign up with GitHub)
3. Click big blue **"New +"** button (top right)
4. Select **"Blueprint"**

```
┌─────────────────────────────────┐
│  New +  ▼                       │
│    ├─ Web Service              │
│    ├─ Static Site              │
│    ├─ Private Service          │
│    └─ Blueprint    ← Click this│
└─────────────────────────────────┘
```

---

### ⏱️ Minute 2: Connect Repository

1. Click **"Connect a repository"**
2. Search: `full-stack-todo`
3. Select: **codewithurooj/full-stack-todo**
4. Click **"Connect"**

If first time connecting GitHub:
- Click **"Connect GitHub"**
- Authorize Render
- Come back and search again

```
┌──────────────────────────────────────┐
│ Search repositories...               │
│                                      │
│ ✓ codewithurooj/full-stack-todo     │
│   main • Updated 2 hours ago         │
│   [Connect] ← Click                  │
└──────────────────────────────────────┘
```

---

### ⏱️ Minute 3: Apply Blueprint

Render will show preview:

```
Blueprint Configuration
═══════════════════════

Service Type:  Web Service
Name:          todo-api
Environment:   Python
Region:        Oregon
Plan:          Free
Branch:        master
```

**Click: Apply** (big blue button)

Wait 10 seconds... service created!

---

### ⏱️ Minute 4: Set Environment Variables

**The build will START but FAIL without these!**

1. Click on **"todo-api"** (your new service)
2. Left sidebar → **"Environment"** tab
3. Click **"Add Environment Variable"**

**Add these THREE variables:**

#### Variable 1:
```
Key:   DATABASE_URL
Value: postgresql://username:password@ep-xxx.neon.tech/dbname?sslmode=require
       ↑ Your Neon connection string from step 1
```

#### Variable 2:
```
Key:   BETTER_AUTH_SECRET
Value: your-generated-secret-from-step-2-should-be-32-plus-characters
       ↑ The random string you generated
```

#### Variable 3 (OPTIONAL):
```
Key:   OPENAI_API_KEY
Value: sk-your-openai-api-key
       ↑ Skip this for now, add later if needed
```

4. Click **"Save Changes"** (bottom of page)

---

### ⏱️ Minute 5: Watch It Deploy

**Automatic redeploy starts!**

Watch the logs in real-time:

```
Build Logs:
═══════════════════════
==> Downloading source code
==> Installing dependencies
==> cd backend && pip install -r requirements.txt
    ✓ Installing fastapi
    ✓ Installing sqlmodel
    ✓ Installing uvicorn
    ...
==> Build successful! ✓

Deploy Logs:
═══════════════════════
==> Starting service
==> cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000
    INFO: Started server process
    INFO: Uvicorn running on http://0.0.0.0:10000
==> Your service is live! 🎉
```

**Expected time:** 3-5 minutes

---

## ✅ Verify Deployment

Your URL will be: **https://todo-api.onrender.com**

### Test 1: Health Check
```bash
curl https://todo-api.onrender.com/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### Test 2: Root Endpoint
```bash
curl https://todo-api.onrender.com/
```

**Expected response:**
```json
{
  "message": "Todo API - Phase 2",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### Test 3: API Documentation
Open in browser:
```
https://todo-api.onrender.com/docs
```

**You should see:** Swagger UI with all your endpoints!

```
┌────────────────────────────────────┐
│ Todo API                      1.0.0│
│ Full-Stack Todo Application API    │
│                                    │
│ Authorize 🔓                       │
│                                    │
│ ▼ auth                            │
│   POST /auth/signup               │
│   POST /auth/signin               │
│                                    │
│ ▼ tasks                           │
│   GET  /api/{user_id}/tasks      │
│   POST /api/{user_id}/tasks      │
│   ...                             │
└────────────────────────────────────┘
```

---

## 🎯 Your Deployed URL

Copy this for your frontend:
```
https://todo-api.onrender.com
```

### Update Frontend

Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://todo-api.onrender.com
```

Commit and push:
```bash
git add frontend/.env.local
git commit -m "Add production API URL"
git push origin master
```

---

## 🔥 Common Issues

### Issue: "Build failed - requirements.txt not found"
**Fix:** Check render.yaml line 8 has `cd backend &&`

### Issue: "Service crashes - DATABASE_URL not set"
**Fix:** Go back to Environment tab, add DATABASE_URL

### Issue: "Python 3.13.0 not available"
**Fix:**
```bash
# Edit backend/runtime.txt
echo "python-3.12.0" > backend/runtime.txt
git add backend/runtime.txt
git commit -m "Use Python 3.12"
git push
```

### Issue: CORS errors from frontend
**Fix:** After deploying frontend to Vercel:
1. Get your Vercel URL (e.g., `https://my-todo.vercel.app`)
2. Render dashboard → Environment
3. Find `CORS_ORIGINS`
4. Update to: `["http://localhost:3000", "https://my-todo.vercel.app"]`
5. Save

---

## 🚀 Next Steps

1. ✅ Backend deployed on Render
2. ⏭️ Deploy frontend to Vercel
3. ⏭️ Update CORS with Vercel URL
4. ⏭️ Test full application
5. ⏭️ Record demo video
6. ⏭️ Submit!

---

## 📝 Add to README

```markdown
## Live Demo

- **Backend API:** https://todo-api.onrender.com
- **API Docs:** https://todo-api.onrender.com/docs
- **Frontend:** (Coming soon - Vercel)

## Tech Stack

- **Backend:** FastAPI + SQLModel (Python 3.13)
- **Database:** Neon Serverless PostgreSQL
- **Hosting:** Render (Free Tier)
- **Deployment:** Automated via Blueprint
```

---

## 🆘 Need Help?

**Quick help:**
- 📖 Read: `RENDER_TROUBLESHOOTING.md`
- 📚 Full guide: `RENDER_DEPLOYMENT_GUIDE.md`
- ✅ Checklist: `DEPLOYMENT_CHECKLIST.md`

**If really stuck:**
1. Check Render logs for exact error
2. Search Render community
3. Open GitHub issue with error details

---

## ⚡ Pro Tips

1. **First request slow?**
   - Normal! Free tier cold starts in 30-60 sec
   - Subsequent requests are fast

2. **Service sleeping?**
   - Happens after 15 min idle (free tier)
   - First request wakes it up

3. **Want always-on?**
   - Upgrade to Starter plan ($7/month)
   - Or use UptimeRobot to ping every 5 min

4. **Auto-deploys**
   - Every push to `master` auto-deploys
   - Check logs to monitor deployment

---

**Time to deploy? You got this!** 🚀

**START HERE:** https://dashboard.render.com → New + → Blueprint
