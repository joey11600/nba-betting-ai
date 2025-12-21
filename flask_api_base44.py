#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API for NBA Stats - Base44 Integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import time
from datetime import datetime
import pandas as pd

# NBA API imports
try:
    from nba_api.stats.static import players, teams
    from nba_api.stats.endpoints import playergamelog, PlayerGameLog, commonplayerinfo
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    print("⚠️  Install nba_api: pip install nba_api pandas")

app = Flask(__name__)
CORS(app)

# Caches
_player_cache = None
_player_cache_time = None
PLAYER_META_TTL_SECONDS = 24 * 60 * 60  # 24 hours
_player_meta_cache = {}


# =======================
# PLAYER METADATA
# =======================

def get_player_metadata(player_id: int):
    """Get player metadata with 24-hour cache"""
    now = time.time()
    
    # Check cache
    cached = _player_meta_cache.get(player_id)
    if cached and (now - cached["ts"] < PLAYER_META_TTL_SECONDS):
        return cached["data"]
    
    # Rate limit
    time.sleep(0.6)
    
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        common_df = info.common_player_info.get_data_frame()
        headline_df = info.player_headline_stats.get_data_frame()
        
        if common_df.empty:
            return None
        
        row = common_df.iloc[0].to_dict()
        
        # Normalize team (null for free agents)
        team_id = row.get("TEAM_ID")
        if not team_id or str(team_id).strip() in ["0", "None", ""]:
            team = None
        else:
            team = {
                "team_id": int(team_id),
                "name": row.get("TEAM_NAME"),
                "abbreviation": row.get("TEAM_ABBREVIATION"),
                "city": row.get("TEAM_CITY"),
                "code": row.get("TEAM_CODE")
            }
        
        # Headline stats (season averages)
        headline = None
        if headline_df is not None and not headline_df.empty:
            h = headline_df.iloc[0].to_dict()
            headline = {
                "timeframe": h.get("TimeFrame"),
                "pts": h.get("PTS"),
                "ast": h.get("AST"),
                "reb": h.get("REB"),
                "pie": h.get("PIE")
            }
        
        meta = {
            "player_id": int(row.get("PERSON_ID")) if row.get("PERSON_ID") else player_id,
            "first_name": row.get("FIRST_NAME"),
            "last_name": row.get("LAST_NAME"),
            "full_name": row.get("DISPLAY_FIRST_LAST"),
            "position": row.get("POSITION"),
            "jersey": row.get("JERSEY"),
            "height": row.get("HEIGHT"),
            "weight": row.get("WEIGHT"),
            "birthdate": row.get("BIRTHDATE"),
            "school": row.get("SCHOOL"),
            "country": row.get("COUNTRY"),
            "season_exp": row.get("SEASON_EXP"),
            "roster_status": row.get("ROSTERSTATUS"),
            "from_year": row.get("FROM_YEAR"),
            "to_year": row.get("TO_YEAR"),
            "draft": {
                "year": row.get("DRAFT_YEAR"),
                "round": row.get("DRAFT_ROUND"),
                "number": row.get("DRAFT_NUMBER")
            },
            "team": team,
            "headline": headline
        }
        
        # Cache it
        _player_meta_cache[player_id] = {"ts": now, "data": meta}
        return meta
        
    except Exception as e:
        print(f"Error getting player metadata: {e}")
        return None


# =======================
# PLAYER SEARCH
# =======================

