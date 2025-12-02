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

# ======================
# PLAYER ENDPOINTS
# ======================

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
def add_prop():
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
