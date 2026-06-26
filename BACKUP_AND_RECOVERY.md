# Backup and Recovery — Men and Women of Passion and Purpose

This guide covers backing up and restoring the ministry website's PostgreSQL database and uploaded media files.

## Prerequisites

- PostgreSQL client tools (`pg_dump`, `pg_restore`, `psql`) installed on the backup host
- Access to production `DATABASE_URL` credentials
- SSH or filesystem access to the application server
- Sufficient disk space for database dumps and upload archives

## 1. PostgreSQL Backup Process

### Full logical backup (recommended daily)

```bash
# Set connection details from your production DATABASE_URL
export PGHOST=localhost
export PGPORT=5432
export PGUSER=mwpp_user
export PGPASSWORD='your-password'
export PGDATABASE=mwpp_ministry

# Timestamped custom-format dump (supports parallel restore)
pg_dump -Fc -f "backups/mwpp_$(date +%Y%m%d_%H%M%S).dump" "$PGDATABASE"
```

### Alternative: plain SQL dump

```bash
pg_dump -f "backups/mwpp_$(date +%Y%m%d_%H%M%S).sql" "$PGDATABASE"
```

### Retention

- Keep daily backups for 7 days
- Keep weekly backups for 4 weeks
- Keep monthly backups for 12 months
- Store at least one copy off-server (cloud storage or separate machine)

## 2. PostgreSQL Restore Process

### Restore to a fresh database (custom format)

```bash
# Create empty database
createdb -h "$PGHOST" -U "$PGUSER" mwpp_ministry_restore

# Restore from dump
pg_restore -h "$PGHOST" -U "$PGUSER" -d mwpp_ministry_restore --no-owner --no-privileges backups/mwpp_YYYYMMDD_HHMMSS.dump
```

### Restore from plain SQL

```bash
createdb -h "$PGHOST" -U "$PGUSER" mwpp_ministry_restore
psql -h "$PGHOST" -U "$PGUSER" -d mwpp_ministry_restore -f backups/mwpp_YYYYMMDD_HHMMSS.sql
```

### Point application to restored database

1. Update `DATABASE_URL` in production environment to the restored database
2. Restart Gunicorn / application workers
3. Verify site health (login, events, gallery, APIs)

### Fresh provisioning (no backup — new environment)

```bash
export FLASK_APP=run.py
export FLASK_ENV=production
export SECRET_KEY='your-secret'
export DATABASE_URL='postgresql://user:password@host:5432/mwpp_ministry'
export API_KEY='your-api-key'
export SITE_URL='https://yourdomain.com'
export ALLOWED_ORIGINS='https://yourdomain.com,https://www.yourdomain.com'

flask db upgrade
```

## 3. Uploads Backup Process

User-uploaded files live under the application `static/` tree (gallery images, event banners, leader photos, assignment files, etc.).

### Archive uploads

```bash
cd /path/to/ministry_project

# Full static assets backup
tar -czf "backups/static_$(date +%Y%m%d_%H%M%S).tar.gz" static/

# Uploads-only subset (if you prefer smaller archives)
tar -czf "backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz" \
  static/uploads \
  static/gallery \
  static/events \
  static/leaders \
  static/assignments \
  static/submissions
```

Adjust paths to match directories present on your server. Run `ensure_upload_dirs()` on deploy so expected folders exist.

### Sync to remote storage (optional)

```bash
aws s3 sync static/uploads s3://your-bucket/mwpp/uploads --delete
# or: rsync -avz static/ backup-server:/backups/mwpp/static/
```

## 4. Uploads Restore Process

### From tar archive

```bash
cd /path/to/ministry_project

# Stop application workers during restore to avoid partial writes
# systemctl stop gunicorn  (or your process manager)

tar -xzf backups/static_YYYYMMDD_HHMMSS.tar.gz

# Restore ownership if needed
chown -R www-data:www-data static/

# Restart application
# systemctl start gunicorn
```

### From remote sync

```bash
aws s3 sync s3://your-bucket/mwpp/uploads static/uploads
```

After restore, verify gallery images, event banners, and leader photos render correctly in the browser.

## 5. Disaster Recovery Checklist

Use this checklist when recovering from server loss, database corruption, or accidental deletion.

### Immediate response

- [ ] Identify scope: database only, uploads only, or full system
- [ ] Take application offline or enable maintenance mode if partial data loss is suspected
- [ ] Notify stakeholders of estimated downtime

### Database recovery

- [ ] Locate most recent valid `pg_dump` backup
- [ ] Provision PostgreSQL instance (or use existing standby)
- [ ] Create empty database
- [ ] Run `pg_restore` or `psql` restore
- [ ] Set `DATABASE_URL` and run `flask db upgrade` if schema drift is possible
- [ ] Smoke-test: admin login, events list, contact messages, donations

### Uploads recovery

- [ ] Locate most recent static/uploads archive or S3 sync
- [ ] Extract to application `static/` directory
- [ ] Confirm file permissions for the web/worker user
- [ ] Smoke-test: gallery lightbox, event banners, leadership photos

### Application recovery

- [ ] Redeploy application code from version control
- [ ] Restore `.env` / secrets: `SECRET_KEY`, `DATABASE_URL`, `API_KEY`, mail and payment keys
- [ ] Run `flask db upgrade` on fresh installs
- [ ] Start Gunicorn per `DEPLOYMENT.md`
- [ ] Verify HTTPS, logging, and error pages

### Post-recovery validation

- [ ] Login and registration work
- [ ] Prayer and contact form submissions succeed
- [ ] Public events and gallery pages load
- [ ] WOP App download page loads
- [ ] API read endpoints respond; write endpoints require `X-API-Key` in production
- [ ] Admin CRUD operations function
- [ ] Document incident, root cause, and backup gap remediation

### Ongoing prevention

- [ ] Automate daily `pg_dump` with off-site copy
- [ ] Automate weekly static archive or S3 sync
- [ ] Test restore procedure quarterly on a staging environment
- [ ] Monitor backup job success and alert on failure

## Related documentation

- `DEPLOYMENT.md` — production deployment and environment variables
- `.env.example` — required production settings including `API_KEY`
