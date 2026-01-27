# ✅ Game API Implementation Complete - Testing Guide

## 🎯 Summary of Changes

All requested fixes have been successfully implemented:

### ✅ 1. GameSession Model Updated
- **Added Fields:**
  - `game_type` (CharField): Required field to distinguish between 'quiz' and 'drag_drop'
  - `game_name` (CharField): User-friendly display name (e.g., "Quiz Game", "Waste Sorting Game")
- **Added Metadata:**
  - `Meta.ordering`: Sessions ordered by most recent first
  - `Meta.indexes`: Optimized for querying by user + game_type

### ✅ 2. UserGameCooldown Model Created
- **Purpose:** Track when each user last played each game type separately
- **Features:**
  - Unique constraint on (user, game_type)
  - `can_play_again()` method checks if cooldown has expired
  - `update_or_create_cooldown()` updates cooldown timestamp after game completion
  - Integrates with GameConfiguration for per-game cooldown settings

### ✅ 3. save_game_session View Updated
- **Extracts from Flutter Payload:**
  - `game_type` (required: 'quiz' or 'drag_drop')
  - `game_id` (fallback if game_type not provided)
  - `game_name` (optional user-friendly label)
- **Validation:**
  - Validates game_type is one of ['quiz', 'drag_drop']
  - Returns 400 error for invalid game_type
- **Game-Specific Notifications:**
  - Quiz: "You earned X points from playing the quiz game!"
  - Drag & Drop: "You earned X points from playing the waste sorting game!"
  - Custom: Uses game_name if provided
- **Cooldown Tracking:**
  - Updates UserGameCooldown record for the specific game_type
  - Enables separate cooldowns per game
- **Response Includes:**
  - `game_type` (echoed back for debugging)
  - `game_name` (echoed back)
  - `session_id`, `new_total_points`, `points_earned`

### ✅ 4. Admin Interface Enhanced
- **GameSession Admin:**
  - Shows game_type and game_name in list view
  - Filter by game_type
  - Search by user and game_name
- **UserGameCooldown Admin:**
  - Visual status indicator (✅ Can play / ❌ Cooldown)
  - Shows time remaining in human-readable format
  - Filter by game_type and last_played_at
- **GameConfiguration Admin:**
  - Existing - controls cooldown duration per game type

### ✅ 5. Database Migrations Applied
Migration created and applied: `0002_usergamecooldown_alter_gamesession_options_and_more.py`

---

## 🧪 API Testing

### Endpoint: `POST /api/game/save-session/`

### Test 1: Quiz Game Submission

**Request:**
```json
POST /api/game/save-session/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "score": 50,
  "correct_answers": 10,
  "wrong_answers": 2,
  "accuracy": 83.33,
  "duration_seconds": 120,
  "game_type": "quiz",
  "game_id": "quiz",
  "game_name": "Quiz Game"
}
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "c9bfcb11-440e-4649-b736-d27a4e2c0d74",
  "game_type": "quiz",
  "game_name": "Quiz Game",
  "new_total_points": 50,
  "points_earned": 50
}
```

**Expected Notification:**
- Message: "You earned 50 points from playing the quiz game!"
- Type: "game"
- Points: 50

**Expected Database:**
- GameSession created with `game_type='quiz'`
- UserGameCooldown updated for `game_type='quiz'`

---

### Test 2: Drag & Drop Game Submission

**Request:**
```json
POST /api/game/save-session/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "score": 75,
  "correct_answers": 15,
  "wrong_answers": 3,
  "accuracy": 83.33,
  "duration_seconds": 180,
  "game_type": "drag_drop",
  "game_id": "drag_drop",
  "game_name": "Waste Sorting Game"
}
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "b2e0fd38-0a3c-497c-9711-4ceef8f41af1",
  "game_type": "drag_drop",
  "game_name": "Waste Sorting Game",
  "new_total_points": 125,
  "points_earned": 75
}
```

**Expected Notification:**
- Message: "You earned 75 points from playing the waste sorting game!"
- Type: "game"
- Points: 75

**Expected Database:**
- GameSession created with `game_type='drag_drop'`
- UserGameCooldown updated for `game_type='drag_drop'`

---

### Test 3: Invalid Game Type

**Request:**
```json
POST /api/game/save-session/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "score": 50,
  "game_type": "invalid_game"
}
```

**Expected Response (400 Error):**
```json
{
  "success": false,
  "error": "Invalid game_type. Must be one of: quiz, drag_drop",
  "error_code": "INVALID_GAME_TYPE"
}
```

---

### Test 4: Missing Game Type (Backward Compatibility)

**Request:**
```json
POST /api/game/save-session/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "score": 50,
  "correct_answers": 10,
  "wrong_answers": 2,
  "accuracy": 83.33,
  "duration_seconds": 120
}
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "...",
  "game_type": "drag_drop",
  "game_name": "Waste Sorting Game",
  "new_total_points": 50,
  "points_earned": 50
}
```

**Note:** Defaults to 'drag_drop' for backward compatibility with existing Flutter code.

---

## 🎮 Cooldown System

### How It Works

1. **Per-Game Cooldown:** Each game type (quiz, drag_drop) has independent cooldown tracking
2. **Configuration:** Admins set cooldown duration in Django admin via GameConfiguration
3. **Enforcement:** After completing a game, UserGameCooldown records the timestamp
4. **Check:** Flutter app calls `/api/game/cooldown/<game_type>/` to check if user can play