@app.route('/api/players/search', methods=['GET'])
def search_players():
    """Search for active NBA players"""
    global _player_cache, _player_cache_time
    
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'success': True, 'players': [], 'count': 0})
        
        if not NBA_API_AVAILABLE:
            return jsonify({'success': False, 'error': 'NBA API not available'}), 500
        
        # Cache player list for 1 hour
        if (_player_cache is None or _player_cache_time is None or 
            time.time() - _player_cache_time > 3600):
            
            print("🔄 Loading active NBA players...")
            all_players = players.get_players()
            _player_cache = [p for p in all_players if p.get("is_active")]
            _player_cache_time = time.time()
            print(f"✅ Loaded {len(_player_cache)} active players")
        
        # Search
        search_lower = query.lower()
        matches = []
        
        for player in _player_cache:
            full_name = player.get("full_name", "").lower()
            first_name = player.get("first_name", "").lower()
            last_name = player.get("last_name", "").lower()
            
            if (search_lower in full_name or search_lower in last_name or search_lower in first_name):
                matches.append({
                    "player_id": player["id"],
                    "full_name": player["full_name"],
                    "first_name": player.get("first_name", ""),
                    "last_name": player.get("last_name", ""),
                    "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/260x190/{player['id']}.png"
                })
                
                if len(matches) >= limit:
                    break
        
        return jsonify({'success': True, 'players': matches, 'count': len(matches)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """Get player info by ID"""
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({'success': False, 'error': 'NBA API not available'}), 500
        
        player_info = players.find_player_by_id(player_id)
        
        if not player_info:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        return jsonify({
            'success': True,
            'player': {
                'player_id': player_info['id'],
                'full_name': player_info['full_name'],
                'first_name': player_info['first_name'],
                'last_name': player_info['last_name']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =======================
# GAME STATS FETCHING
# =======================

@app.route('/api/stats/fetch-game', methods=['POST'])
def fetch_game_stats():
    """Fetch game stats for fixMissingPropData"""
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({'success': False, 'error': 'NBA API not available'}), 500
        
        data = request.json
        player_id = data['player_id']
        game_date = data['game_date']
        stat_type = data.get('stat_type', 'points').lower()
        period = data.get('period', None)
        
        game_log = get_game_for_date(player_id, game_date)

        if not game_log:
            return jsonify({
                'success': True,
                'game_found': False,
                'message': f"No game found for player {player_id} on {game_date}"
            }), 200

        game_id = str(game_log.get('Game_ID', ''))

        # Quarter stats
        if period and period in ['Q1', 'Q2', 'Q3', 'Q4', '1H', '2H']:
            from quarter_stats_parser import QuarterStatsParser
    
            date_obj = datetime.strptime(game_date, '%Y-%m-%d')
            if date_obj.month >= 10:
                season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
            else:
                season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
    
            parser = QuarterStatsParser()
            quarter_data = parser.get_quarter_stats(player_id, season, game_id)
    
            if not quarter_data or period not in quarter_data:
                return jsonify({
                    'success': True,
                    'game_found': False,
                    'message': f"No {period} stats found"
                }), 200
    
            period_stats = quarter_data[period]
    
            stat_map = {
                'points': 'PTS', 'rebounds': 'REB', 'assists': 'AST',
                'steals': 'STL', 'blocks': 'BLK', 'threes': 'FG3M', 'turnovers': 'TO'
            }
    
            stat_key = stat_map.get(stat_type, 'PTS')
            actual_value = period_stats.get(stat_key, 0)
    
            return jsonify({
                'success': True,
                'game_found': True,
                'actual_value': actual_value,
                'stat_type': stat_type,
                'game_date': game_date,
                'game_id': game_id,
                'period': period,
                'all_stats': period_stats
            })

        # Full game stats
        stat_map = {
            'points': 'PTS', 'rebounds': 'REB', 'assists': 'AST',
            'steals': 'STL', 'blocks': 'BLK', 'threes': 'FG3M', 'turnovers': 'TOV'
        }
        
        stat_key = stat_map.get(stat_type, 'PTS')
        actual_value = game_log.get(stat_key, 0)
        
        return jsonify({
            'success': True,
            'game_found': True,
            'actual_value': actual_value,
            'stat_type': stat_type,
            'game_date': game_date,
            'game_id': game_id,
            'all_stats': {
                'PTS': game_log.get('PTS', 0),
                'REB': game_log.get('REB', 0),
                'AST': game_log.get('AST', 0),
                'STL': game_log.get('STL', 0),
                'BLK': game_log.get('BLK', 0),
                'TOV': game_log.get('TOV', 0),
                'FG3M': game_log.get('FG3M', 0),
                'FGM': game_log.get('FGM', 0),
                'FG_PCT': game_log.get('FG_PCT', 0),
                'MATCHUP': game_log.get('MATCHUP', ''),
                'WL': game_log.get('WL', '')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =======================
# RESEARCH PAGE ENDPOINT
# =======================

@app.route('/api/research/player', methods=['GET'])
def research_player():
    """Base44 Research page endpoint with player metadata"""
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({'success': False, 'error': 'NBA API not available'}), 500
        
        # Parse parameters
        player_id = request.args.get('player_id', type=int)
        stat = request.args.get('stat', 'pts')
        window = request.args.get('window', 'L15')
        game_result = request.args.get('game_result', 'any')
        season_filter = request.args.get('season_filter', 'all')
        quarter = request.args.get('quarter', None)
        
        if not player_id:
            return jsonify({'success': False, 'error': 'player_id required'}), 400
        
        # Get player metadata (non-fatal if fails)
        player_meta = None
        try:
            player_meta = get_player_metadata(player_id)
        except Exception as e:
            print(f"Metadata fetch failed (non-fatal): {e}")
        
        # Determine season
        now = datetime.now()
        if now.month >= 10:
            current_season = f"{now.year}-{str(now.year + 1)[-2:]}"
            last_season = f"{now.year - 1}-{str(now.year)[-2:]}"
        else:
            current_season = f"{now.year - 1}-{str(now.year)[-2:]}"
            last_season = f"{now.year - 2}-{str(now.year - 1)[-2:]}"
        
        season_to_query = last_season if window == 'last_season' else current_season
        season_type = 'Playoffs' if season_filter == 'playoffs' else 'Regular Season'
        
        # Get game logs
        time.sleep(0.6)
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season_to_query,
            season_type_all_star=season_type
        )
        
        df = gamelog.get_data_frames()[0]
        
        if df.empty:
            return jsonify({
                'success': True,
                'player': player_meta,
                'summary': {'games': 0, 'avg': 0, 'median': 0, 'min': 0, 'max': 0, 'hit_rate': 0, 'std_dev': 0},
                'chart': {'games': []},
                'message': 'No games found'
            })
        
        # Filter by game result
        if game_result == 'won':
            df = df[df['WL'] == 'W']
        elif game_result == 'lost':
            df = df[df['WL'] == 'L']
        
        # Apply window filter
        if window == 'L5':
            df = df.head(5)
        elif window == 'L10':
            df = df.head(10)
        elif window == 'L15':
            df = df.head(15)
        
        # Stat mapping
        stat_map = {
            'pts': 'PTS', 'reb': 'REB', 'ast': 'AST', 'blk': 'BLK', 'stl': 'STL', '3pm': 'FG3M',
            'pra': ['PTS', 'REB', 'AST'], 'pr': ['PTS', 'REB'], 'ra': ['REB', 'AST'], 'pa': ['PTS', 'AST']
        }
        
        stat_values = []
        chart_games = []
        
        # Quarter stats
        if quarter and quarter in ['Q1', 'Q2', 'Q3', 'Q4', '1H', '2H']:
            try:
                from quarter_stats_parser import QuarterStatsParser
                parser = QuarterStatsParser()
                all_quarter_data = parser.get_quarter_stats(player_id, season_to_query)
                
                quarter_stat_map = {'pts': 'PTS', 'reb': 'REB', 'ast': 'AST', 'blk': 'BLK', 'stl': 'STL', '3pm': 'FG3M'}
                
                for _, row in df.iterrows():
                    game_id = str(row['Game_ID'])
                    if game_id in all_quarter_data and quarter in all_quarter_data[game_id]:
                        period_stats = all_quarter_data[game_id][quarter]
                        
                        if stat in ['pra', 'pr', 'ra', 'pa']:
                            combo_keys = stat_map[stat]
                            value = sum(period_stats.get(quarter_stat_map.get(k.lower(), k), 0) 
                                      for k in ['pts', 'reb', 'ast'] if k.upper() in combo_keys)
                        else:
                            stat_key = quarter_stat_map.get(stat, 'PTS')
                            value = period_stats.get(stat_key, 0)
                        
                        stat_values.append(float(value))
                        chart_games.append({
                            'date': row['GAME_DATE'],
                            'opponent': row['MATCHUP'].split()[-1],
                            'value': float(value),
                            'result': row.get('WL', '')
                        })
            except ImportError:
                return jsonify({'success': False, 'error': 'Quarter stats not available'}), 500
        else:
            # Full game stats
            for _, row in df.iterrows():
                if stat in ['pra', 'pr', 'ra', 'pa']:
                    combo_stats = stat_map[stat]
                    value = sum(float(row.get(s, 0)) for s in combo_stats)
                else:
                    stat_key = stat_map.get(stat, 'PTS')
                    value = float(row.get(stat_key, 0))
                
                stat_values.append(value)
                chart_games.append({
                    'date': row['GAME_DATE'],
                    'opponent': row['MATCHUP'].split()[-1],
                    'value': value,
                    'result': row.get('WL', '')
                })
        
        if not stat_values:
            return jsonify({
                'success': True,
                'player': player_meta,
                'summary': {'games': 0, 'avg': 0, 'median': 0, 'min': 0, 'max': 0, 'hit_rate': 0, 'std_dev': 0},
                'chart': {'games': []},
                'message': 'No data for selected filters'
            })
        
        # Calculate stats
        avg_value = sum(stat_values) / len(stat_values)
        sorted_values = sorted(stat_values)
        median_value = sorted_values[len(sorted_values) // 2]
        min_value = min(stat_values)
        max_value = max(stat_values)
        
        variance = sum((x - avg_value) ** 2 for x in stat_values) / len(stat_values)
        std_dev = variance ** 0.5
        hit_rate = (sum(1 for v in stat_values if v > avg_value) / len(stat_values)) * 100
        
        return jsonify({
            'success': True,
            'player': player_meta,  # Player metadata with team, position, etc
            'summary': {
                'games': len(stat_values),
                'avg': round(avg_value, 1),
                'median': round(median_value, 1),
                'min': round(min_value, 1),
                'max': round(max_value, 1),
                'hit_rate': round(hit_rate, 1),
                'std_dev': round(std_dev, 1)
            },
            'chart': {'games': chart_games},
            'message': 'Player data loaded successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =======================
# BATCH FETCH
# =======================

@app.route('/api/stats/batch-fetch', methods=['POST'])
def batch_fetch_stats():
    """Fetch stats for multiple props"""
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({'success': False, 'error': 'NBA API not available'}), 500
        
        data = request.json
        props = data.get('props', [])
        results = []
        
        for prop in props:
            try:
                time.sleep(0.6)
                
                player_id = prop['player_id']
                game_date = prop['game_date']
                stat_type = prop.get('stat_type', 'points').lower()
                period = prop.get('period', None)
                
                game_log = get_game_for_date(player_id, game_date)
                
                if not game_log:
                    results.append({
                        'player_id': player_id,
                        'game_date': game_date,
                        'game_found': False,
                        'error': 'No game found'
                    })
                    continue
                
                game_id = str(game_log.get('Game_ID', ''))
                
                if period and period in ['Q1', 'Q2', 'Q3', 'Q4', '1H', '2H']:
                    from quarter_stats_parser import QuarterStatsParser
                    
                    date_obj = datetime.strptime(game_date, '%Y-%m-%d')
                    if date_obj.month >= 10:
                        season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
                    else:
                        season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
                    
                    parser = QuarterStatsParser()
                    quarter_data = parser.get_quarter_stats(player_id, season, game_id)
                    
                    if quarter_data and period in quarter_data:
                        period_stats = quarter_data[period]
                        stat_map = {
                            'points': 'PTS', 'rebounds': 'REB', 'assists': 'AST',
                            'steals': 'STL', 'blocks': 'BLK', 'threes': 'FG3M', 'turnovers': 'TO'
                        }
                        stat_key = stat_map.get(stat_type, 'PTS')
                        actual_value = period_stats.get(stat_key, 0)
                    else:
                        results.append({
                            'player_id': player_id,
                            'game_date': game_date,
                            'game_found': False,
                            'error': f'No {period} stats found'
                        })
                        continue
                else:
                    stat_map = {
                        'points': 'PTS', 'rebounds': 'REB', 'assists': 'AST',
                        'steals': 'STL', 'blocks': 'BLK', 'threes': 'FG3M', 'turnovers': 'TOV'
                    }
                    stat_key = stat_map.get(stat_type, 'PTS')
                    actual_value = game_log.get(stat_key, 0)
                
                results.append({
                    'player_id': player_id,
                    'game_date': game_date,
                    'game_found': True,
                    'stat_type': stat_type,
                    'actual_value': actual_value,
                    'period': period
                })
                
            except Exception as e:
                results.append({
                    'player_id': prop.get('player_id'),
                    'game_date': prop.get('game_date'),
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(props),
            'processed': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =======================
# HELPER FUNCTIONS
# =======================

def get_game_for_date(player_id: int, game_date: str):
    """Get player's game log for specific date"""
    try:
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        
        if date_obj.month >= 10:
            season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
        else:
            season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
        
        time.sleep(0.6)
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        
        df = gamelog.get_data_frames()[0]
        
        if df.empty:
            return None
        
        df["GAME_DATE_DT"] = pd.to_datetime(df["GAME_DATE"]).dt.date
        game_date_obj = pd.to_datetime(game_date).date()
        matching_games = df[df["GAME_DATE_DT"] == game_date_obj]
        
        if not matching_games.empty:
            return matching_games.iloc[0].to_dict()
        
        return None
        
    except Exception as e:
        print(f"Error fetching game: {e}")
        return None


# =======================
# HEALTH CHECK & ROOT
# =======================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'NBA Stats API for Base44',
        'nba_api_available': NBA_API_AVAILABLE
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'NBA Stats API for Base44',
        'status': 'running',
        'endpoints': {
            'player_search': 'GET /api/players/search?q=jaden',
            'player_by_id': 'GET /api/players/<player_id>',
            'research_player': 'GET /api/research/player?player_id=1628973&stat=pts&window=L15',
            'fetch_game_stats': 'POST /api/stats/fetch-game',
            'batch_fetch': 'POST /api/stats/batch-fetch',
            'health': 'GET /api/health'
        }
    })


# =======================
# RUN SERVER
# =======================

if __name__ == '__main__':
    import os
    
    print("\n" + "="*70)
    print("🏀 NBA STATS API - BASE44 INTEGRATION")
    print("="*70)
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n📡 Starting Flask server on port {port}")
    print("\n📚 Available endpoints:")
    print("  GET  /api/players/search?q=jaden")
    print("  GET  /api/players/<id>")
    print("  GET  /api/research/player (with metadata)")
    print("  POST /api/stats/fetch-game")
    print("  POST /api/stats/batch-fetch")
    print("  GET  /api/health")
    print("\n" + "="*70 + "\n")
    
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
