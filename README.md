# 🏀 NBA Betting Stats API for Base44

Complete NBA stats tracking system for your Base44 betting app. Automatically captures player performance, opponent data, and defensive ratings when props miss.

## 🎯 What This Does

When you mark a bet as lost, the system **automatically captures**:
- ✅ Player's shooting percentage that game (FG%, 3P%, FT%)
- ✅ Opponent team they played against
- ✅ Opponent's defensive rating
- ✅ Points allowed by opponent
- ✅ How much the prop missed by

Over time, you'll know:
- 🔴 **Which players consistently fuck you over**
- 🛡️ **Which opponent defenses cause your players to bust**
- 📊 **Patterns in prop failures** (shooting %, matchup difficulty, etc.)

---

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
python flask_api_base44.py
```

### 3. Test It

Open `demo.html` in your browser to test the complete system locally.

**API will be running at:** `http://localhost:5000`

---

## 📁 Files Overview

| File | Description |
|------|-------------|
| `nba_betting_stats_api.py` | Core API with NBA stats integration |
| `flask_api_base44.py` | REST API endpoints for Base44 |
| `base44_player_search.js` | Autocomplete player search (vanilla JS) |
| `NBAPlayerSearch.jsx` | React component for player search |
| `demo.html` | Full demo/test interface |
| `BASE44_INTEGRATION_GUIDE.md` | Complete integration guide |
| `requirements.txt` | Python dependencies |
| `start.sh` | Quick start script |

---

## 🔌 Base44 Integration

### Step 1: Copy JavaScript to Base44

Copy the contents of `base44_player_search.js` into your Base44 custom JavaScript section.

### Step 2: Add HTML Elements

```html
<!-- Player search input -->
<input type="text" id="player_search" placeholder="Search player..." />
<div id="player_results"></div>

<!-- Hidden fields to store selection -->
<input type="hidden" id="selected_player_id" />
<input type="hidden" id="selected_player_name" />
```

### Step 3: Initialize Search

```javascript
window.addEventListener('DOMContentLoaded', function() {
    initNBAPlayerSearch('player_search', 'player_results', function(player) {
        // Store selected player
        document.getElementById('selected_player_id').value = player.player_id;
        document.getElementById('selected_player_name').value = player.full_name;
    });
});
```

### Step 4: Create Bet Workflow

When user submits a bet:

```javascript
// 1. Create bet
const response = await fetch('http://localhost:5000/api/bets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        bet_date: "2024-12-01",
        game_date: "2024-12-01",
        bet_type: "parlay",
        odds: -110,
        stake: 1.0
    })
});
const data = await response.json();
const betId = data.bet_id;

// 2. Add props to bet
await fetch(`http://localhost:5000/api/bets/${betId}/props`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        player_id: 1630596,
        player_name: "Jaden Ivey",
        prop_type: "points",
        line: 15.5,
        over_under: "over"
    })
});
```

### Step 5: Mark Results (THIS IS KEY!)

When marking props as won/lost:

```javascript
// Mark prop as MISS - automatically captures stats!
await fetch(`http://localhost:5000/api/props/${propId}/result`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        result: "miss",
        actual_value: 13.0,
        capture_stats: true  // ⚡ THIS TRIGGERS STAT CAPTURE
    })
});
```

### Step 6: View Analytics

```javascript
// Get bust players
const response = await fetch('http://localhost:5000/api/analytics/bust-players?min_props=5');
const data = await response.json();

data.players.forEach(player => {
    console.log(`${player.player_name}: ${player.miss_rate}% miss rate`);
});
```

---

## 📊 API Endpoints

### Player Search

```
GET /api/players/search?q=jaden&limit=10
```

Returns list of matching players with autocomplete.

### Bet Management

```
POST /api/bets                          # Create bet
POST /api/bets/<bet_id>/props           # Add prop to bet
PUT  /api/bets/<bet_id>/result          # Mark bet won/lost
PUT  /api/props/<prop_id>/result        # Mark prop hit/miss (captures stats)
GET  /api/bets/recent?limit=50          # Get recent bets
```

### Analytics

```
GET /api/analytics/bust-players?min_props=5              # Players with high miss rates
GET /api/analytics/tough-matchups?min_games=3            # Opponents causing misses
GET /api/analytics/player-vs-opponent?player_id=X        # Player vs team stats
```

---

## 🗄️ Database Schema

The system uses SQLite (`nba_betting_tracker.db`) with 3 main tables:

### `bets`
- Bet details (date, type, odds, stake, result)

### `props`
- Individual props linked to bets
- Player, prop type, line, over/under, result

### `prop_miss_stats` ⚡ (Auto-populated on misses)
- Player shooting percentages (FG%, 3P%, FT%)
- Opponent team and team ID
- Opponent defensive rating
- Points allowed by opponent
- How much the prop missed by

---

## 💡 Example: Complete Workflow

```python
# Initialize API
from nba_betting_stats_api import NBABettingStatsAPI
api = NBABettingStatsAPI()

