# NBA Stats API - Base44 Integration Guide

Complete guide for integrating NBA player stats tracking into your Base44 betting app.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install nba_api pandas flask flask-cors
```

### 2. Start the API Server

```bash
python flask_api_base44.py
```

Server will run on `http://localhost:5000`

### 3. Test the API

```bash
# Test player search
curl "http://localhost:5000/api/players/search?q=jaden"

# Health check
curl "http://localhost:5000/api/health"
```

---

## 📱 Base44 Integration Steps

### Step 1: Add Player Search to Your Form

In your Base44 app, create a new **Input Field** for player search:

1. Add a Text Input component with ID: `player_search`
2. Add a Container component with ID: `player_results` (for autocomplete dropdown)
3. Add Hidden Fields for storing selected player:
   - `selected_player_id`
   - `selected_player_name`

### Step 2: Add the JavaScript

In your Base44 **Custom JavaScript** section:

```javascript
// Paste the contents of base44_player_search.js here

// Initialize when page loads
window.addEventListener('DOMContentLoaded', function() {
    initNBAPlayerSearch('player_search', 'player_results', function(player) {
        // Store selected player
        document.getElementById('selected_player_id').value = player.player_id;
        document.getElementById('selected_player_name').value = player.full_name;
        
        // Optional: Trigger Base44 workflow
        console.log('Selected:', player.full_name);
    });
});
```

### Step 3: Create Bet Logging Workflow

In Base44, create a workflow that:

1. **On Submit** of bet form:
   - Calls `/api/bets` (POST) to create bet
   - Gets `bet_id` in response
   - Loops through each prop and calls `/api/bets/{bet_id}/props` (POST)

2. **On Marking Results**:
   - For each prop, call `/api/props/{prop_id}/result` (PUT)
   - Set `capture_stats: true` for missed props
   - System automatically captures shooting %, opponent, defensive rating

---

## 🎯 Complete Workflow Example

### Creating a Bet with Props

```javascript
// 1. Create the bet
const betData = {
    bet_date: "2024-12-01",
    game_date: "2024-12-01",
    bet_type: "3-leg parlay",
    odds: -110,
    stake: 1.0
};

fetch('http://localhost:5000/api/bets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(betData)
})
.then(res => res.json())
.then(data => {
    const betId = data.bet_id;
    console.log('Created bet:', betId);
    
    // 2. Add props to the bet
    const props = [
        {
            player_id: 1630596,
            player_name: "Jaden Ivey",
            prop_type: "points",
            line: 15.5,
            over_under: "over"
        },
        {
            player_id: 1630162,
            player_name: "Tyrese Maxey",
            prop_type: "assists",
            line: 5.5,
            over_under: "over"
        }
    ];
    
    props.forEach(prop => {
        fetch(`http://localhost:5000/api/bets/${betId}/props`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prop)
        })
        .then(res => res.json())
        .then(data => {
            console.log('Added prop:', data.prop_id);
        });
    });
});
```

### Marking Prop Results

```javascript
// Mark a prop as MISS (auto-captures stats)
const propId = 1;
const propResult = {
    result: "miss",
    actual_value: 13.0,
    capture_stats: true  // THIS IS KEY!
};

fetch(`http://localhost:5000/api/props/${propId}/result`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(propResult)
})
.then(res => res.json())
.then(data => {
    console.log('Stats captured:', data);
    // System captured:
    // - Shooting percentage for that game
    // - Opponent team
    // - Opponent defensive rating
});
```

### Getting Analytics

```javascript
// Get bust players (who fuck up a lot)
fetch('http://localhost:5000/api/analytics/bust-players?min_props=5')
    .then(res => res.json())
    .then(data => {
        data.players.forEach(player => {
            console.log(`${player.player_name}: ${player.miss_rate}% miss rate`);
        });
    });

