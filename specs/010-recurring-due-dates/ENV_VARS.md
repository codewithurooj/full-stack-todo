# Environment Variables - Feature 010

## Backend Environment Variables

### Required for Production

None required for Phase 1 (database schema only).

### Optional Configuration (Future Phases)

The following environment variables will be used in later implementation phases:

#### APScheduler Configuration (Phase 2+)
```env
# Job scheduler timezone (default: UTC)
SCHEDULER_TIMEZONE=UTC

# Job store configuration (default: in-memory, production should use PostgreSQL)
SCHEDULER_JOBSTORE_TYPE=memory
# SCHEDULER_JOBSTORE_TYPE=postgresql  # For production

# Maximum concurrent jobs (default: 10)
SCHEDULER_MAX_WORKERS=10

# Misfire grace time in seconds (default: 60)
SCHEDULER_MISFIRE_GRACE_TIME=60
```

#### Notification Service Configuration (Phase 4+)
```env
# Enable/disable browser notifications (default: true)
ENABLE_NOTIFICATIONS=true

# Default reminder offset in minutes before due date (default: 60)
DEFAULT_REMINDER_OFFSET=60

# Notification retry attempts for failed deliveries (default: 3)
NOTIFICATION_MAX_RETRIES=3
```

#### Recurring Task Configuration (Phase 5+)
```env
# Enable recurring task auto-generation (default: true)
ENABLE_RECURRING_TASKS=true

# Backfill window in days for missed recurring instances (default: 7)
RECURRING_BACKFILL_DAYS=7

# Maximum instances to generate per recurring task (default: 10)
RECURRING_MAX_INSTANCES=10
```

---

## Frontend Environment Variables

### Required for Production

```env
# API base URL (required)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Optional Configuration

```env
# Enable browser notifications (default: true)
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true

# User timezone detection (default: auto from browser)
NEXT_PUBLIC_DEFAULT_TIMEZONE=America/New_York
```

---

## Development Environment

### Backend `.env`
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key

# Feature 010 - All defaults work for development
# SCHEDULER_TIMEZONE=UTC
# ENABLE_NOTIFICATIONS=true
# ENABLE_RECURRING_TASKS=true
```

### Frontend `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-key-min-32-chars

# Feature 010
# NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true
# NEXT_PUBLIC_DEFAULT_TIMEZONE=America/New_York
```

---

## Production Environment

### Backend (Railway/Render)
```env
DATABASE_URL=postgresql://user:password@prod.neon.tech/dbname
BETTER_AUTH_SECRET=<32-char-secret>
OPENAI_API_KEY=sk-prod-key

# Feature 010 Production Settings
SCHEDULER_TIMEZONE=UTC
SCHEDULER_JOBSTORE_TYPE=postgresql
SCHEDULER_MAX_WORKERS=20
ENABLE_NOTIFICATIONS=true
ENABLE_RECURRING_TASKS=true
RECURRING_BACKFILL_DAYS=7
NOTIFICATION_MAX_RETRIES=3
```

### Frontend (Vercel)
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
BETTER_AUTH_SECRET=<same-as-backend>

# Feature 010
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true
```

---

## Environment Variable Validation

### Backend Validation (app/config.py)

```python
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # Existing settings
    DATABASE_URL: str
    BETTER_AUTH_SECRET: str
    OPENAI_API_KEY: str = ""

    # Feature 010: Scheduler settings
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_JOBSTORE_TYPE: Literal["memory", "postgresql"] = "memory"
    SCHEDULER_MAX_WORKERS: int = 10
    SCHEDULER_MISFIRE_GRACE_TIME: int = 60

    # Feature 010: Notification settings
    ENABLE_NOTIFICATIONS: bool = True
    DEFAULT_REMINDER_OFFSET: int = 60
    NOTIFICATION_MAX_RETRIES: int = 3

    # Feature 010: Recurring task settings
    ENABLE_RECURRING_TASKS: bool = True
    RECURRING_BACKFILL_DAYS: int = 7
    RECURRING_MAX_INSTANCES: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## Security Considerations

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Rotate secrets regularly** - Especially `BETTER_AUTH_SECRET`
3. **Use different secrets per environment** - Dev, staging, production
4. **Validate timezone strings** - Use pytz to verify valid timezones
5. **Limit worker counts** - Prevent resource exhaustion

---

## Migration Notes

### Phase 1 (Current)
- No new environment variables required
- Database migration adds schema only
- Existing `DATABASE_URL` is sufficient

### Phase 2 (Scheduler Setup)
- Add scheduler configuration
- Test with in-memory job store first
- Switch to PostgreSQL job store in production

### Phase 4 (Notifications)
- Enable notification settings
- Configure retry logic
- Test browser notification permissions

### Phase 5 (Recurring Tasks)
- Enable recurring task settings
- Configure backfill window
- Test auto-generation logic

---

## Troubleshooting

### Common Issues

**Problem:** Scheduler jobs not executing
- **Solution:** Check `SCHEDULER_TIMEZONE` matches your database timezone
- **Verify:** Run `SELECT now()` in PostgreSQL to check server time

**Problem:** Notifications not delivered
- **Solution:** Verify `ENABLE_NOTIFICATIONS=true` and browser permissions granted
- **Check:** Frontend console for Notification API errors

**Problem:** Recurring tasks not generating
- **Solution:** Check `ENABLE_RECURRING_TASKS=true` and scheduler is running
- **Verify:** Check logs for APScheduler startup messages

---

## References

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [pytz Timezone List](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- [Browser Notification API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**Last Updated:** 2026-01-09 (Feature 010 - Phase 1 Setup)
