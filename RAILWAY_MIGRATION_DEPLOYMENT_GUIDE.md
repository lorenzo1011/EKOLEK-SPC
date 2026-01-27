# Railway Migration Deployment Guide
## Deploy Game API Database Changes to Production

**Date:** January 27, 2026  
**Migration:** `game/migrations/0002_usergamecooldown_alter_gamesession_options_and_more.py`  
**Status:** ✅ Ready to Deploy

---

## 📋 What Will Be Deployed

This migration adds support for separate game types (quiz vs drag_drop):

### New Database Changes:
1. ✅ **New Table:** `UserGameCooldown` - tracks per-game cooldowns
2. ✅ **New Field:** `GameSession.game_type` (quiz/drag_drop)
3. ✅ **New Field:** `GameSession.game_name` (display name)
4. ✅ **New Index:** On (user, game_type, -completed_at) for performance
5. ✅ **Unique Constraint:** On UserGameCooldown (user, game_type)

---

## 🚀 Deployment Steps

### Step 1: Verify Local Changes
```bash
# Check that migration exists
dir game\migrations\0002_*.py

# Expected output: 0002_usergamecooldown_alter_gamesession_options_and_more.py
```

### Step 2: Check Git Status
```bash
git status
```

**Expected to see:**
- `game/models.py` (modified)
- `game/views.py` (modified)
- `game/admin.py` (modified)
- `game/migrations/0002_usergamecooldown_alter_gamesession_options_and_more.py` (new)

### Step 3: Stage Changes for Commit
```bash
# Add all game-related changes
git add game/models.py
git add game/views.py
git add game/admin.py
git add game/migrations/0002_usergamecooldown_alter_gamesession_options_and_more.py

# Verify staged files
git status
```

### Step 4: Commit Changes
```bash
git commit -m "feat: Add game_type support for quiz and drag_drop games

- Add game_type and game_name fields to GameSession
- Create UserGameCooldown model for per-game tracking
- Update save_game_session to handle game_type
- Add game-specific notification templates
- Enhance admin interfaces for game management
- Migration: 0002_usergamecooldown_alter_gamesession_options_and_more"
```

### Step 5: Push to Railway
```bash
# Push to main/master branch (Railway watches this)
git push origin master

# If your main branch is called 'main':
git push origin main
```

### Step 6: Monitor Railway Deployment
1. Open Railway dashboard: https://railway.app/
2. Go to your project
3. Click on your service
4. Go to "Deployments" tab
5. Watch the latest deployment

**Expected logs:**
```
Building...
Installing dependencies...
Running migrations...
  ✓ Applying game.0002_usergamecooldown_alter_gamesession_options_and_more... OK
Starting server...
```

### Step 7: Verify Migration Applied
```bash
# SSH into Railway (if you have Railway CLI)
railway run python manage.py showmigrations game

# Expected output:
# game
#  [X] 0001_initial
#  [X] 0002_usergamecooldown_alter_gamesession_options_and_more
```

**Alternative:** Check using Railway dashboard:
- Go to "Data" tab
- Check if `game_usergamecooldown` table exists
- Check if `game_gamesession` has `game_type` and `game_name` columns

---

## ✅ Post-Deployment Verification

### Test 1: Check Database Schema
**Via Railway Dashboard:**
1. Open Railway project
2. Go to PostgreSQL database
3. Click "Query" or use PGAdmin
4. Run:
```sql
-- Check new table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'game_usergamecooldown';
-- Expected: 1 row

-- Check new fields exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'game_gamesession' 
  AND column_name IN ('game_type', 'game_name');
-- Expected: 2 rows
```

### Test 2: Setup Game Configurations
**Via Railway CLI or SSH:**
```bash
# Setup default cooldown configurations
railway run python manage.py setup_game_cooldowns --active
```

**Expected output:**
```
✅ Created configuration for Quiz Game (72 hours)
✅ Created configuration for Drag & Drop Game (72 hours)
✅ Created configuration for All Games (default: 72 hours)

Game configurations set up successfully!
```

### Test 3: Test API with Quiz Game
```bash
# Get a test token first
curl -X POST https://e-kolek-production.up.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_test_user",
    "password": "your_password"
  }'

# Save the access token from response
# Then test quiz game submission:

curl -X POST https://e-kolek-production.up.railway.app/api/game/save-session/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 50,
    "correct_answers": 10,
    "wrong_answers": 2,
    "accuracy": 83.33,
    "duration_seconds": 120,
    "game_type": "quiz",
    "game_id": "quiz",
    "game_name": "Quiz Game"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "game_type": "quiz",
  "game_name": "Quiz Game",
  "new_total_points": 50,
  "points_earned": 50
}
```

