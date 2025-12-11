#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quarter Stats Parser - Standalone Module
Add this to your betting app to get real quarter-by-quarter stats
"""

import time
from typing import Dict

try:
    from nba_api.stats.endpoints import playergamelogs
    NBA_API_AVAILABLE = True
except ImportError:
    print("❌ Please install: pip install nba_api")
    NBA_API_AVAILABLE = False


class QuarterStatsParser:
    """
    Get quarter-by-quarter stats using the official PlayerGameLogs endpoint
    Uses the period_nullable parameter to get stats for Q1, Q2, Q3, Q4
    """
    
    def __init__(self):
        self.cache = {}
    
    def get_quarter_stats(self, player_id: int, season: str, game_id: str = None) -> Dict:
        """
        Get quarter-by-quarter stats for a player
        
        Args:
            player_id: NBA player ID
            season: Season string like '2025-26'
            game_id: Optional - if provided, only return stats for this game
        
        Returns:
            If game_id provided:
                {
                    'Q1': {'PTS': 8, 'REB': 2, ...},
                    'Q2': {'PTS': 7, 'REB': 2, ...},
                    'Q3': {...},
                    'Q4': {...},
                    '1H': {...},
                    '2H': {...},
                    'FULL_GAME': {...},
                    'GAME_DATE': '2025-12-10',
                    'MATCHUP': 'LAL vs. BOS',
                    'WL': 'W'
                }
            
            If no game_id:
                {
                    '0022500362': { 'Q1': {...}, 'Q2': {...}, ... },
                    '0022500363': { 'Q1': {...}, 'Q2': {...}, ... },
                    ...
                }
        """
        
        if not NBA_API_AVAILABLE:
            return {}
        
        # Check cache
        cache_key = f"{player_id}_{season}_{game_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            quarter_data = {}
            
            # Get stats for each quarter (1-4)
            for period in range(1, 5):
                time.sleep(0.6)  # Rate limit - respect NBA API limits
                
                logs = playergamelogs.PlayerGameLogs(
                    season_nullable=season,
                    player_id_nullable=player_id,
                    period_nullable=period,
                    per_mode_simple_nullable='Totals'
                )
                
                df = logs.get_data_frames()[0]
                
                if df.empty:
                    continue
                
                # Store by game_id
                for _, row in df.iterrows():
                    row_game_id = str(row['GAME_ID'])
                    
                    if row_game_id not in quarter_data:
                        quarter_data[row_game_id] = {
                            'GAME_ID': row_game_id,
                            'GAME_DATE': row['GAME_DATE'],
                            'MATCHUP': row['MATCHUP'],
                            'WL': row.get('WL', ''),
                        }
                    
                    # Add quarter stats
                    quarter_data[row_game_id][f'Q{period}'] = {
                        'PTS': int(row.get('PTS', 0) or 0),
                        'REB': int(row.get('REB', 0) or 0),
                        'AST': int(row.get('AST', 0) or 0),
                        'STL': int(row.get('STL', 0) or 0),
                        'BLK': int(row.get('BLK', 0) or 0),
                        'TO': int(row.get('TOV', 0) or 0),
                        'PF': int(row.get('PF', 0) or 0),
                        'FGM': int(row.get('FGM', 0) or 0),
                        'FGA': int(row.get('FGA', 0) or 0),
                        'FG3M': int(row.get('FG3M', 0) or 0),
                        'FG3A': int(row.get('FG3A', 0) or 0),
                        'FTM': int(row.get('FTM', 0) or 0),
                        'FTA': int(row.get('FTA', 0) or 0),
                    }
            
            # Calculate full game totals and halves for each game
            for gid in quarter_data:
                game_quarters = quarter_data[gid]
                
                # Calculate full game totals
                full_game = self._calculate_game_totals(game_quarters)
                game_quarters['FULL_GAME'] = full_game
                
                # Calculate halves
                halves = self._calculate_halves(game_quarters)
                game_quarters['1H'] = halves['1H']
                game_quarters['2H'] = halves['2H']
            
            # If specific game requested, return just that game
            if game_id and game_id in quarter_data:
                result = quarter_data[game_id]
                self.cache[cache_key] = result
                return result
            
            # Otherwise return all games
            self.cache[cache_key] = quarter_data
            return quarter_data
            
        except Exception as e:
            print(f"❌ Error getting quarter stats: {e}")
            return {}
    
    def _calculate_game_totals(self, game_quarters: Dict) -> Dict:
        """Calculate full game totals from quarters"""
        totals = {
            'PTS': 0, 'REB': 0, 'AST': 0, 'STL': 0, 'BLK': 0,
            'TO': 0, 'PF': 0, 'FGM': 0, 'FGA': 0,
            'FG3M': 0, 'FG3A': 0, 'FTM': 0, 'FTA': 0,
        }
        
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            if quarter in game_quarters:
                for stat in totals.keys():
                    totals[stat] += game_quarters[quarter].get(stat, 0)
        
        return totals
    
    def _calculate_halves(self, game_quarters: Dict) -> Dict:
        """Calculate 1H and 2H stats"""
        first_half = {
            'PTS': 0, 'REB': 0, 'AST': 0, 'STL': 0, 'BLK': 0,
            'TO': 0, 'PF': 0, 'FGM': 0, 'FGA': 0,
            'FG3M': 0, 'FG3A': 0, 'FTM': 0, 'FTA': 0,
        }
        
        second_half = {
            'PTS': 0, 'REB': 0, 'AST': 0, 'STL': 0, 'BLK': 0,
            'TO': 0, 'PF': 0, 'FGM': 0, 'FGA': 0,
            'FG3M': 0, 'FG3A': 0, 'FTM': 0, 'FTA': 0,
        }
        
        # Sum Q1 + Q2 for first half
        for quarter in ['Q1', 'Q2']:
            if quarter in game_quarters:
                for stat in first_half.keys():
                    first_half[stat] += game_quarters[quarter].get(stat, 0)
        
        # Sum Q3 + Q4 for second half
        for quarter in ['Q3', 'Q4']:
            if quarter in game_quarters:
                for stat in second_half.keys():
                    second_half[stat] += game_quarters[quarter].get(stat, 0)
        
        return {'1H': first_half, '2H': second_half}
