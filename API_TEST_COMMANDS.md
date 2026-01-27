# Quick API Test Commands

## Get JWT Token First
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Save the `access` token from the response.

---

## Test 1: Quiz Game Session

```bash
curl -X POST http://localhost:8000/api/game/save-session/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
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

**Expected:** Notification says "quiz game"

---

## Test 2: Drag & Drop Game Session

```bash
curl -X POST http://localhost:8000/api/game/save-session/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "score": 75,
    "correct_answers": 15,
    "wrong_answers": 3,
    "accuracy": 83.33,
    "duration_seconds": 180,
    "game_type": "drag_drop",
    "game_id": "drag_drop",
    "game_name": "Waste Sorting Game"
  }'
```

**Expected:** Notification says "waste sorting game"

---

## Test 3: Check Cooldown for Quiz

```bash
curl http://localhost:8000/api/game/cooldown/quiz/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## Test 4: Check Cooldown for Drag & Drop

```bash
curl http://localhost:8000/api/game/cooldown/drag_drop/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## Test 5: Get Notifications

```bash
curl http://localhost:8000/api/notifications/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Expected:** Shows separate notifications for each game type

---

## Test 6: Invalid Game Type (should fail)

```bash
curl -X POST http://localhost:8000/api/game/save-session/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "score": 50,
    "game_type": "invalid_type"
  }'
```

**Expected:** 400 error with "Invalid game_type" message

---

## PowerShell Version (Windows)

### Quiz Game:
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

Invoke-RestMethod -Uri "http://localhost:8000/api/game/save-session/" `
  -Method Post `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
  } `
  -Body (@{
    score = 50
    correct_answers = 10
    wrong_answers = 2
    accuracy = 83.33
    duration_seconds = 120
    game_type = "quiz"
    game_id = "quiz"
    game_name = "Quiz Game"
  } | ConvertTo-Json)
```

### Drag & Drop Game:
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"

Invoke-RestMethod -Uri "http://localhost:8000/api/game/save-session/" `
  -Method Post `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
  } `
  -Body (@{
    score = 75
    correct_answers = 15
    wrong_answers = 3
    accuracy = 83.33
    duration_seconds = 180
    game_type = "drag_drop"
    game_id = "drag_drop"
    game_name = "Waste Sorting Game"
  } | ConvertTo-Json)
```

---

## Verify in Database (Django Shell)

```bash
python manage.py shell
```

```python
from game.models import GameSession, UserGameCooldown
from accounts.models import Users

# Check sessions by game type
quiz_sessions = GameSession.objects.filter(game_type='quiz')
print(f"Quiz sessions: {quiz_sessions.count()}")

drag_drop_sessions = GameSession.objects.filter(game_type='drag_drop')
print(f"Drag & Drop sessions: {drag_drop_sessions.count()}")

# Check cooldowns for a user
user = Users.objects.get(username='your_username')
cooldowns = UserGameCooldown.objects.filter(user=user)

for cd in cooldowns:
    can_play, time_remaining = cd.can_play_again()
    status = "✅ Can play" if can_play else f"❌ {int(time_remaining)}s remaining"
    print(f"{cd.get_game_type_display()}: {status}")

# Check notifications
from accounts.models import Notification
notifications = Notification.objects.filter(user=user, type='game').order_by('-created_at')[:5]
for n in notifications:
    print(f"- {n.message}")
```
