# Render Deployment Troubleshooting Guide

## Quick Diagnostics

### Is your service deployed?
Check: https://dashboard.render.com → Services → todo-api

**Status Indicators:**
- 🟢 **Live** - Everything working
- 🟡 **Building** - Deployment in progress
- 🔴 **Failed** - Check logs for errors
- ⚫ **Sleeping** - Free tier idle (wakes on request)

---

## Common Deployment Errors

### Error 1: "requirements.txt not found"

**Logs show:**
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory
```

**Cause:** Build command looking in wrong directory

**Fix:**
1. Go to Render dashboard → todo-api → Settings
2. Find "Build Command"
3. Ensure it's: `cd backend && pip install -r requirements.txt`
4. Save and redeploy

**Alternative:** Edit `render.yaml` line 8:
```yaml
buildCommand: "cd backend && pip install -r requirements.txt"
```

---

### Error 2: "DATABASE_URL environment variable not set"

**Logs show:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
DATABASE_URL
  Field required
```

**Cause:** Missing environment variable

**Fix:**
1. Go to Render dashboard → todo-api → Environment
2. Click "Add Environment Variable"
3. Add:
   - Key: `DATABASE_URL`
   - Value: Your Neon connection string
4. Click "Save Changes"
5. Service will auto-redeploy

**Get DATABASE_URL:**
```
1. Log into https://console.neon.tech
2. Select your project
3. Click "Connection Details"
4. Copy the connection string
5. Format: postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
```

---

### Error 3: "Python version 3.13.0 is not available"

**Logs show:**
```
ERROR: The Python version '3.13.0' is not available on this platform
```

**Cause:** Python 3.13 not yet supported by Render

**Fix Option 1 - Use Python 3.12:**
1. Edit `backend/runtime.txt`
2. Change to: `python-3.12.0`
3. Commit and push:
   ```bash
   git add backend/runtime.txt
   git commit -m "Use Python 3.12 for Render compatibility"
   git push origin master
   ```

**Fix Option 2 - Remove runtime.txt:**
1. Delete `backend/runtime.txt`
2. Let Render use default Python version
3. Push changes

**Check current Python support:**
- Visit: https://render.com/docs/python-version

---

### Error 4: "Port already in use" or "Address already in use"

**Logs show:**
```
ERROR: [Errno 98] Address already in use
```

**Cause:** Not using Render's $PORT variable

**Fix:**
1. Check `render.yaml` line 9:
   ```yaml
   startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```
2. Ensure `$PORT` is used (NOT hardcoded 8000)
3. Save and redeploy

---

### Error 5: "Health check failed"

**Dashboard shows:**
```
❌ Health check failing at /health
```

**Cause:** Health endpoint not responding or returning wrong format

**Fix:**
1. Check `render.yaml` line 21:
   ```yaml
   healthCheckPath: /health
   ```
2. Verify endpoint exists in `backend/app/main.py`:
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```
3. Test locally:
   ```bash
   curl http://localhost:8000/health
   ```
4. If working locally, check Render logs for startup errors

---

### Error 6: "ModuleNotFoundError: No module named 'app'"

**Logs show:**
```
ModuleNotFoundError: No module named 'app'
```

**Cause:** Python not finding app module (path issue)

**Fix:**
1. Verify `startCommand` in `render.yaml`:
   ```yaml
   startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```
2. Ensure it has `cd backend &&` before uvicorn
3. Check directory structure:
   ```
   backend/
   ├── app/
   │   ├── __init__.py  ← Must exist!
   │   └── main.py
   ```

---

### Error 7: "CORS policy blocked"

**Frontend shows:**
```
Access to fetch at 'https://todo-api.onrender.com/api/...' from origin
'https://your-app.vercel.app' has been blocked by CORS policy
```

**Cause:** Frontend URL not in CORS_ORIGINS

**Fix:**
1. Go to Render dashboard → todo-api → Environment
2. Find or add `CORS_ORIGINS`
3. Set value to:
   ```json
   ["http://localhost:3000", "https://your-app.vercel.app"]
   ```
4. Replace `your-app.vercel.app` with your actual Vercel URL
5. Save and wait for redeploy

**Test CORS:**
```bash
curl -H "Origin: https://your-app.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://todo-api.onrender.com/health -v
```

Look for: `Access-Control-Allow-Origin: https://your-app.vercel.app`

---

### Error 8: "Database connection failed"

**Logs show:**
```
psycopg2.OperationalError: connection to server at "..." failed
```

**Cause:** Invalid DATABASE_URL or Neon database not accessible

**Fix:**
1. Verify DATABASE_URL format:
   ```
   postgresql://username:password@ep-xxx.neon.tech/dbname?sslmode=require
   ```
2. Test connection from local machine:
   ```bash
   psql "postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require"
   ```
3. Check Neon dashboard for:
   - Database is not paused
   - IP allowlist settings (should allow all for Render)
   - Connection limit not exceeded

**Get fresh DATABASE_URL:**
1. Neon console → Project → Connection Details
2. Copy the pooled connection string
3. Update in Render environment variables

---

### Error 9: "Service keeps crashing/restarting"

**Dashboard shows:**
```
Service restarted due to error (exit code 1)
```

**Diagnostic Steps:**

1. **Check full logs:**
   - Dashboard → Logs
   - Look for the error right before "Service restarted"

