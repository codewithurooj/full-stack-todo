# Authentication "Invalid Token" - Root Cause Analysis & Fix

## Investigation Summary

After 3 days of authentication issues, I've identified the **EXACT ROOT CAUSE** of the "Invalid token" error.

---

## Critical Discovery: Better Auth Does NOT Use JWT by Default! 🔥

### The Problem

Your backend is trying to decode the session token as a JWT, but **Better Auth stores a simple session token (NOT a JWT) in the cookie by default**.

### Evidence

1. **Better Auth Session Table Structure:**
   ```
   Session table schema:
     id: text
     userId: text
     expiresAt: timestamp without time zone
     token: text          ← This is a random token, NOT a JWT
     ipAddress: text
     userAgent: text
     createdAt: timestamp without time zone
     updatedAt: timestamp without time zone
   ```

2. **Better Auth Documentation:**
   - Better Auth uses **sessions by default**, not JWTs
   - The JWT plugin is **optional** and must be explicitly enabled
   - Quote from docs: "This plugin is not meant as a replacement for the session. It's meant to be used for services that require JWT tokens."
   - The session token is a **reference token** that maps to database session data, not a self-contained JWT

3. **Cookie Cache Encoding:**
   - When `cookieCache` is enabled, Better Auth can encode session data in 3 formats:
     - `compact` (default): base64url with HMAC signature - **NOT a JWT**
     - `jwt`: Standard JWT (HS256) - Must be explicitly configured
     - `jwe`: Encrypted JWE - Must be explicitly configured

4. **Your Current Configuration** (`frontend/lib/auth.ts`):
   ```typescript
   session: {
     expiresIn: 60 * 60 * 24 * 7, // 7 days
     updateAge: 60 * 60 * 24, // 1 day
     cookieCache: {
       enabled: true,
       maxAge: 5 * 60, // 5 minutes
     },
     // ❌ NO strategy specified, defaults to "compact" (NOT JWT)
   }
   ```

---

## Why Your Backend Fails

**Location:** `C:\Users\pc1\Desktop\full-stack-todo\backend\app\middleware\auth.py` (Lines 53-56)

```python
# This code tries to decode the token as a JWT:
payload = jwt.decode(
    token,                        # ← This is a simple session token, NOT a JWT!
    settings.BETTER_AUTH_SECRET,
    algorithms=["HS256"]
)
```

**Result:** `jwt.InvalidTokenError` because the token is NOT in JWT format.

---

## Environment Variables Status ✅

**Frontend** (`.env.local`):
```env
BETTER_AUTH_SECRET=NdqKa4dKGIaZRy0W7qLmpKsFxj903xPcLrJIvP44Hqa4xack5FZO82xYpejZaEZe
```

**Backend** (`.env`):
```env
BETTER_AUTH_SECRET=NdqKa4dKGIaZRy0W7qLmpKsFxj903xPcLrJIvP44Hqa4xack5FZO82xYpejZaEZe
```

✅ **Secrets MATCH** - This is not the problem!

---

## The Real Issue: Architecture Mismatch

You have **two fundamentally incompatible approaches**:

### Frontend:
- Better Auth with session-based authentication
- Stores a **session token** in cookie
- Session token references database session record

### Backend:
- FastAPI expecting **JWT tokens**
- Tries to decode and extract user_id from JWT payload
- No database lookup for session validation

---

## Solution Options

### Option 1: Enable JWT Strategy in Better Auth (RECOMMENDED) ⭐

Make Better Auth store actual JWTs in the cookie cache.

**File:** `C:\Users\pc1\Desktop\full-stack-todo\frontend\lib\auth.ts`

**Change:**
```typescript
session: {
  expiresIn: 60 * 60 * 24 * 7, // 7 days
  updateAge: 60 * 60 * 24, // 1 day
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60, // 5 minutes
    strategy: "jwt",  // ← ADD THIS LINE
  },
},
```

**What this does:**
- Better Auth will now encode session data as a **real JWT** in the cookie
- The JWT will contain `sub` (user ID) and other session data
- Your backend JWT decoding will work correctly
- No database lookup needed for every request

**Pros:**
- ✅ Minimal code changes
- ✅ Backend stays the same
- ✅ Stateless authentication (faster)
- ✅ Works with your current architecture

**Cons:**
- ⚠️ Cookie size increases slightly (JWT is larger than compact format)
- ⚠️ Must restart frontend dev server

---

### Option 2: Backend Session Validation (Alternative)

Rewrite backend to validate session tokens via database lookup.

**File:** `C:\Users\pc1\Desktop\full-stack-todo\backend\app\middleware\auth.py`

**Complete rewrite needed:**
```python
async def get_current_user_id(
    request: Request,
    session: Session = Depends(get_session)
) -> str:
    """Validate Better Auth session token via database"""

    # Get session token from cookie
    token = request.cookies.get("better-auth.session_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token"
        )

    # Query Better Auth session table
    statement = select(BetterAuthSession).where(
        BetterAuthSession.token == token,
        BetterAuthSession.expiresAt > datetime.utcnow()
    )
    db_session = session.exec(statement).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return db_session.userId
```

**Pros:**
- ✅ Uses Better Auth exactly as designed
- ✅ Session revocation works properly
- ✅ More secure (sessions can be invalidated server-side)

