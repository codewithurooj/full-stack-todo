# Database Migrations

This directory contains all database migration scripts for the Full-Stack Todo Application.

## Migration Files

### Migration 002: Priority and Tags
- **002_add_priority_tags.sql** - Add priority and tags columns to tasks table
- **002_add_priority_tags_rollback.sql** - Rollback priority and tags

### Migration 003: Due Dates and Reminders
- **003_add_due_dates_reminders.sql** - Add due date and reminder fields
- **003_add_due_dates_reminders_rollback.sql** - Rollback due dates and reminders

### Migration 004: Kafka Event-Driven Architecture
- **004_add_kafka_event_schema.sql** - Forward migration (apply changes)
- **004_add_kafka_event_schema_rollback.sql** - Rollback migration (undo changes)
- **004_validate.sql** - Validation queries (verify success)
- **004_MIGRATION_GUIDE.md** - Comprehensive migration documentation
- **004_TESTING_CHECKLIST.md** - Complete testing checklist

**Feature:** 011-kafka-event-architecture
**Changes:**
- Creates `audit_logs` table with 6 indexes
- Creates `notification_subscriptions` table with 2 indexes
- Adds idempotency constraint to `tasks` table
- Total: 2 new tables, 8 new indexes, 3 foreign keys, 2 check constraints

**Risk Level:** Low (backward compatible, zero downtime)

---

## Quick Start

### Apply Migration
```bash
# Development
psql $DATABASE_URL -f 004_add_kafka_event_schema.sql

# Production
psql $PROD_DATABASE_URL -f 004_add_kafka_event_schema.sql
```

### Validate Migration
```bash
psql $DATABASE_URL -f 004_validate.sql
```

### Rollback (if needed)
```bash
psql $DATABASE_URL -f 004_add_kafka_event_schema_rollback.sql
```

---

## Migration Naming Convention

Format: `{version}_{description}.sql`

Examples:
- `004_add_kafka_event_schema.sql` (forward)
- `004_add_kafka_event_schema_rollback.sql` (rollback)
- `004_validate.sql` (validation)

---

## Best Practices

1. **Always backup before migration**
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

2. **Test on dev/staging first**
   ```bash
   psql $DEV_DATABASE_URL -f migration.sql
   ```

3. **Run validation queries**
   ```bash
   psql $DATABASE_URL -f validate.sql
   ```

4. **Monitor after migration**
   - Check application logs
   - Monitor database metrics
   - Verify API health

5. **Know how to rollback**
   ```bash
   psql $DATABASE_URL -f rollback.sql
   ```

---

## Migration Checklist

Before running any migration in production:

- [ ] Tested on development database
- [ ] Tested on staging database
- [ ] Validation queries pass
- [ ] Rollback script tested
- [ ] Database backup completed
- [ ] Team notified
- [ ] Monitoring alerts configured
- [ ] Documentation updated

---

## Getting Help

- Review migration guide: `004_MIGRATION_GUIDE.md`
- Review testing checklist: `004_TESTING_CHECKLIST.md`
- Check validation queries: `004_validate.sql`
- Contact DevOps team if issues arise

---

**Last Updated:** 2026-01-12
