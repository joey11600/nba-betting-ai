# 🎯 QUICK REFERENCE - NBA Betting Stats API

## 🚀 SETUP (30 seconds)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
python flask_api_base44.py

# 3. Test it
# Open demo.html in browser
```

Server runs on: `http://localhost:5000`

---

## 🔥 THE KEY FEATURE

When marking a prop as LOST, set `capture_stats: true`:

```javascript
fetch(`/api/props/${propId}/result`, {
    method: 'PUT',
    body: JSON.stringify({
        result: "miss",
        actual_value: 13.0,
        capture_stats: true  // ⚡ THIS IS THE MAGIC
    })
});
```

This **automatically captures**:
- ✅ Player's shooting % that game
- ✅ Opponent team
- ✅ Opponent's defensive rating
- ✅ How much they missed by

---

## 📱 BASE44 INTEGRATION (3 steps)

### 1. Add HTML
```html
<input type="text" id="player_search" />
<div id="player_results"></div>
<input type="hidden" id="selected_player_id" />
<input type="hidden" id="selected_player_name" />
```

### 2. Add JavaScript
Copy `base44_player_search.js` to Base44 custom JS section.

### 3. Initialize
```javascript
initNBAPlayerSearch('player_search', 'player_results', function(player) {
    document.getElementById('selected_player_id').value = player.player_id;
    document.getElementById('selected_player_name').value = player.full_name;
});
```

---

## 📊 WORKFLOW

```javascript
// 1. Create bet
POST /api/bets → returns bet_id

// 2. Add props
POST /api/bets/{bet_id}/props → returns prop_id

// 3. Mark results
PUT /api/props/{prop_id}/result
{
    "result": "miss",
    "actual_value": 13.0,
    "capture_stats": true  // ⚡ Captures stats!
}

// 4. View analytics
GET /api/analytics/bust-players
GET /api/analytics/tough-matchups
```

---

## 🎯 ANALYTICS ENDPOINTS

```bash
# Players who fuck you over
GET /api/analytics/bust-players?min_props=5

# Teams with tough defenses
GET /api/analytics/tough-matchups?min_games=3

# Player vs specific team
GET /api/analytics/player-vs-opponent?player_id=1630596&opponent=LAL
```

---

## 📁 FILES

| File | Purpose |
|------|---------|
| `nba_betting_stats_api.py` | Core logic |
| `flask_api_base44.py` | REST API |
| `base44_player_search.js` | Player search |
| `demo.html` | Test interface |
| `README.md` | Full docs |
| `BASE44_INTEGRATION_GUIDE.md` | Step-by-step guide |

---

## 💡 EXAMPLE DATA CAPTURED

```python
{
    'player_name': 'Jaden Ivey',
    'game_date': '2024-12-01',
    'opponent_team': 'LAL',
    'prop_type': 'points',
    'line': 15.5,
    'actual_value': 13.0,
    'shooting_pct': 42.5,         # ⚡
    'fg_pct': 40.0,               # ⚡
    'opponent_def_rating': 108.5, # ⚡
    'missed_by': 2.5
}
```

---

## 🚨 CRITICAL

**ALWAYS** set `capture_stats: true` when marking misses!

This is what triggers the automatic stat capture:
- Shooting percentages
- Opponent team
- Defensive rating

Without this, you just get "prop missed" but no insights.

---

## 🎯 WHY THIS IS POWERFUL

After 50-100 bets, you'll know:

❌ **Bust Players**: "Avoid Jaden Ivey - 60% miss rate"
🛡️ **Tough Matchups**: "Don't bet players vs LAL - elite defense"
📊 **Patterns**: "Players shooting under 40% miss 75% of props"

---

## 📞 NEED HELP?

1. Open `demo.html` to test locally
2. Check `README.md` for full documentation
3. See `BASE44_INTEGRATION_GUIDE.md` for step-by-step

---

**Start with:** `python flask_api_base44.py`
**Test with:** Open `demo.html` in browser
**Deploy:** See README.md deployment section

🏀 Track your bets. Find the patterns. Win more.
