#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API for Base44 Integration
Provides REST endpoints for player search, bet tracking, and analytics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from nba_betting_stats_api import NBABettingStatsAPI
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for Base44

# Initialize API
api = NBABettingStatsAPI(db_path="nba_betting_tracker.db")

# =======================
# PLAYER ENDPOINTS
# =======================

@app.route('/api/players/search', methods=['GET'])
def search_players():
    """
    Search for players with autocomplete
    GET /api/players/search?q=jaden&limit=10
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'players': []})
        
        results = api.search_players(query, limit=limit)
        
        return jsonify({
            'success': True,
            'players': results,
            'count': len(results)
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
        player = api.get_player_by_id(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404
        
        return jsonify({
            'success': True,
            'player': player
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ======================
# BET TRACKING ENDPOINTS
# ======================

@app.route('/api/bets', methods=['POST'])
def create_bet():
    """
    Create a new bet
    POST /api/bets
    Body: {
        "bet_date": "2024-12-01",
        "game_date": "2024-12-01",
        "bet_type": "parlay",
        "odds": -110,
        "stake": 1.0
    }
    """
    try:
        data = request.json
        
        bet_id = api.create_bet(
            bet_date=data['bet_date'],
            game_date=data['game_date'],
            bet_type=data.get('bet_type', 'parlay'),
            odds=data.get('odds', -110),
            stake=data.get('stake', 1.0)
        )
        
        return jsonify({
            'success': True,
            'bet_id': bet_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bets/<int:bet_id>/props', methods=['POST'])
def add_prop(bet_id):
    """
    Add a prop to a bet
    POST /api/bets/1/props
    Body: {
        "player_id": 1630596,
        "player_name": "Jaden Ivey",
        "prop_type": "points",
        "line": 15.5,
        "over_under": "over"
    }
    """
    try:
        data = request.json
        
        prop_id = api.add_prop_to_bet(
            bet_id=bet_id,
            player_id=data['player_id'],
            player_name=data['player_name'],
            prop_type=data['prop_type'],
            line=data['line'],
            over_under=data.get('over_under', 'over')
        )
        
        return jsonify({
            'success': True,
            'prop_id': prop_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bets/<int:bet_id>/result', methods=['PUT'])
def mark_bet_result(bet_id):
    """
    Mark bet result
    PUT /api/bets/1/result
    Body: {"result": "won"}  // won, lost, push
    """
    try:
        data = request.json
        api.mark_bet_result(bet_id, data['result'])
        
        return jsonify({
            'success': True,
            'message': f'Bet {bet_id} marked as {data["result"]}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/props/<int:prop_id>/result', methods=['PUT'])
def mark_prop_result(prop_id):
    """
    Mark prop result (hit/miss)
    PUT /api/props/1/result
    Body: {
        "result": "miss",
        "actual_value": 13.0,
        "capture_stats": true
    }
    """
    try:
        data = request.json
        
        api.mark_prop_result(
            prop_id=prop_id,
            result=data['result'],
            actual_value=data['actual_value'],
            capture_stats=data.get('capture_stats', True)
        )
        
        return jsonify({
            'success': True,
            'message': f'Prop {prop_id} marked as {data["result"]}',
            'stats_captured': data.get('capture_stats', True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bets/recent', methods=['GET'])
def get_recent_bets():
    """
    Get recent bets
    GET /api/bets/recent?limit=20
    """
    try:
        limit = int(request.args.get('limit', 50))
        bets = api.get_recent_bets(limit=limit)
        
        return jsonify({
            'success': True,
            'bets': bets,
            'count': len(bets)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ======================
# ANALYTICS ENDPOINTS
# ======================

@app.route('/api/analytics/bust-players', methods=['GET'])
def get_bust_players():
    """
    Get players who frequently cause losses
    GET /api/analytics/bust-players?min_props=5
    """
    try:
        min_props = int(request.args.get('min_props', 5))
        players = api.get_bust_players(min_props=min_props)
        
        return jsonify({
            'success': True,
            'players': players,
            'count': len(players)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/tough-matchups', methods=['GET'])
def get_tough_matchups():
    """
    Get opponent teams that cause frequent misses
    GET /api/analytics/tough-matchups?min_games=3
    """
    try:
        min_games = int(request.args.get('min_games', 3))
        teams = api.get_tough_matchups(min_games=min_games)
        
        return jsonify({
            'success': True,
            'teams': teams,
            'count': len(teams)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/player-vs-opponent', methods=['GET'])
def get_player_vs_opponent():
    """
    Get player stats vs specific opponent
    GET /api/analytics/player-vs-opponent?player_id=1630596&opponent=LAL
    """
    try:
        player_id = int(request.args.get('player_id'))
        opponent = request.args.get('opponent')
        
        stats = api.get_player_vs_opponent_stats(player_id, opponent)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ======================
# PLAYER RESEARCH ENDPOINTS
# ======================

@app.route("/api/research/player")
def research_player():
    try:
        player_id = int(request.args.get("player_id"))
        stat = request.args.get("stat", "pts")
        window = request.args.get("window", "L10")
        opponent = request.args.get("opponent", None)
        season_filter = request.args.get("season_filter", "all")
        quarter = request.args.get("quarter", None)  # Q1, Q2, Q3, Q4, or None
        
        # Accept BOTH parameter names for compatibility
        game_result = request.args.get("game_result") or request.args.get("result_filter", "any")

        data = api.get_player_research(
            player_id=player_id,
            stat=stat,
            window=window,
            opponent=opponent,
            season_filter=season_filter,
            game_result=game_result,
            quarter=quarter,
        )

        return jsonify({"success": True, **data})

    except Exception as e:
        print("Error in /api/research/player:", e)
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ======================
# HEALTH CHECK
# ======================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'NBA Betting Stats API'
    })

# ======================
# AUTO-FETCH PROP RESULT ENDPOINT
# ======================

@app.route('/api/props/<int:prop_id>/auto-result', methods=['PUT'])
def auto_fetch_prop_result(prop_id):
    """
    Automatically fetch game stats and determine hit/miss
    PUT /api/props/1/auto-result
    Body: {
        "player_id": 1630596,
        "player_name": "Jaden Ivey",
        "game_date": "2024-12-10",
        "prop_type": "points",
        "line": 15.5,
        "over_under": "over"
    }
    """
    try:
        data = request.json
        
        # Get game stats from NBA API
        game_log = api._get_game_for_date(
            player_id=data['player_id'],
            game_date=data['game_date']
        )
        
        if not game_log:
            return jsonify({
                'success': False,
                'error': f"No game found for {data['player_name']} on {data['game_date']}"
            }), 404
        
        # Extract actual stat value based on prop type
        stat_map = {
            'points': 'PTS',
            'rebounds': 'REB',
            'assists': 'AST',
            'steals': 'STL',
            'blocks': 'BLK',
            'threes': 'FG3M',
            'turnovers': 'TOV',
            'pra': lambda log: log.get('PTS', 0) + log.get('REB', 0) + log.get('AST', 0),
            'pr': lambda log: log.get('PTS', 0) + log.get('REB', 0),
            'pa': lambda log: log.get('PTS', 0) + log.get('AST', 0),
            'ra': lambda log: log.get('REB', 0) + log.get('AST', 0)
        }
        
        prop_type_lower = data['prop_type'].lower()
        
        if callable(stat_map.get(prop_type_lower)):
            actual_value = stat_map[prop_type_lower](game_log)
        else:
            stat_key = stat_map.get(prop_type_lower, 'PTS')
            actual_value = game_log.get(stat_key, 0)
        
        # Determine hit or miss
        line = data['line']
        over_under = data.get('over_under', 'over').lower()
        
        if over_under == 'over':
            result = 'hit' if actual_value > line else 'miss'
        else:  # under
            result = 'hit' if actual_value < line else 'miss'
        
        # Update the prop with result
        api.mark_prop_result(
            prop_id=prop_id,
            result=result,
            actual_value=actual_value,
            capture_stats=(result == 'miss')  # Only capture detailed stats on misses
        )
        
        return jsonify({
            'success': True,
            'prop_id': prop_id,
            'result': result,
            'actual_value': actual_value,
            'line': line,
            'over_under': over_under,
            'message': f"{data['player_name']} {result.upper()}: {actual_value} (needed {over_under} {line})"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ======================
# BATCH BACKFILL ENDPOINT
# ======================

@app.route('/api/props/backfill-results', methods=['POST'])
def backfill_prop_results():
    """
    Backfill results for multiple props at once
    POST /api/props/backfill-results
    Body: {
        "props": [
            {
                "prop_id": 1,
                "player_id": 1630596,
                "player_name": "Jaden Ivey",
                "game_date": "2024-12-10",
                "prop_type": "points",
                "line": 15.5,
                "over_under": "over"
            },
            ...
        ]
    }
    """
    try:
        data = request.json
        props = data.get('props', [])
        
        results = {
            'total': len(props),
            'processed': 0,
            'hits': 0,
            'misses': 0,
            'errors': []
        }
        
        for prop in props:
            try:
                # Add delay to avoid rate limiting NBA API
                time.sleep(0.6)
                
                # Get game stats
                game_log = api._get_game_for_date(
                    player_id=prop['player_id'],
                    game_date=prop['game_date']
                )
                
                if not game_log:
                    results['errors'].append({
                        'prop_id': prop['prop_id'],
                        'error': f"No game found for {prop['player_name']} on {prop['game_date']}"
                    })
                    continue
                
                # Extract actual stat value
                stat_map = {
                    'points': 'PTS',
                    'rebounds': 'REB',
                    'assists': 'AST',
                    'steals': 'STL',
                    'blocks': 'BLK',
                    'threes': 'FG3M',
                    'turnovers': 'TOV'
                }
                
                prop_type_lower = prop['prop_type'].lower()
                stat_key = stat_map.get(prop_type_lower, 'PTS')
                actual_value = game_log.get(stat_key, 0)
                
                # Determine hit or miss
                line = prop['line']
                over_under = prop.get('over_under', 'over').lower()
                
                if over_under == 'over':
                    result = 'hit' if actual_value > line else 'miss'
                else:
                    result = 'hit' if actual_value < line else 'miss'
                
                # Update prop
                api.mark_prop_result(
                    prop_id=prop['prop_id'],
                    result=result,
                    actual_value=actual_value,
                    capture_stats=(result == 'miss')
                )
                
                results['processed'] += 1
                if result == 'hit':
                    results['hits'] += 1
                else:
                    results['misses'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'prop_id': prop['prop_id'],
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ======================
# RUN SERVER
# ======================

if __name__ == '__main__':
    import os
    
    print("\n" + "="*70)
    print("🏀 NBA BETTING STATS API SERVER")
    print("="*70)
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n📡 Starting Flask server on port {port}")
    print("\n📚 Available endpoints:")
    print("  GET  /api/players/search?q=jaden")
    print("  GET  /api/players/<id>")
    print("  POST /api/bets")
    print("  POST /api/bets/<id>/props")
    print("  PUT  /api/bets/<id>/result")
    print("  PUT  /api/props/<id>/result")
    print("  GET  /api/bets/recent")
    print("  GET  /api/analytics/bust-players")
    print("  GET  /api/analytics/tough-matchups")
    print("  GET  /api/analytics/player-vs-opponent")
    print("\n" + "="*70 + "\n")
    
    # Use production settings for Railway
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
