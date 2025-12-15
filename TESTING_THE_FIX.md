# Testing the Authentication Fix

## What Was Changed

**File:** `frontend/lib/auth.ts` (Line 29)

**Change:**
```diff
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60, // 5 minutes
+   strategy: "jwt", // Store JWT in cookie (compatible with backend JWT decoding)
  },
```

---

## How to Test

### Step 1: Restart Frontend Server

```bash
# If the frontend is running, stop it (Ctrl+C)
cd C:\Users\pc1\Desktop\full-stack-todo\frontend
npm run dev
```

The server should start on http://localhost:3000

### Step 2: Clear Browser Data

**Option A - Clear All Cookies (Recommended):**
1. Open http://localhost:3000 in your browser
2. Press `F12` to open DevTools
3. Go to **Application** tab
4. In the left sidebar, click **Cookies** > **http://localhost:3000**
5. Right-click and select **Clear**
6. Close DevTools

**Option B - Clear Specific Cookie:**
1. Open DevTools > Application > Cookies
2. Find `better-auth.session_token`
3. Delete it

### Step 3: Sign In Again

1. Go to http://localhost:3000/login
2. Enter your credentials
3. Click "Sign In"

### Step 4: Verify JWT Format

**Open DevTools** (`F12`) and check the cookie:

1. Go to **Application** > **Cookies** > **http://localhost:3000**
2. Find `better-auth.session_token`
3. Click on it to see the value

**Expected Result:**
The cookie value should now look like this:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlY2YyODk1MS04YmMxLTQ1Y...
```

**Key indicators:**
- ✅ Starts with `eyJ` (base64-encoded JWT header)
- ✅ Contains two dots (`.`) separating three parts: `header.payload.signature`
- ✅ Much longer than before

**If you see something like:** `abc123randomtoken` (no dots, shorter)
→ The strategy change didn't take effect. Restart the server again.

### Step 5: Test Task API

1. Navigate to the tasks page (usually http://localhost:3000/tasks or the main page)
2. Try to **create a new task**
3. Try to **view existing tasks**
4. Try to **update a task**
5. Try to **delete a task**

**Expected Result:**
- ✅ No "Invalid token" errors
- ✅ No "Not authenticated" errors
- ✅ All CRUD operations work correctly
- ✅ Tasks are saved and retrieved successfully

### Step 6: Check Browser Console

Open the **Console** tab in DevTools and look for errors.

**Expected Result:**
- ✅ No authentication errors
- ✅ API calls return `200 OK` or `201 Created`
- ✅ No JWT-related errors

---

## Debugging If It Still Fails

### Check Backend Logs

In your backend terminal, you should see logs like:
```
INFO:     127.0.0.1:xxxxx - "GET /api/user123/tasks HTTP/1.1" 200 OK
```

**If you see:**
```
INFO:     127.0.0.1:xxxxx - "GET /api/user123/tasks HTTP/1.1" 401 Unauthorized
```

The authentication is still failing.

### Verify the JWT (Advanced)

1. Copy the `better-auth.session_token` cookie value
2. Go to https://jwt.io
3. Paste the token in the "Encoded" section
4. Check the **Decoded** payload:

**Should contain:**
```json
{
  "sub": "ecf28951-8bc1-45c4-9f11-2fc07cfb6e89", // User ID
  "exp": 1734189000,  // Expiration timestamp
  "iat": 1733584200,  // Issued at timestamp
  // ... other fields
}
```

**Key field:**
- `sub` - This is the user ID that your backend needs
- `exp` - Expiration time (should be in the future)

### Print Backend Token (Debugging)

If it's still not working, add debug logging to the backend:

**File:** `backend/app/middleware/auth.py` (around line 41)

```python
elif "better-auth.session_token" in request.cookies:
    token = request.cookies.get("better-auth.session_token")

    # DEBUG: Print token info
    print(f"\n=== DEBUG: Cookie Token ===")
    print(f"First 50 chars: {token[:50]}...")
    print(f"Token parts: {len(token.split('.'))}")  # Should be 3 for JWT
    print(f"Starts with 'eyJ': {token.startswith('eyJ')}")
    print("===========================\n")
```

**Check backend terminal output:**
- **If `Token parts: 3`** and **`Starts with 'eyJ': True`** → It's a valid JWT format
- **If `Token parts: 1`** → Still getting compact format (server didn't restart)

---

## Success Checklist

After testing, you should be able to:

- ✅ Sign in successfully
- ✅ See JWT-formatted cookie (`eyJ...` with dots)
- ✅ Access the tasks page without errors
- ✅ Create new tasks
- ✅ Read/list all tasks
- ✅ Update existing tasks
- ✅ Delete tasks
- ✅ Toggle task completion
- ✅ No "Invalid token" errors in browser console
- ✅ No 401 errors in network tab

---

## What to Do If It Works

1. **Test all features** thoroughly
2. **Sign out and sign in again** to verify persistence
3. **Test in a different browser** to verify it's not cached
4. **Deploy to production** if everything works locally

---

## What to Do If It Still Fails

1. **Check that frontend restarted** (you should see "compiled successfully" in terminal)
2. **Verify cookies were cleared** (no old session tokens)
3. **Check browser console** for any JavaScript errors
4. **Check backend logs** for specific error messages
5. **Verify both servers are running:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
6. **Double-check the code change** in `frontend/lib/auth.ts` line 29

---

## Common Issues

### "Still getting Invalid token"
→ Old cookie still in browser. Clear all cookies and try again.

### "Cookie value doesn't start with eyJ"
→ Frontend server didn't restart. Stop and start it again.

### "No cookie is being set"
→ Sign out completely, then sign in again.

### "Can't access http://localhost:3000"
→ Frontend server not running. Run `npm run dev` in frontend directory.

### "Can't access http://localhost:8000"
→ Backend server not running. Run `uvicorn app.main:app --reload` in backend directory.

---

## Expected Timeline

- **Step 1-2:** 1 minute (restart + clear cookies)
- **Step 3:** 30 seconds (sign in)
- **Step 4:** 30 seconds (verify JWT)
- **Step 5:** 2 minutes (test all CRUD operations)
- **Total:** ~5 minutes

---

## Need Help?

If you encounter any issues:

1. Check the **browser console** (F12 > Console)
2. Check the **network tab** (F12 > Network) for failed requests
3. Check the **backend terminal** for error logs
4. Review the **AUTHENTICATION_FIX_COMPLETE_ANALYSIS.md** for detailed explanation

---

**You're ONE RESTART away from victory!** 🚀
