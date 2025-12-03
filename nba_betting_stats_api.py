#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBA Betting Stats API Integration for Base44
Tracks props, captures stats on misses, identifies bust players & tough matchups
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time
import pandas as pd

try:
    from nba_api.stats.static import players, teams
    from nba_api.stats.endpoints import (
        playergamelog,
        leaguedashteamstats,
        boxscoretraditionalv2,
        leaguegamefinder
    )
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    print("⚠️  Install nba_api: pip install nba_api")


class NBABettingStatsAPI:
    """
    NBA Stats API for betting app integration
    Handles player search, bet tracking, stat capture, and analytics
    """
    
    def __init__(self, db_path: str = "nba_betting_tracker.db"):
        """Initialize with database for tracking bets and stats"""
        self.db_path = db_path
        self.init_database()
        self._player_cache = None
        self._player_cache_time = None
        
    def init_database(self):
        """Create database tables for tracking bets and stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bet_date TEXT NOT NULL,
                game_date TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                odds REAL,
                stake REAL,
                potential_win REAL,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Props table (each bet can have multiple props)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS props (
                prop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bet_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                prop_type TEXT NOT NULL,
                line REAL NOT NULL,
                over_under TEXT NOT NULL,
                result TEXT,
                actual_value REAL,
                FOREIGN KEY (bet_id) REFERENCES bets(bet_id)
            )
        """)
        
        # Prop miss stats (captured when a prop fails)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prop_miss_stats (
                miss_id INTEGER PRIMARY KEY AUTOINCREMENT,
                prop_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                game_date TEXT NOT NULL,
                opponent_team TEXT NOT NULL,
                opponent_team_id INTEGER,
                prop_type TEXT NOT NULL,
                line REAL NOT NULL,
                actual_value REAL NOT NULL,
                shooting_pct REAL,
                fg_pct REAL,
                fg3_pct REAL,
                ft_pct REAL,
                opponent_def_rating REAL,
                opponent_opp_pts REAL,
                missed_by REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prop_id) REFERENCES props(prop_id)
            )
        """)
        
        # Analytics cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✓ Database initialized")
    
    # ======================
    # PLAYER SEARCH
    # ======================
    
    def search_players(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search for NBA players using static list"""
        if not NBA_API_AVAILABLE:
            return []

        # Cache player list for 1 hour
        if (
            self._player_cache is None
            or self._player_cache_time is None
            or time.time() - self._player_cache_time > 3600
        ):
            print("🔄 Loading ACTIVE NBA players...")

            try:
                # Get everyone, then keep only active players (rookies included)
                all_players = players.get_players()

                self._player_cache = [
                    p for p in all_players
                    if p.get("is_active")  # True only for current NBA players
                ]

                self._player_cache_time = time.time()
                print(f"✅ Loaded {len(self._player_cache)} active players")

            except Exception as e:
                print(f"❌ Error loading players: {e}")
                self._player_cache = []
                self._player_cache_time = time.time()

            except Exception as e:
                print(f"❌ Error loading players: {e}")
                self._player_cache = []
                self._player_cache_time = time.time()

        # Search the cache
        search_lower = search_term.lower().strip()

        if not search_lower:
            return []

        if not self._player_cache:
            print("⚠️ Player cache is empty!")
            return []

        matches = []
        for player in self._player_cache:
            full_name = player.get("full_name", "").lower()
            first_name = player.get("first_name", "").lower()
            last_name = player.get("last_name", "").lower()

            if (
                search_lower in full_name
                or search_lower in last_name
                or search_lower in first_name
            ):
                matches.append(
                    {
                        "player_id": player["id"],
                        "full_name": player["full_name"],
                        "first_name": player.get("first_name", ""),
                        "last_name": player.get("last_name", ""),
                        "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/260x190/{player['id']}.png",
                    }
                )

                if len(matches) >= limit:
                    break

        print(f"🔍 Search '{search_term}' found {len(matches)} matches")
        return matches
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict]:
        """Get player info by ID"""
        if not NBA_API_AVAILABLE:
            return None
            
        try:
            player_info = players.find_player_by_id(player_id)
            if player_info:
                return {
                    'player_id': player_info['id'],
                    'full_name': player_info['full_name'],
                    'first_name': player_info['first_name'],
                    'last_name': player_info['last_name']
                }
        except:
            pass
        return None
    
    # ======================
    # BET TRACKING
    # ======================
    
    def create_bet(self, bet_date: str, game_date: str, bet_type: str = "parlay",
                   odds: float = -110, stake: float = 1.0) -> int:
        """
        Create a new bet entry
        Returns bet_id
        """
        potential_win = self._calculate_payout(odds, stake)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bets (bet_date, game_date, bet_type, odds, stake, potential_win)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bet_date, game_date, bet_type, odds, stake, potential_win))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return bet_id
    
    def add_prop_to_bet(self, bet_id: int, player_id: int, player_name: str,
                       prop_type: str, line: float, over_under: str = "over") -> int:
        """
        Add a prop to a bet
        prop_type: 'points', 'rebounds', 'assists', 'steals', 'blocks', 'threes', etc.
        Returns prop_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO props (bet_id, player_id, player_name, prop_type, line, over_under)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bet_id, player_id, player_name, prop_type, line, over_under))
        
        prop_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prop_id
    
    def mark_bet_result(self, bet_id: int, result: str):
        """Mark bet as 'won', 'lost', or 'push'"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bets SET result = ? WHERE bet_id = ?
        """, (result, bet_id))
        
        conn.commit()
        conn.close()
    
    def mark_prop_result(self, prop_id: int, result: str, actual_value: float,
                        capture_stats: bool = True):
        """
        Mark individual prop as 'hit' or 'miss'
        If miss and capture_stats=True, automatically capture game stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update prop result
        cursor.execute("""
            UPDATE props SET result = ?, actual_value = ?
            WHERE prop_id = ?
        """, (result, actual_value, prop_id))
        
        # If it's a miss, capture stats
        if result == 'miss' and capture_stats:
            cursor.execute("""
                SELECT p.player_id, p.player_name, p.prop_type, p.line, 
                       p.actual_value, b.game_date
                FROM props p
                JOIN bets b ON p.bet_id = b.bet_id
                WHERE p.prop_id = ?
            """, (prop_id,))
            
            row = cursor.fetchone()
            if row:
                player_id, player_name, prop_type, line, actual_value, game_date = row
                
                # Capture stats in background (don't block)
                try:
                    self._capture_miss_stats(
                        prop_id, player_id, player_name, game_date,
                        prop_type, line, actual_value
                    )
                except Exception as e:
                    print(f"⚠️  Error capturing stats: {e}")
        
        conn.commit()
        conn.close()
    
    def _capture_miss_stats(self, prop_id: int, player_id: int, player_name: str,
                           game_date: str, prop_type: str, line: float, 
                           actual_value: float):
        """
        Capture detailed stats for a missed prop
        - Shooting percentages
        - Opponent team
        - Opponent defensive rating
        """
        if not NBA_API_AVAILABLE:
            return
        
        try:
            # Get the specific game log for that date
            game_log = self._get_game_for_date(player_id, game_date)
            
            if not game_log:
                print(f"⚠️  No game found for {player_name} on {game_date}")
                return
            
            # Extract opponent
            matchup = game_log.get('MATCHUP', '')
            if ' @ ' in matchup:
                opponent_abbrev = matchup.split(' @ ')[1]
            elif ' vs. ' in matchup:
                opponent_abbrev = matchup.split(' vs. ')[1]
            else:
                opponent_abbrev = 'UNKNOWN'
            
            # Get opponent team ID
            opponent_team_id = self._get_team_id_by_abbrev(opponent_abbrev)
            
            # Get shooting percentages
            fg_pct = game_log.get('FG_PCT', 0) * 100 if game_log.get('FG_PCT') else None
            fg3_pct = game_log.get('FG3_PCT', 0) * 100 if game_log.get('FG3_PCT') else None
            ft_pct = game_log.get('FT_PCT', 0) * 100 if game_log.get('FT_PCT') else None
            
            # Calculate overall shooting % (weighted)
            fga = game_log.get('FGA', 0)
            fg3a = game_log.get('FG3A', 0)
            fta = game_log.get('FTA', 0)
            total_attempts = fga + fg3a + fta
            
            if total_attempts > 0:
                shooting_pct = (
                    (fg_pct or 0) * fga + 
                    (fg3_pct or 0) * fg3a + 
                    (ft_pct or 0) * fta
                ) / total_attempts
            else:
                shooting_pct = None
            
            # Get opponent defensive rating
            opponent_def_rating = None
            opponent_opp_pts = None
            
            if opponent_team_id:
                def_stats = self._get_team_defensive_stats(opponent_team_id, game_date)
                if def_stats:
                    opponent_def_rating = def_stats.get('def_rating')
                    opponent_opp_pts = def_stats.get('opp_pts')
            
            missed_by = line - actual_value
            
            # Insert into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO prop_miss_stats (
                    prop_id, player_id, player_name, game_date,
                    opponent_team, opponent_team_id, prop_type, line,
                    actual_value, shooting_pct, fg_pct, fg3_pct, ft_pct,
                    opponent_def_rating, opponent_opp_pts, missed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prop_id, player_id, player_name, game_date,
                opponent_abbrev, opponent_team_id, prop_type, line,
                actual_value, shooting_pct, fg_pct, fg3_pct, ft_pct,
                opponent_def_rating, opponent_opp_pts, missed_by
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Captured miss stats for {player_name} vs {opponent_abbrev}")
            
        except Exception as e:
            print(f"❌ Error capturing miss stats: {e}")
    
    def _get_game_for_date(self, player_id: int, game_date: str) -> Optional[Dict]:
        """Get player's game log for specific date"""
        try:
            # Format: '2024-12-01' -> season 2024-25
            date_obj = datetime.strptime(game_date, '%Y-%m-%d')
            
            # Determine season
            if date_obj.month >= 10:
                season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
            else:
                season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
            
            # Get game logs
            time.sleep(0.6)  # Rate limit
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season
            )
            
            df = gamelog.get_data_frames()[0]
            
            # Find game on that date
            df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
            game_date_obj = pd.to_datetime(game_date)
            
            matching_games = df[df['GAME_DATE'] == game_date_obj]
            
            if not matching_games.empty:
                return matching_games.iloc[0].to_dict()
            
        except Exception as e:
            print(f"Error fetching game: {e}")
        
        return None
    
    def _get_team_id_by_abbrev(self, abbrev: str) -> Optional[int]:
        """Get team ID from abbreviation"""
        try:
            all_teams = teams.get_teams()
            for team in all_teams:
                if team['abbreviation'] == abbrev:
                    return team['id']
        except:
            pass
        return None
    
    def _get_team_defensive_stats(self, team_id: int, game_date: str) -> Optional[Dict]:
        """
        Get team's defensive stats (defensive rating, opp pts per game)
        Uses season stats up to that date
        """
        try:
            # Determine season
            date_obj = datetime.strptime(game_date, '%Y-%m-%d')
            if date_obj.month >= 10:
                season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
            else:
                season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
            
            time.sleep(0.6)  # Rate limit
            team_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                per_mode_detailed='PerGame',
                measure_type_detailed_defense='Defense'
            )
            
            df = team_stats.get_data_frames()[0]
            team_data = df[df['TEAM_ID'] == team_id]
            
            if not team_data.empty:
                return {
                    'def_rating': team_data.iloc[0].get('DEF_RATING'),
                    'opp_pts': team_data.iloc[0].get('OPP_PTS_PER_GAME')
                }
            
        except Exception as e:
            print(f"Error fetching defensive stats: {e}")
        
        return None
    
    def _calculate_payout(self, odds: float, stake: float) -> float:
        """Calculate potential payout from American odds"""
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))
    
    # ======================
    # ANALYTICS
    # ======================
    
    def get_bust_players(self, min_props: int = 5) -> List[Dict]:
        """
        Get players who frequently cause bet losses
        Returns list sorted by miss rate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                player_id,
                player_name,
                COUNT(*) as total_props,
                SUM(CASE WHEN result = 'miss' THEN 1 ELSE 0 END) as misses,
                ROUND(100.0 * SUM(CASE WHEN result = 'miss' THEN 1 ELSE 0 END) / COUNT(*), 1) as miss_rate,
                AVG(CASE WHEN result = 'miss' THEN actual_value ELSE NULL END) as avg_value_when_miss
            FROM props
            WHERE result IS NOT NULL
            GROUP BY player_id, player_name
            HAVING COUNT(*) >= ?
            ORDER BY miss_rate DESC, total_props DESC
        """, (min_props,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'player_id': row[0],
                'player_name': row[1],
                'total_props': row[2],
                'misses': row[3],
                'miss_rate': row[4],
                'avg_value_when_miss': row[5]
            })
        
        conn.close()
        return results
    
    def get_tough_matchups(self, min_games: int = 3) -> List[Dict]:
        """
        Get opponent teams that frequently cause props to miss
        Returns list sorted by miss rate against them
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                opponent_team,
                COUNT(*) as total_props,
                SUM(CASE WHEN pms.prop_id IS NOT NULL THEN 1 ELSE 0 END) as misses,
                ROUND(100.0 * SUM(CASE WHEN pms.prop_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as miss_rate,
                AVG(opponent_def_rating) as avg_def_rating,
                AVG(opponent_opp_pts) as avg_opp_pts
            FROM props p
            LEFT JOIN prop_miss_stats pms ON p.prop_id = pms.prop_id
            WHERE opponent_team IS NOT NULL
            GROUP BY opponent_team
            HAVING COUNT(*) >= ?
            ORDER BY miss_rate DESC
        """, (min_games,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'opponent_team': row[0],
                'total_props': row[1],
                'misses': row[2],
                'miss_rate': row[3],
                'avg_def_rating': row[4],
                'avg_opp_pts': row[5]
            })
        
        conn.close()
        return results
    
    def get_player_vs_opponent_stats(self, player_id: int, 
                                    opponent_team: str = None) -> Dict:
        """
        Get detailed stats for a player vs specific opponent or all opponents
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if opponent_team:
            cursor.execute("""
                SELECT 
                    prop_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'miss' THEN 1 ELSE 0 END) as misses,
                    AVG(missed_by) as avg_missed_by,
                    AVG(shooting_pct) as avg_shooting_pct,
                    AVG(opponent_def_rating) as avg_def_rating
                FROM props p
                JOIN prop_miss_stats pms ON p.prop_id = pms.prop_id
                WHERE p.player_id = ? AND pms.opponent_team = ?
                GROUP BY prop_type
            """, (player_id, opponent_team))
        else:
            cursor.execute("""
                SELECT 
                    pms.opponent_team,
                    COUNT(*) as total,
                    SUM(CASE WHEN p.result = 'miss' THEN 1 ELSE 0 END) as misses,
                    AVG(pms.missed_by) as avg_missed_by,
                    AVG(pms.shooting_pct) as avg_shooting_pct,
                    AVG(pms.opponent_def_rating) as avg_def_rating
                FROM props p
                JOIN prop_miss_stats pms ON p.prop_id = pms.prop_id
                WHERE p.player_id = ?
                GROUP BY pms.opponent_team
                ORDER BY misses DESC
            """, (player_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'category': row[0],
                'total': row[1],
                'misses': row[2],
                'avg_missed_by': row[3],
                'avg_shooting_pct': row[4],
                'avg_def_rating': row[5]
            })
        
        conn.close()
        return {'stats': results}
    
    def get_recent_bets(self, limit: int = 50) -> List[Dict]:
        """Get recent bets with all props"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                b.bet_id, b.bet_date, b.game_date, b.bet_type,
                b.odds, b.stake, b.potential_win, b.result,
                COUNT(p.prop_id) as num_props,
                SUM(CASE WHEN p.result = 'hit' THEN 1 ELSE 0 END) as props_hit,
                SUM(CASE WHEN p.result = 'miss' THEN 1 ELSE 0 END) as props_miss
            FROM bets b
            LEFT JOIN props p ON b.bet_id = p.bet_id
            GROUP BY b.bet_id
            ORDER BY b.created_at DESC
            LIMIT ?
        """, (limit,))
        
        bets = []
        for row in cursor.fetchall():
            bet = {
                'bet_id': row[0],
                'bet_date': row[1],
                'game_date': row[2],
                'bet_type': row[3],
                'odds': row[4],
                'stake': row[5],
                'potential_win': row[6],
                'result': row[7],
                'num_props': row[8],
                'props_hit': row[9],
                'props_miss': row[10],
                'props': []
            }
            
            # Get props for this bet
            cursor.execute("""
                SELECT prop_id, player_id, player_name, prop_type,
                       line, over_under, result, actual_value
                FROM props
                WHERE bet_id = ?
            """, (row[0],))
            
            for prop_row in cursor.fetchall():
                bet['props'].append({
                    'prop_id': prop_row[0],
                    'player_id': prop_row[1],
                    'player_name': prop_row[2],
                    'prop_type': prop_row[3],
                    'line': prop_row[4],
                    'over_under': prop_row[5],
                    'result': prop_row[6],
                    'actual_value': prop_row[7]
                })
            
            bets.append(bet)
        
        conn.close()
        return bets


# ======================
# EXAMPLE USAGE
# ======================

def example_usage():
    """Example of how to use the API"""
    
    api = NBABettingStatsAPI()
    
    print("\n" + "="*70)
    print("🏀 NBA BETTING STATS API - EXAMPLE USAGE")
    print("="*70)
    
    # 1. Search for players
    print("\n1️⃣  PLAYER SEARCH")
    print("-" * 70)
    results = api.search_players("Jaden")
    for player in results[:5]:
        print(f"  {player['full_name']} (ID: {player['player_id']})")
    
    # 2. Create a bet with multiple props
    print("\n2️⃣  CREATE BET WITH PROPS")
    print("-" * 70)
    bet_id = api.create_bet(
        bet_date="2024-12-01",
        game_date="2024-12-01",
        bet_type="3-leg parlay",
        odds=-110,
        stake=1.0
    )
    print(f"  ✓ Created bet #{bet_id}")
    
    # Add props
    prop1 = api.add_prop_to_bet(
        bet_id=bet_id,
        player_id=1630596,  # Jaden Ivey
        player_name="Jaden Ivey",
        prop_type="points",
        line=15.5,
        over_under="over"
    )
    print(f"  ✓ Added prop: Jaden Ivey O15.5 points")
    
    prop2 = api.add_prop_to_bet(
        bet_id=bet_id,
        player_id=1630162,  # Tyrese Maxey
        player_name="Tyrese Maxey",
        prop_type="assists",
        line=5.5,
        over_under="over"
    )
    print(f"  ✓ Added prop: Tyrese Maxey O5.5 assists")
    
    # 3. Mark results (one hits, one misses)
    print("\n3️⃣  MARK PROP RESULTS")
    print("-" * 70)
    
    api.mark_prop_result(prop1, "miss", actual_value=13.0, capture_stats=True)
    print(f"  ✗ Jaden Ivey missed (got 13 pts)")
    print(f"  ✓ Auto-captured shooting %, opponent, def rating")
    
    api.mark_prop_result(prop2, "hit", actual_value=7.0, capture_stats=False)
    print(f"  ✓ Tyrese Maxey hit (got 7 ast)")
    
    api.mark_bet_result(bet_id, "lost")
    print(f"  ✓ Bet marked as LOST")
    
    # 4. Get analytics
    print("\n4️⃣  BUST PLAYERS (Players who fuck up a lot)")
    print("-" * 70)
    bust_players = api.get_bust_players(min_props=1)
    for player in bust_players[:5]:
        print(f"  {player['player_name']}: {player['miss_rate']}% miss rate "
              f"({player['misses']}/{player['total_props']})")
    
    print("\n5️⃣  TOUGH MATCHUPS (Teams causing misses)")
    print("-" * 70)
    tough_teams = api.get_tough_matchups(min_games=1)
    for team in tough_teams[:5]:
        print(f"  vs {team['opponent_team']}: {team['miss_rate']}% miss rate "
              f"(Def Rating: {team['avg_def_rating']:.1f})")
    
    print("\n" + "="*70)
    print("✓ Example complete!")
    print("="*70)


if __name__ == "__main__":
    if not NBA_API_AVAILABLE:
        print("❌ Please install: pip install nba_api pandas")
    else:
        example_usage()
