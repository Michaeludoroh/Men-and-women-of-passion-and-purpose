# Admin 500 Error Fix Plan - Database Schema Sync

## Problem
500 error on /admin/ due to missing `donation.gateway` column in SQLite DB. Model expects it but table doesn't have it.

## Immediate Fix Steps (Run these in VSCode terminal from project root)

1. **Switch to project dir:**
   ```
   cd ministry_project
   ```

2. **Set Flask CLI context:**
   ```
   set FLASK_APP=run.py
   ```

3. **Init migrations (creates migrations/ dir):**
   ```
   flask db init
   ```

4. **Create migration for schema changes:**
   ```
   flask db migrate -m "add donation gateway column"
   ```

5. **Apply migration:**
   ```
   flask db upgrade
   ```

6. **Restart app:**
   ```
   python run.py
   ```

7. **Test:** Login, visit http://127.0.0.1:5000/admin/ - stats should load.

## Alternative Quick Fix (if no data loss OK)
If no important donation data:
```
rm database/site.db
python run.py
```
db.create_all() will recreate tables with current schema.

## Prevention
Delete `db.create_all()` after migrations work, rely on `flask db upgrade`.

Approve to execute or run these commands manually.