**Cons:**
- ❌ Requires database query on EVERY request (slower)
- ❌ Need to create SQLModel for Better Auth session table
- ❌ More complex backend code
- ❌ Not stateless

---

## Recommended Fix (Step-by-Step)

### Step 1: Enable JWT Strategy

**Edit:** `C:\Users\pc1\Desktop\full-stack-todo\frontend\lib\auth.ts`

**Find this section (lines 23-30):**
```typescript
session: {
  expiresIn: 60 * 60 * 24 * 7, // 7 days
  updateAge: 60 * 60 * 24, // 1 day
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60, // 5 minutes
  },
},
```

**Replace with:**
```typescript
session: {
  expiresIn: 60 * 60 * 24 * 7, // 7 days
  updateAge: 60 * 60 * 24, // 1 day
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60, // 5 minutes
    strategy: "jwt", // ← ADD THIS LINE: Store JWT instead of compact format
  },
},
```

### Step 2: Restart Frontend

```bash
# Stop the frontend dev server (Ctrl+C)
cd C:\Users\pc1\Desktop\full-stack-todo\frontend
npm run dev
```

### Step 3: Clear Browser Cookies

1. Open your app in browser
2. Open DevTools (F12)
3. Go to Application > Cookies
4. Delete all `better-auth.*` cookies
5. Refresh the page

### Step 4: Test Authentication

1. **Sign out** (if logged in)
2. **Sign in** again
3. **Inspect the cookie** in DevTools:
   - Name: `better-auth.session_token`
   - Value: Should now look like `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...` (JWT format)
4. **Try to access tasks** - should work now!

### Step 5: Verify JWT Format

You can decode the JWT at https://jwt.io to verify:
- It should have `sub` field with user ID
- It should be signed with HS256
- It should have `exp` (expiration) field

---

## Expected Results After Fix

### Before (Current State):
1. Cookie contains: `abc123randomtoken` (compact format)
2. Backend tries to decode as JWT → ❌ **"Invalid token"**

### After (With JWT Strategy):
1. Cookie contains: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzM0MTg5MDAwfQ.signature` (JWT format)
2. Backend decodes JWT → ✅ **Gets user_id from `sub` claim**
3. Backend validates user_id → ✅ **Request succeeds**

---

## Alternative Quick Test

If you want to verify this is the issue without making changes, you can:

1. **Print the raw token** in your backend middleware:
   ```python
   # In auth.py around line 41
   token = request.cookies.get("better-auth.session_token")
   print(f"RAW TOKEN: {token[:50]}...")  # Print first 50 chars

   # Try to decode
   import base64
   try:
       parts = token.split('.')
       print(f"TOKEN HAS {len(parts)} PARTS")  # JWT should have 3 parts
   except:
       print("TOKEN IS NOT DOT-SEPARATED")
   ```

2. **Check the output:**
   - If it shows `TOKEN HAS 1 PARTS` or `TOKEN IS NOT DOT-SEPARATED` → Confirms it's not a JWT
   - If it shows `TOKEN HAS 3 PARTS` → It is a JWT (something else is wrong)

---

## Technical Background

### What Better Auth Actually Stores

Better Auth has two layers:

1. **Database Session** (always exists):
   - Stored in `session` table
   - Contains: `id`, `userId`, `token`, `expiresAt`, `ipAddress`, `userAgent`
   - The `token` field is a random string (not JWT)

2. **Cookie Cache** (optional optimization):
   - Reduces database lookups
   - Can encode session data in cookie using 3 strategies:
     - **compact** (default): Custom base64url format - NOT JWT compatible
     - **jwt**: Standard JWT (HS256) - Works with your backend
     - **jwe**: Encrypted JWT - Would need different backend decoding

### Why JWT Strategy Solves Your Problem

When you set `strategy: "jwt"`:
- Better Auth creates a **real JWT** with the session data
- The JWT payload includes:
  ```json
  {
    "sub": "user_id_here",  ← Your backend reads this
    "exp": 1734189000,      ← Expiration timestamp
    "iat": 1733584200,      ← Issued at
    // ... other session data
  }
  ```
- This JWT is signed with `BETTER_AUTH_SECRET` using HS256
- Your backend can decode it without any database lookup
- The `sub` claim contains the user ID your backend needs

---

## Summary

### Root Cause:
**Better Auth stores a session token (NOT JWT) by default. Your backend expects JWT.**

### The Fix:
**Add `strategy: "jwt"` to Better Auth cookie cache config.**

### Why It Works:
**Better Auth will now store actual JWTs that your backend can decode.**

### Complexity:
**One line of code + restart frontend.**

---

## References

Sources consulted:
- [Better Auth Session Management](https://www.better-auth.com/docs/concepts/session-management)
- [Better Auth Cookies](https://www.better-auth.com/docs/concepts/cookies)
- [Better Auth JWT Plugin](https://www.better-auth.com/docs/plugins/jwt)
- [Better Auth 1.4 Release Notes](https://www.better-auth.com/blog/1-4)

---

## Next Steps

1. ✅ Make the one-line change to `frontend/lib/auth.ts`
2. ✅ Restart frontend dev server
3. ✅ Clear browser cookies
4. ✅ Test login and task access
5. ✅ Celebrate after 3 days! 🎉

The fix is literally **ONE LINE OF CODE**. You've been so close!
