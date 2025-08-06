import os
import requests

class SportsDataService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("SPORTSDATA_API_KEY")
        self.base_url = os.getenv("SPORTSDATAIO_BASE_URL", "https://api.sportsdata.io/v3")
        self.headers = {"Ocp-Apim-Subscription-Key": self.api_key}

    def get_nfl_schedule(self, season="2025REG"):
        url = f"{self.base_url}/nfl/scores/json/Schedules/{season}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_player_game_stats(self, player_id, season="2025REG"):
        url = f"{self.base_url}/nfl/stats/json/PlayerGameStatsByPlayerID/{season}/{player_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_player_props_by_game(self, game_id):
        url = f"{self.base_url}/nfl/odds/json/PlayerPropsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_fantasy_projections(self, player_id, week=None, season="2025REG"):
        if week:
            url = f"{self.base_url}/nfl/projections/json/PlayerGameProjectionStatsByPlayerID/{season}/{week}/{player_id}"
        else:
            url = f"{self.base_url}/nfl/projections/json/PlayerSeasonProjectionStatsByPlayerID/{season}/{player_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_live_player_stats(self, game_id):
        url = f"{self.base_url}/nfl/stats/json/PlayerGameStatsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_players_by_team(self, team):
        """Get all active players for a team"""
        url = f"{self.base_url}/nfl/scores/json/PlayersActiveByTeam/{team}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_all_players(self):
        """Get all active NFL players"""
        url = f"{self.base_url}/nfl/scores/json/Players"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def search_players(self, name_query):
        """Search for players by name"""
        all_players = self.get_all_players()
        matching_players = []
        query_lower = name_query.lower()
        
        for player in all_players:
            if (query_lower in player.get('Name', '').lower() or 
                query_lower in player.get('FirstName', '').lower() or 
                query_lower in player.get('LastName', '').lower()):
                matching_players.append(player)
        
        return matching_players[:20]  # Limit to 20 results

    def get_game_players(self, game_id):
        """Get all players from both teams in a specific game"""
        try:
            # First get the schedule to find team info
            schedule = self.get_nfl_schedule()
            game = next((g for g in schedule if g['GameID'] == int(game_id)), None)
            
            if not game:
                return []
            
            home_team = game['HomeTeam']
            away_team = game['AwayTeam']
            
            # Get players from both teams
            home_players = self.get_players_by_team(home_team)
            away_players = self.get_players_by_team(away_team)
            
            # Add team info to players
            for player in home_players:
                player['GameTeam'] = home_team
                player['IsHome'] = True
            
            for player in away_players:
                player['GameTeam'] = away_team
                player['IsHome'] = False
            
            return home_players + away_players
            
        except Exception as e:
            print(f"Error getting game players: {e}")
            return []

    def get_available_prop_types(self):
        """Return common prop types that map to FanDuel categories"""
        return {
            'passing_yards': {
                'fanduel_name': 'Passing Yards',
                'sportsdata_field': 'PassingYards',
                'description': 'Total passing yards in the game'
            },
            'rushing_yards': {
                'fanduel_name': 'Rushing Yards', 
                'sportsdata_field': 'RushingYards',
                'description': 'Total rushing yards in the game'
            },
            'receiving_yards': {
                'fanduel_name': 'Receiving Yards',
                'sportsdata_field': 'ReceivingYards', 
                'description': 'Total receiving yards in the game'
            },
            'passing_tds': {
                'fanduel_name': 'Passing TDs',
                'sportsdata_field': 'PassingTouchdowns',
                'description': 'Total passing touchdowns'
            },
            'rushing_tds': {
                'fanduel_name': 'Rushing TDs',
                'sportsdata_field': 'RushingTouchdowns',
                'description': 'Total rushing touchdowns'
            },
            'receiving_tds': {
                'fanduel_name': 'Receiving TDs',
                'sportsdata_field': 'ReceivingTouchdowns',
                'description': 'Total receiving touchdowns'
            },
            'receptions': {
                'fanduel_name': 'Receptions',
                'sportsdata_field': 'Receptions',
                'description': 'Total number of catches'
            },
            'completions': {
                'fanduel_name': 'Pass Completions',
                'sportsdata_field': 'PassingCompletions',
                'description': 'Total completed passes'
            },
            'attempts': {
                'fanduel_name': 'Pass Attempts',
                'sportsdata_field': 'PassingAttempts',
                'description': 'Total pass attempts'
            },
            'carries': {
                'fanduel_name': 'Rushing Attempts',
                'sportsdata_field': 'RushingAttempts',
                'description': 'Total rushing attempts'
            }
        }

    def get_game_odds(self, season="2025REG"):
        """Get game odds and betting lines"""
        url = f"{self.base_url}/nfl/odds/json/GameOddsByWeek/{season}/1"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_current_season_odds(self, season="2025REG"):
        """Get current season betting odds"""
        url = f"{self.base_url}/nfl/odds/json/GameOdds/{season}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_pregame_odds(self, game_id):
        """Get pregame odds for a specific game"""
        url = f"{self.base_url}/nfl/odds/json/GameOddsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_live_odds(self, game_id):
        """Get live/in-game odds for a specific game"""
        url = f"{self.base_url}/nfl/odds/json/LiveGameOddsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_sportsbook_odds(self, season="2025REG"):
        """Get odds from multiple sportsbooks"""
        url = f"{self.base_url}/nfl/odds/json/BettingOddsByWeek/{season}/1"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_consensus_odds(self, season="2025REG"):
        """Get consensus betting odds across sportsbooks"""
        url = f"{self.base_url}/nfl/odds/json/BettingOddsConsensus/{season}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_alternate_market_odds(self, game_id):
        """Get alternate market odds (different spreads/totals)"""
        url = f"{self.base_url}/nfl/odds/json/AlternateMarketGameOddsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_betting_trends(self, team):
        """Get betting trends for a team"""
        url = f"{self.base_url}/nfl/odds/json/BettingTrendsByTeam/{team}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_betting_results_by_week(self, season="2025REG", week=1):
        """Get betting results by week"""
        url = f"{self.base_url}/nfl/odds/json/BettingResultsByWeek/{season}/{week}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_public_betting_percentages(self, game_id):
        """Get public betting percentages for a game"""
        url = f"{self.base_url}/nfl/odds/json/BettingMarketsByGameID/{game_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()