### Example: User plays both games

1. **User plays Quiz Game:**
   - Quiz cooldown starts (72 hours by default)
   - Drag & Drop still available ✅

2. **User plays Drag & Drop Game:**
   - Drag & Drop cooldown starts
   - Quiz still on cooldown ❌

3. **72 hours later:**
   - Both games available again ✅

### Unrestricted Play

To disable cooldown for a game:
1. Go to Django Admin → Game Configurations
2. Find the game type (e.g., "Quiz Game")
3. Set `is_active = False` OR `cooldown_hours = 0`
4. Save

---

## 📊 Database Verification

### Check GameSessions by Type:

```python
from game.models import GameSession

# Count sessions by game type
quiz_count = GameSession.objects.filter(game_type='quiz').count()
drag_drop_count = GameSession.objects.filter(game_type='drag_drop').count()

print(f"Quiz sessions: {quiz_count}")
print(f"Drag & Drop sessions: {drag_drop_count}")
```

### Check User Cooldowns:

```python
from game.models import UserGameCooldown
from accounts.models import Users

user = Users.objects.get(username='some_user')
cooldowns = UserGameCooldown.objects.filter(user=user)

for cd in cooldowns:
    can_play, time_remaining = cd.can_play_again()
    status = "✅ Ready" if can_play else f"⏱ {int(time_remaining)}s remaining"
    print(f"{cd.get_game_type_display()}: {status}")
```

---

## ✅ Checklist Verification

### Backend Implementation ✅

- [x] **GameSession model updated**
  - [x] Added `game_type` field with choices ['quiz', 'drag_drop']
  - [x] Added `game_name` field for display
  - [x] Default value for backward compatibility
  
- [x] **UserGameCooldown model created**
  - [x] Tracks per-game cooldowns separately
  - [x] Unique constraint on (user, game_type)
  - [x] Methods to check and update cooldown status
  
- [x] **save_game_session view updated**
  - [x] Extracts `game_type` from request payload
  - [x] Validates game_type (only 'quiz' or 'drag_drop')
  - [x] Saves game_type to GameSession
  - [x] Uses game_type for notification template selection
  - [x] Updates UserGameCooldown for the specific game
  - [x] Returns game_type in response
  
- [x] **Notification templates**
  - [x] Quiz: "...quiz game!"
  - [x] Drag & Drop: "...waste sorting game!"
  - [x] No hardcoded default to single game type
  
- [x] **Cooldown configuration**
  - [x] Fetches cooldown for specific game_type
  - [x] Falls back to 'all' only when specific not found
  - [x] Supports unrestricted play (is_active=false or cooldown=0)
  
- [x] **Admin interface**
  - [x] GameSession shows game_type and game_name
  - [x] UserGameCooldown admin with status display
  - [x] GameConfiguration admin (already existed)
  
- [x] **Database migrations**
  - [x] Created migration file
  - [x] Applied to database

### Testing ✅

- [x] **Unit tests passed**
  - [x] Quiz game session created with correct game_type
  - [x] Drag & Drop session created with correct game_type
  - [x] Separate cooldown records created
  - [x] Notification templates verified
  
- [x] **Ready for API testing**
  - [x] Endpoint available: POST /api/game/save-session/
  - [x] Test payloads prepared (see above)
  - [x] Expected responses documented

---

## 🚀 Deployment Notes

### Before Deploying:

1. **Run migrations on production:**
   ```bash
   python manage.py migrate game
   ```

2. **Set up game cooldown configurations:**
   ```bash
   python manage.py setup_game_cooldowns --active
   ```

3. **Verify admin can access GameConfiguration:**
   - Login to Django admin
   - Navigate to "Game Configurations"
   - Verify 3 entries exist (quiz, drag_drop, all)

### After Deploying:

1. **Test with Postman/curl:**
   - Submit quiz game session
   - Verify notification says "quiz game"
   - Submit drag_drop game session
   - Verify notification says "waste sorting game"

2. **Check Flutter app:**
   - Update Flutter to latest code (with game_type in payload)
   - Play quiz game → verify notification
   - Play drag & drop game → verify notification
   - Verify cooldowns are enforced separately

---

## 📝 Summary

**All requested features have been successfully implemented:**

✅ **GameSession model:** Now stores game_type and game_name  
✅ **Notification system:** Uses game_type to select correct template  
✅ **Cooldown tracking:** Separate per game_type via UserGameCooldown model  
✅ **API endpoint:** Extracts, validates, and returns game_type  
✅ **Admin interface:** Enhanced with game_type displays  
✅ **Database:** Migrations created and applied  
✅ **Testing:** Unit tests pass successfully  

**Ready for production deployment!** 🎉

---

## 🛠 Maintenance

### To modify cooldown for a specific game:

1. Django Admin → Game Configurations
2. Select game type (Quiz Game / Drag & Drop Game)
3. Adjust cooldown_hours and cooldown_minutes
4. Save
5. Changes take effect within 30 minutes (Flutter cache)

### To add a new game type:

1. Update `GAME_TYPE_CHOICES` in models.py (GameSession, UserGameCooldown, GameConfiguration)
2. Add notification template in save_game_session view
3. Create migration
4. Add GameConfiguration entry for new game type
5. Update Flutter app to send new game_type

---

**Implementation completed successfully!** ✅