### Test 4: Verify Notification
```bash
curl https://e-kolek-production.up.railway.app/api/notifications/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected:** Latest notification should say "quiz game" not "waste sorting game"

### Test 5: Test Drag & Drop Game
```bash
curl -X POST https://e-kolek-production.up.railway.app/api/game/save-session/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 75,
    "game_type": "drag_drop",
    "game_name": "Waste Sorting Game"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "game_type": "drag_drop",
  "game_name": "Waste Sorting Game"
}
```

**Expected Notification:** Should say "waste sorting game"

---

## 🐛 Troubleshooting

### Issue: Migration Not Running
**Symptoms:**
- Railway logs show "No migrations to apply"
- Database schema unchanged

**Solutions:**
1. Check that migration file was committed:
   ```bash
   git ls-files game/migrations/0002_*.py
   ```
2. Check Railway environment variables:
   - `DATABASE_URL` should be set
3. Force migration:
   ```bash
   railway run python manage.py migrate game --fake-initial
   ```

### Issue: Migration Fails
**Symptoms:**
- Error: "relation already exists"
- Error: "column already exists"

**Solutions:**
1. Check if migration was partially applied:
   ```bash
   railway run python manage.py showmigrations game
   ```
2. If needed, fake the migration:
   ```bash
   railway run python manage.py migrate game 0002 --fake
   ```

### Issue: 500 Error After Deployment
**Symptoms:**
- API returns 500 Internal Server Error
- Railway logs show "ProgrammingError: relation does not exist"

**Solutions:**
1. Check Railway logs for migration status
2. Manually run migrations:
   ```bash
   railway run python manage.py migrate
   ```
3. Restart Railway service

### Issue: Old Game Sessions Have NULL game_type
**Symptoms:**
- Database query fails on old records
- Errors about NULL values

**Solution:**
This is expected! The migration sets `default='drag_drop'` for old records. Verify:
```sql
SELECT game_type, COUNT(*) 
FROM game_gamesession 
GROUP BY game_type;
```

If you see NULL values, run:
```sql
UPDATE game_gamesession 
SET game_type = 'drag_drop', game_name = 'Waste Sorting Game'
WHERE game_type IS NULL;
```

---

## 📊 Monitoring Post-Deployment

### Railway Dashboard Checks
1. **Logs Tab:** Monitor for errors
2. **Metrics Tab:** Check for increased error rates
3. **Database Tab:** Verify table/column creation

### Database Health Check
```sql
-- Count records by game type
SELECT game_type, COUNT(*) 
FROM game_gamesession 
GROUP BY game_type;

-- Check cooldown tracking
SELECT COUNT(*) 
FROM game_usergamecooldown;

-- Verify indexes
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'game_gamesession';
```

### API Health Check
```bash
# Test endpoint availability
curl -I https://e-kolek-production.up.railway.app/api/game/save-session/

# Expected: HTTP/1.1 405 Method Not Allowed (GET not allowed, POST required)
# This confirms endpoint exists
```

---

## 📝 Rollback Plan (If Needed)

If deployment causes critical issues:

### Step 1: Revert Code
```bash
# Revert to previous commit
git revert HEAD
git push origin master
```

### Step 2: Revert Migration
```bash
# Via Railway CLI
railway run python manage.py migrate game 0001

# This will undo:
# - Drop game_usergamecooldown table
# - Remove game_type and game_name columns
# - Remove indexes
```

### Step 3: Verify Rollback
```bash
railway run python manage.py showmigrations game
```

**Expected:**
```
game
 [X] 0001_initial
 [ ] 0002_usergamecooldown_alter_gamesession_options_and_more
```

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ Railway build completes without errors
2. ✅ Migration `0002_usergamecooldown...` shows as applied
3. ✅ `game_usergamecooldown` table exists in database
4. ✅ `game_gamesession` has `game_type` and `game_name` columns
5. ✅ Quiz game submission creates session with `game_type='quiz'`
6. ✅ Drag & Drop game creates session with `game_type='drag_drop'`
7. ✅ Notifications show correct game names
8. ✅ Cooldowns are tracked separately per game
9. ✅ No 500 errors in Railway logs
10. ✅ Admin interface shows game_type fields

---

## 📞 Support

**If you encounter issues:**

1. **Check Railway Logs:**
   - Railway Dashboard → Deployments → Latest build → Logs

2. **Check Django Logs:**
   - Look for migration errors
   - Look for database errors

3. **Verify Environment:**
   - `DATABASE_URL` is set correctly
   - PostgreSQL service is running
   - No connection errors

4. **Test Locally First:**
   - Run migrations on local copy of production database
   - Test API endpoints locally
   - Verify no errors before pushing

---

## 🎯 Next Steps After Deployment

Once migration is deployed successfully:

1. **Update Flutter App:**
   - Ensure it sends `game_type` in payload
   - Update to handle separate cooldowns per game

2. **Configure Cooldowns:**
   - Django Admin → Game Configurations
   - Set desired cooldown durations for each game

3. **Monitor Usage:**
   - Check if users are playing both games
   - Verify cooldowns work correctly
   - Monitor for any errors

4. **Test Edge Cases:**
   - User plays quiz then drag_drop
   - Cooldown expiry for each game
   - Invalid game_type rejection

---

## 📚 Related Documentation

- [GAME_API_IMPLEMENTATION_COMPLETE.md](GAME_API_IMPLEMENTATION_COMPLETE.md) - Full implementation details
- [API_TEST_COMMANDS.md](API_TEST_COMMANDS.md) - Manual testing commands
- [game/models.py](game/models.py) - Model definitions
- [game/views.py](game/views.py) - API endpoint implementation

---

**Deployment Ready:** ✅ YES  
**Breaking Changes:** ❌ NO (backward compatible)  
**Downtime Required:** ❌ NO (zero-downtime deployment)  
**Database Backup Recommended:** ✅ YES (Railway auto-backs up)

---

**Good luck with the deployment! 🚀**
