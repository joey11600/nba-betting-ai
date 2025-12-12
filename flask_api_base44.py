#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Flask API for NBA Stats Fetching
This is a STATELESS microservice - NO database, just fetches stats from NBA API
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
    from nba_api.stats.endpoints import (
        playergamelog,
        PlayerGameLog
    )
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    print("⚠️  Install nba_api: pip install nba_api pandas")

app = Flask(__name__)
CORS(app)

# Player cache (so we don't reload every time)
_player_cache = None
_player_cache_time = None


# =======================
# PLAYER SEARCH
# =======================

@app.route('/api/players/search', methods=['GET'])
def search_players():
    """
    Search for active NBA players
    GET /api/players/search?q=jaden&limit=10
    """
    global _player_cache, _player_cache_time
    
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'success': True, 'players': [], 'count': 0})
        
        if not NBA_API_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'NBA API not available'
            }), 500
        
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
            
            if (search_lower in full_name or 
                search_lower in last_name or 
                search_lower in first_name):
                
                matches.append({
                    "player_id": player["id"],
                    "full_name": player["full_name"],
                    "first_name": player.get("first_name", ""),
                    "last_name": player.get("last_name", ""),
                    "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/260x190/{player['id']}.png"
                })
                
                if len(matches) >= limit:
                    break
        
        return jsonify({
            'success': True,
            'players': matches,
            'count': len(matches)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """
    Get player info by ID
    GET /api/players/1630596
    """
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'NBA API not available'
            }), 500
        
        player_info = players.find_player_by_id(player_id)
        
        if not player_info:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =======================
# GAME STATS FETCHING
# =======================