// Get tough matchups (teams causing misses)
fetch('http://localhost:5000/api/analytics/tough-matchups?min_games=3')
    .then(res => res.json())
    .then(data => {
        data.teams.forEach(team => {
            console.log(`vs ${team.opponent_team}: ${team.miss_rate}% miss rate`);
        });
    });
```

---

## 🗄️ Database Schema

The system uses SQLite to track everything:

### `bets` table
- bet_id
- bet_date
- game_date
- bet_type (parlay, single, etc.)
- odds
- stake
- potential_win
- result (won/lost/push)

### `props` table
- prop_id
- bet_id (FK)
- player_id
- player_name
- prop_type (points, rebounds, assists, etc.)
- line
- over_under
- result (hit/miss)
- actual_value

### `prop_miss_stats` table (auto-populated on misses)
- prop_id (FK)
- player_id
- player_name
- game_date
- opponent_team
- opponent_team_id
- prop_type
- line
- actual_value
- **shooting_pct** ⚡
- **fg_pct** ⚡
- **fg3_pct** ⚡
- **ft_pct** ⚡
- **opponent_def_rating** ⚡
- **opponent_opp_pts** ⚡
- missed_by

---

## 📊 API Endpoints Reference

### Player Search
```
GET /api/players/search?q=jaden&limit=10
GET /api/players/<player_id>
```

### Bet Management
```
POST /api/bets
POST /api/bets/<bet_id>/props
PUT  /api/bets/<bet_id>/result
PUT  /api/props/<prop_id>/result
GET  /api/bets/recent?limit=50
```

### Analytics
```
GET /api/analytics/bust-players?min_props=5
GET /api/analytics/tough-matchups?min_games=3
GET /api/analytics/player-vs-opponent?player_id=<id>&opponent=<team>
```

---

## 🎨 Base44 UI Components

### Player Search Input

```html
<div class="player-search-container">
    <label>Search Player</label>
    <input 
        type="text" 
        id="player_search"
        placeholder="Start typing player name..."
    />
    <div id="player_results"></div>
    
    <!-- Hidden fields -->
    <input type="hidden" id="selected_player_id" />
    <input type="hidden" id="selected_player_name" />
</div>
```

### Prop Entry Form

```html
<form id="prop_form">
    <div class="form-group">
        <label>Player</label>
        <input type="text" id="player_search" />
        <div id="player_results"></div>
    </div>
    
    <div class="form-group">
        <label>Prop Type</label>
        <select id="prop_type">
            <option value="points">Points</option>
            <option value="rebounds">Rebounds</option>
            <option value="assists">Assists</option>
            <option value="steals">Steals</option>
            <option value="blocks">Blocks</option>
            <option value="threes">3-Pointers Made</option>
        </select>
    </div>
    
    <div class="form-group">
        <label>Line</label>
        <input type="number" id="prop_line" step="0.5" />
    </div>
    
    <div class="form-group">
        <label>Over/Under</label>
        <select id="over_under">
            <option value="over">Over</option>
            <option value="under">Under</option>
        </select>
    </div>
    
    <button type="submit">Add Prop to Bet</button>
</form>
```

### Results Marking Interface

```html
<div class="prop-result-form">
    <h3>Mark Prop Results</h3>
    
    <div class="prop-item">
        <span class="player-name">Jaden Ivey O15.5 points</span>
        
        <div class="result-inputs">
            <input 
                type="number" 
                placeholder="Actual value"
                class="actual-value"
                step="0.5"
            />
            
            <button class="btn-hit" onclick="markProp(propId, 'hit', actualValue)">
                ✓ Hit
            </button>
            
            <button class="btn-miss" onclick="markProp(propId, 'miss', actualValue, true)">
                ✗ Miss (Capture Stats)
            </button>
        </div>
    </div>
</div>