# 1. Search for player
players = api.search_players("Jaden")
print(players[0])  # {'player_id': 1630596, 'full_name': 'Jaden Ivey'}

# 2. Create bet
bet_id = api.create_bet(
    bet_date="2024-12-01",
    game_date="2024-12-01",
    bet_type="parlay",
    odds=-110,
    stake=1.0
)

# 3. Add props
prop_id = api.add_prop_to_bet(
    bet_id=bet_id,
    player_id=1630596,
    player_name="Jaden Ivey",
    prop_type="points",
    line=15.5,
    over_under="over"
)

# 4. Mark result (auto-captures stats on miss!)
api.mark_prop_result(
    prop_id=prop_id,
    result="miss",
    actual_value=13.0,
    capture_stats=True  # ⚡ Captures shooting %, opponent, def rating
)

# 5. View analytics
bust_players = api.get_bust_players(min_props=5)
for player in bust_players:
    print(f"{player['player_name']}: {player['miss_rate']}% miss rate")
```

---

## 🎨 What Gets Captured on Prop Miss

When you mark a prop as "miss" with `capture_stats=True`:

```python
{
    'player_id': 1630596,
    'player_name': 'Jaden Ivey',
    'game_date': '2024-12-01',
    'opponent_team': 'LAL',
    'opponent_team_id': 1610612747,
    'prop_type': 'points',
    'line': 15.5,
    'actual_value': 13.0,
    'shooting_pct': 42.5,        # ⚡ Overall shooting %
    'fg_pct': 40.0,              # ⚡ Field goal %
    'fg3_pct': 33.3,             # ⚡ 3-point %
    'ft_pct': 80.0,              # ⚡ Free throw %
    'opponent_def_rating': 108.5, # ⚡ Lakers defensive rating
    'opponent_opp_pts': 112.3,    # ⚡ Points Lakers allow per game
    'missed_by': 2.5              # How much it missed by
}
```

---

## 📈 Analytics Features

### Bust Players
Identify players who consistently cause losses:
```
Jaden Ivey: 60% miss rate (6/10 props)
LaMelo Ball: 55% miss rate (11/20 props)
```

### Tough Matchups
Find opponent defenses that shut down your players:
```
vs LAL: 70% miss rate (Def Rating: 108.5)
vs BOS: 65% miss rate (Def Rating: 106.2)
```

### Player vs Opponent
Detailed breakdown of how a player performs vs specific teams:
```
Jaden Ivey vs LAL:
- Points: 3 misses / 5 props (60% miss)
- Avg shooting: 38.2%
- Avg missed by: 3.2 points
```

---

## 🚀 Deployment to Production

### 1. Deploy Flask API

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flask_api_base44:app
```

### 2. Update Base44 API URL

In your Base44 JavaScript, change:
```javascript
const API_URL = 'https://your-domain.com/api';  // Production URL
```

### 3. Set up HTTPS

For production, use HTTPS:
- Deploy to Heroku, DigitalOcean, AWS, etc.
- Set up SSL certificate
- Update Base44 to use `https://` URLs

---

## 🔧 Troubleshooting

### "No game found for player on date"
- Check game_date format is `YYYY-MM-DD`
- Verify player actually played that day
- NBA API may be slow to update recent games

### Player search not working
- Ensure Flask server is running
- Check browser console for CORS errors
- Verify API_URL is correct

### Stats not captured
- Must set `capture_stats: true` when marking miss
- Check Flask logs for errors
- Verify game_date is valid

---

## 📝 Notes

- **Rate Limiting**: NBA API has limits (600 req/min). System includes 0.6s delays.
- **Season Detection**: Automatically determines NBA season from game date.
- **Database**: All data stored in `nba_betting_tracker.db` - back it up!
- **CORS**: Enabled by default for Base44 integration.

---

## 📚 Documentation

See `BASE44_INTEGRATION_GUIDE.md` for:
- Complete integration walkthrough
- UI component examples
- Advanced workflows
- Troubleshooting guide

---

## 🎯 Why This Is Powerful

Over time, you'll build a **data-driven betting strategy**:

1. **Identify patterns**: Which players consistently underperform?
2. **Avoid tough matchups**: Don't bet on players facing elite defenses
3. **Shooting % correlation**: See if low shooting % = prop misses
4. **Team tendencies**: Which opponents shut down certain play styles?

**Example insights you'll discover:**
- "Jaden Ivey shoots 35% vs LAL, avoid his overs"
- "Maxey's assists props fail 70% vs BOS (elite defense)"
- "Player X has 80% miss rate when shooting under 40%"

---

## 🤝 Support

Open an issue or check the integration guide for help.

**Built with:** nba_api, Flask, SQLite
**Compatible with:** Base44, any web platform

---

**Ready to track your bets like a pro? Start with `./start.sh` and open `demo.html`!** 🚀