@app.route('/api/stats/fetch-game', methods=['POST'])
def fetch_game_stats():
    """
    Fetch game stats for a player on a specific date
    POST /api/stats/fetch-game
    Body: {
        "player_id": 1630596,
        "player_name": "Jaden Ivey",
        "game_date": "2024-12-10",
        "stat_type": "points"
    }
    
    Returns: {
        "success": true,
        "game_found": true,
        "actual_value": 13.0,
        "all_stats": {...}  // Full game stats
    }
    """
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'NBA API not available'
            }), 500
        
        data = request.json
        player_id = data['player_id']
        game_date = data['game_date']  # Format: "2024-12-10"
        stat_type = data.get('stat_type', 'points').lower()
        period = data.get('period', None)
        
        # Get game log
        game_log = get_game_for_date(player_id, game_date)

        if not game_log:
            return jsonify({
                'success': True,
                'game_found': False,
                'error': f"No game found for player {player_id} on {game_date}"
            }), 404

        # Get game_id from the log
        game_id = str(game_log.get('Game_ID', ''))

        # If period is specified, get quarter stats
        if period and period in ['Q1', 'Q2', 'Q3', 'Q4', '1H', '2H']:
            from quarter_stats_parser import QuarterStatsParser
    
            # Determine season
            from datetime import datetime
            date_obj = datetime.strptime(game_date, '%Y-%m-%d')
            if date_obj.month >= 10:
                season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
            else:
                season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
    
            # Get quarter stats
            parser = QuarterStatsParser()
            quarter_data = parser.get_quarter_stats(player_id, season, game_id)
    
            if not quarter_data or period not in quarter_data:
                return jsonify({
                    'success': True,
                    'game_found': False,
                    'error': f"No {period} stats found for this game"
                }), 404
    
            # Get the period stats
            period_stats = quarter_data[period]
    
            # Map stat types
            stat_map = {
                'points': 'PTS',
                'rebounds': 'REB',
                'assists': 'AST',
                'steals': 'STL',
                'blocks': 'BLK',
                'threes': 'FG3M',
                'turnovers': 'TO'
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

        # Otherwise, use full game stats (existing code)
        stat_map = {
            'points': 'PTS',
            'rebounds': 'REB',
            'assists': 'AST',
            'steals': 'STL',
            'blocks': 'BLK',
            'threes': 'FG3M',
            'turnovers': 'TOV'
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
                'FG3M': game_log.get('FG3M', 0),
                'TOV': game_log.get('TOV', 0),
                'FGA': game_log.get('FGA', 0),
                'FGM': game_log.get('FGM', 0),
                'FG_PCT': game_log.get('FG_PCT', 0),
                'MATCHUP': game_log.get('MATCHUP', ''),
                'WL': game_log.get('WL', '')
            }
        })
        
        # Extract the requested stat
        stat_map = {
            'points': 'PTS',
            'rebounds': 'REB',
            'assists': 'AST',
            'steals': 'STL',
            'blocks': 'BLK',
            'threes': 'FG3M',
            'turnovers': 'TOV',
            'fga': 'FGA',
            'fta': 'FTA'
        }
        
        stat_key = stat_map.get(stat_type, 'PTS')
        actual_value = game_log.get(stat_key, 0)
        
        return jsonify({
            'success': True,
            'game_found': True,
            'actual_value': actual_value,
            'stat_type': stat_type,
            'game_date': game_date,
            'game_id': str(game_log.get('Game_ID', '')),  # FIXED: Use Game_ID (capital G, capital I)
            'all_stats': {
                'PTS': game_log.get('PTS', 0),
                'REB': game_log.get('REB', 0),
                'AST': game_log.get('AST', 0),
                'STL': game_log.get('STL', 0),
                'BLK': game_log.get('BLK', 0),
                'FG3M': game_log.get('FG3M', 0),
                'TOV': game_log.get('TOV', 0),
                'FGA': game_log.get('FGA', 0),
                'FGM': game_log.get('FGM', 0),
                'FG_PCT': game_log.get('FG_PCT', 0),
                'MATCHUP': game_log.get('MATCHUP', ''),
                'WL': game_log.get('WL', '')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/stats/batch-fetch', methods=['POST'])
def batch_fetch_stats():
    """
    Fetch stats for multiple props at once
    POST /api/stats/batch-fetch
    Body: {
        "props": [
            {
                "player_id": 1630596,
                "game_date": "2024-12-10",
                "stat_type": "points"
            },
            ...
        ]
    }
    
    Returns: Array of results with actual_value for each prop
    """
    try:
        if not NBA_API_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'NBA API not available'
            }), 500
        
        data = request.json
        props = data.get('props', [])
        
        results = []
        
        for prop in props:
            try:
                # Rate limit: 0.6 seconds between requests
                time.sleep(0.6)
                
                player_id = prop['player_id']
                game_date = prop['game_date']
                stat_type = prop.get('stat_type', 'points').lower()
                
                # Get game log
                game_log = get_game_for_date(player_id, game_date)
                
                if not game_log:
                    results.append({
                        'player_id': player_id,
                        'game_date': game_date,
                        'game_found': False,
                        'error': 'No game found'
                    })
                    continue
                
                # Extract stat
                stat_map = {
                    'points': 'PTS',
                    'rebounds': 'REB',
                    'assists': 'AST',
                    'steals': 'STL',
                    'blocks': 'BLK',
                    'threes': 'FG3M',
                    'turnovers': 'TOV'
                }
                
                stat_key = stat_map.get(stat_type, 'PTS')
                actual_value = game_log.get(stat_key, 0)
                
                results.append({
                    'player_id': player_id,
                    'game_date': game_date,
                    'game_found': True,
                    'stat_type': stat_type,
                    'actual_value': actual_value
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
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# =======================
# HELPER FUNCTIONS
# =======================

def get_game_for_date(player_id: int, game_date: str):
    """
    Get player's game log for specific date
    game_date format: "2024-12-10"
    Returns: dict of game stats or None
    """
    try:
        # Parse date and determine season
        date_obj = datetime.strptime(game_date, '%Y-%m-%d')
        
        if date_obj.month >= 10:
            season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
        else:
            season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
        
        # Get game logs with rate limiting
        time.sleep(0.6)
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )
        
        df = gamelog.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Find game on that date
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
# HEALTH CHECK
# =======================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'NBA Stats Fetching API',
        'nba_api_available': NBA_API_AVAILABLE
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'NBA Stats Fetching API',
        'status': 'running',
        'endpoints': {
            'player_search': '/api/players/search?q=jaden',
            'player_by_id': '/api/players/<player_id>',
            'fetch_game_stats': 'POST /api/stats/fetch-game',
            'batch_fetch': 'POST /api/stats/batch-fetch',
            'health': '/api/health'
        }
    })


# =======================
# RUN SERVER
# =======================

if __name__ == '__main__':
    import os
    
    print("\n" + "="*70)
    print("🏀 NBA STATS FETCHING API (Simplified)")
    print("="*70)
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n📡 Starting Flask server on port {port}")
    print("\n📚 Available endpoints:")
    print("  GET  /api/players/search?q=jaden")
    print("  GET  /api/players/<id>")
    print("  POST /api/stats/fetch-game")
    print("  POST /api/stats/batch-fetch")
    print("  GET  /api/health")
    print("\n" + "="*70 + "\n")
    
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