<script>
function markProp(propId, result, actualValue, captureStats = false) {
    fetch(`http://localhost:5000/api/props/${propId}/result`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            result: result,
            actual_value: actualValue,
            capture_stats: captureStats
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(`Prop marked as ${result}!`);
            if (captureStats) {
                alert('Stats captured: shooting %, opponent, def rating');
            }
        }
    });
}
</script>
```

### Analytics Dashboard

```html
<div class="analytics-dashboard">
    <h2>Betting Analytics</h2>
    
    <!-- Bust Players -->
    <div class="analytics-section">
        <h3>🔴 Bust Players (Players Who Cost You)</h3>
        <div id="bust_players_list"></div>
    </div>
    
    <!-- Tough Matchups -->
    <div class="analytics-section">
        <h3>🛡️ Tough Matchups (Teams Causing Misses)</h3>
        <div id="tough_matchups_list"></div>
    </div>
</div>

<script>
// Load bust players
fetch('http://localhost:5000/api/analytics/bust-players?min_props=5')
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('bust_players_list');
        data.players.forEach(player => {
            container.innerHTML += `
                <div class="player-stat">
                    <strong>${player.player_name}</strong>: 
                    ${player.miss_rate}% miss rate 
                    (${player.misses}/${player.total_props} props)
                </div>
            `;
        });
    });

// Load tough matchups
fetch('http://localhost:5000/api/analytics/tough-matchups?min_games=3')
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('tough_matchups_list');
        data.teams.forEach(team => {
            container.innerHTML += `
                <div class="matchup-stat">
                    <strong>vs ${team.opponent_team}</strong>: 
                    ${team.miss_rate}% miss rate 
                    (Def Rating: ${team.avg_def_rating?.toFixed(1) || 'N/A'})
                </div>
            `;
        });
    });
</script>
```

---

## 🔥 Pro Tips

1. **Always set `capture_stats: true`** when marking props as "miss" - this is what captures the shooting %, opponent, and defensive rating

2. **Use the analytics endpoints** to identify patterns:
   - Which players consistently underperform?
   - Which opponent defenses shut down your players?

3. **Rate limiting**: NBA API has rate limits (600 requests/min). The system includes 0.6s delays between calls.

4. **Season detection**: System automatically determines which NBA season a game belongs to based on date

5. **Database backup**: Your `nba_betting_tracker.db` file contains all your data - back it up regularly!

---

## 🚨 Troubleshooting

### "No game found for player on date"
- Check that the game_date format is correct: `YYYY-MM-DD`
- Ensure the player actually played that day
- NBA API might be slow to update recent games

### Player search not working
- Check that Flask server is running on port 5000
- Verify CORS is enabled (should be by default)
- Check browser console for errors

### Stats not being captured
- Verify `capture_stats: true` is set when marking miss
- Check that game_date is valid and game exists
- Look at Flask console for error messages

---

## 📦 Deployment

### Deploy Flask API to Production

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flask_api_base44:app
```

### Update Base44 JavaScript API URL

Change the `apiBaseUrl` in your JavaScript:

```javascript
const search = new NBAPlayerSearch({
    apiBaseUrl: 'https://your-api-domain.com/api',  // Production URL
    // ... rest of config
});
```

---

## 🎯 What Gets Captured When a Prop Misses

When you mark a prop as "miss" with `capture_stats: true`:

✓ **Player's shooting percentage** (FG%, 3P%, FT% - weighted average)
✓ **Opponent team** (e.g., "LAL", "BOS")
✓ **Opponent's defensive rating** (season average)
✓ **Opponent's points allowed** (season average)
✓ **How much the prop missed by** (line - actual value)

This data powers your analytics to identify:
- Players who underperform consistently
- Tough defensive matchups
- Patterns in prop failures

---

## 📞 Need Help?

Check the example files:
- `nba_betting_stats_api.py` - Core API logic
- `flask_api_base44.py` - REST endpoints
- `base44_player_search.js` - Frontend search component

Run the example:
```bash
python nba_betting_stats_api.py
```

This will demonstrate the full workflow with example data.