2. **Common causes:**
   - Missing environment variables
   - Database connection issues
   - Python module import errors
   - Port binding issues

3. **Test locally:**
   ```bash
   cd backend
   export DATABASE_URL="your-neon-url"
   export BETTER_AUTH_SECRET="test-secret-32-chars-min"
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Check dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

---

### Error 10: "Service is slow/timing out"

**Symptoms:**
- First request takes 30-60 seconds
- Subsequent requests are fast
- Happens after 15 minutes of inactivity

**Cause:** Free tier cold starts (NOT an error!)

**Explanation:**
- Free tier services spin down after 15 min idle
- First request wakes the service (30-60 sec)
- This is expected behavior

**Solutions:**

1. **Accept it** (recommended for dev/portfolio):
   - First request is slow, rest are fast
   - Mention in demo: "Free tier - cold start expected"

2. **Keep service awake** (free external service):
   - Use UptimeRobot: https://uptimerobot.com
   - Add monitor for your health endpoint
   - Ping every 5 minutes

3. **Upgrade to paid tier** ($7/month):
   - Render dashboard → todo-api → Settings
   - Change plan to "Starter"
   - Service stays always-on

---

## Debugging Workflow

### Step 1: Check Service Status
```
Dashboard → Services → todo-api
```
- Green = live
- Yellow = deploying
- Red = failed

### Step 2: Read Logs
```
Dashboard → Logs tab
```
- Look for ERROR or CRITICAL messages
- Check the last log before crash
- Note exact error message

### Step 3: Verify Environment
```
Dashboard → Environment tab
```
- DATABASE_URL is set
- BETTER_AUTH_SECRET is set
- CORS_ORIGINS includes your frontend URL

### Step 4: Test Endpoints
```bash
# Health check
curl https://todo-api.onrender.com/health

# Root endpoint
curl https://todo-api.onrender.com/

# API docs (open in browser)
https://todo-api.onrender.com/docs
```

### Step 5: Compare with Local
```bash
# Run locally
cd backend
uvicorn app.main:app --reload

# Test locally
curl http://localhost:8000/health
```

If it works locally but not on Render:
- Environment variable mismatch
- Database connection issue
- Path/directory issue

---

## Environment Variables Debug

### Check Current Values

**Render Dashboard:**
1. Go to: Environment tab
2. Variables are hidden for security
3. Click "Edit" to see truncated values

**Required Variables:**
```
DATABASE_URL=postgresql://...     ✓ Must be set
BETTER_AUTH_SECRET=xxxxx...       ✓ Must be 32+ chars
OPENAI_API_KEY=sk-...             ○ Optional
```

**Auto-set by Render:**
```
PYTHON_VERSION=3.13.0             ✓ From render.yaml
CORS_ORIGINS=[...]                ✓ From render.yaml
PORT=10000                        ✓ Automatic
```

### Test Environment Variable Loading

Add temporary debug endpoint to `backend/app/main.py`:

```python
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint - REMOVE BEFORE PRODUCTION!"""
    from app.config import settings
    return {
        "database_url_set": bool(settings.DATABASE_URL),
        "auth_secret_set": bool(settings.BETTER_AUTH_SECRET),
        "cors_origins": settings.CORS_ORIGINS,
    }
```

Test: `curl https://todo-api.onrender.com/debug/env`

**IMPORTANT:** Remove this endpoint before final deployment!

---

## Performance Optimization

### Free Tier Limitations
- ✅ 750 hours/month compute
- ⚠️ 512 MB RAM
- ⚠️ Shared CPU
- ⚠️ Spins down after 15 min idle

### Optimize for Free Tier

1. **Reduce cold start time:**
   - Keep dependencies minimal
   - Use lazy loading where possible

2. **Optimize database queries:**
   - Add indexes on user_id
   - Limit query results
   - Use connection pooling

3. **Cache responses:**
   - Add caching for frequent queries
   - Use ETags for unchanged resources

---

## Getting Help

### Check Status Pages
- Render Status: https://status.render.com
- Neon Status: https://neonstatus.com

### Documentation
- Render Docs: https://render.com/docs
- Render Python Guide: https://render.com/docs/deploy-fastapi
- Render Blueprints: https://render.com/docs/blueprint-spec

### Community Support
- Render Community: https://community.render.com
- Render Discord: https://discord.gg/render
- GitHub Issues: https://github.com/codewithurooj/full-stack-todo/issues

### Contact Support
- Render Support: support@render.com (paid plans)
- Community support: community.render.com (free tier)

---

## Still Stuck?

1. **Copy exact error message** from logs
2. **Check all environment variables** are set
3. **Test the same setup locally** - does it work?
4. **Search Render community** for similar issues
5. **Check this project's GitHub issues**
6. **Create new issue** with:
   - Error message
   - Logs (remove secrets!)
   - Steps to reproduce

---

## Success Indicators

Your deployment is working when:

- ✅ Dashboard shows "Live" status (green)
- ✅ Health check returns: `{"status": "healthy"}`
- ✅ API docs load at `/docs`
- ✅ Can hit any endpoint without 500 errors
- ✅ Database queries work (test with signup)
- ✅ No CORS errors from frontend
- ✅ Logs show no errors

---

**Most issues are environment variables or CORS - check those first!** 🔍
